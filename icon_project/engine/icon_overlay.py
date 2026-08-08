"""
아이콘 오버레이 - IPC 버전
오버레이 안에 HTTP 서버 (포트 19876) 띄워서 백엔드가 직접 명령 전송
- /reload     → 전체 재로드 (수정 반영)
- /reposition → 위치만 업데이트 (그리드 정렬)
"""

import ctypes, json, sys, os, threading

# ── DPI 인식 선언 (반드시 Qt 초기화 전에 호출) ──────────────
# Per-Monitor DPI Aware v2: 150% 배율 환경에서 아이콘 재배치 방지
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

from PySide6.QtWidgets import (QApplication, QWidget, QSystemTrayIcon, QMenu,
                                QFileDialog, QInputDialog, QLabel)
from PySide6.QtCore  import Qt, QSize, QRect, QTimer, Signal, QObject
from PySide6.QtGui   import (QPixmap, QPainter, QColor, QFont, QFontMetrics,
                              QMovie, QIcon, QImageReader, QImage)

ENGINE_DIR  = Path(__file__).resolve().parent
CONFIG_PATH = ENGINE_DIR / "icons_config.json"
PID_PATH    = ENGINE_DIR / ".overlay.pid"
ORIGINAL_WALLPAPER_PATH = ENGINE_DIR / ".original_wallpaper.txt"
ACTIVE_WALLPAPER_PATH   = ENGINE_DIR / ".active_wallpaper.txt"
CTRL_PORT   = 19876   # IPC 포트

TEXT_GAP = 3
TEXT_H   = 40
PAD      = 10

_CK_R, _CK_G, _CK_B = 2, 2, 2
BG_COLOR = QColor(_CK_R, _CK_G, _CK_B)
BG_WIN32 = (_CK_B << 16) | (_CK_G << 8) | _CK_R
BG_CSS   = f"rgb({_CK_R},{_CK_G},{_CK_B})"



def _wrap_2lines(name: str, fm, max_w: int) -> str:
    """
    텍스트를 최대 2줄로 제한, 초과 시 ... 처리
    - TextWrapAnywhere: 공백 없는 파일명도 글자 단위 줄바꿈
    - TextWordWrap: 공백 있으면 단어 단위 우선
    """
    from PySide6.QtCore import QRect as _QR

    # 공백 있으면 단어 단위 + 없으면 글자 단위 (둘 다 적용)
    flags = Qt.TextWordWrap | Qt.TextWrapAnywhere | Qt.AlignHCenter
    max_h = fm.height() * 2 + fm.leading() + 4

    # 전체가 2줄 안에 들어오면 그대로 반환
    br = fm.boundingRect(_QR(0, 0, max_w, 9999), flags, name)
    if br.height() <= max_h:
        return name

    # 이진탐색: name[:lo] + "..." 이 2줄 안에 들어가는 최대 lo 탐색
    lo, hi = 0, len(name)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        test = name[:mid] + "..."
        br2 = fm.boundingRect(_QR(0, 0, max_w, 9999), flags, test)
        if br2.height() <= max_h:
            lo = mid
        else:
            hi = mid - 1

    return name[:lo] + "..."


def _apply_colorkey(hwnd):
    try:
        u32 = ctypes.windll.user32
        ex  = u32.GetWindowLongW(hwnd, -20)
        u32.SetWindowLongW(hwnd, -20, ex | 0x80000)
        u32.SetLayeredWindowAttributes(hwnd, BG_WIN32, 255, 0x01)
    except: pass


def _win32_move(hwnd, x, y):
    """Win32 SetWindowPos - DPI-aware 앱이므로 논리좌표 그대로 전달"""
    try:
        ctypes.windll.user32.SetWindowPos(
            hwnd, None, int(x), int(y), 0, 0, 0x0001 | 0x0004 | 0x0010)
    except: pass


# ── 캔버스 좌표 → 실제 화면 좌표 매핑 ──────────────────────────────
# 백엔드는 원본 캔버스(1920×1080) 좌표만 넘기고, 실제 배율/해상도에 맞춘
# 변환은 여기(Qt)에서 한다. Qt의 primaryScreen().geometry() 는 move()/pos()
# 와 동일한 좌표계라, ctypes DPI 추정과 달리 절대 어긋나지 않는다.
def _screen_size():
    scr = QApplication.primaryScreen()
    g = scr.geometry() if scr else None
    return (g.width(), g.height()) if g else (1920, 1080)


def _cover_scale(cw, ch, sw, sh):
    if not cw or not ch:
        return 1.0
    return max(sw / cw, sh / ch)   # 배경 Fill(cover) 과 동일


def _canvas_to_screen(cx, cy, cw, ch, sw, sh):
    s = _cover_scale(cw, ch, sw, sh)
    return ((float(cx) - cw / 2) * s + sw / 2, (float(cy) - ch / 2) * s + sh / 2)


def _screen_to_canvas(sx, sy, cw, ch, sw, sh):
    s = _cover_scale(cw, ch, sw, sh) or 1.0
    return ((float(sx) - sw / 2) / s + cw / 2, (float(sy) - sh / 2) / s + ch / 2)


def _find_defview():
    u32 = ctypes.windll.user32
    progman = u32.FindWindowW("Progman", None)
    defview = u32.FindWindowExW(progman, None, "SHELLDLL_DefView", None)
    if not defview:
        worker = None
        while True:
            worker = u32.FindWindowExW(None, worker, "WorkerW", None)
            if not worker:
                break
            defview = u32.FindWindowExW(worker, None, "SHELLDLL_DefView", None)
            if defview:
                break
    return defview


def _show_desktop_icons():
    """바탕화면 기본 아이콘 표시 (SW_SHOW)."""
    try:
        u32 = ctypes.windll.user32
        defview = _find_defview()
        if not defview:
            return
        lv = u32.FindWindowExW(defview, None, "SysListView32", "FolderView")
        if lv:
            u32.ShowWindow(lv, 5)  # SW_SHOW
    except Exception:
        pass


def _hide_desktop_icons():
    """바탕화면 기본 아이콘 숨김 (SW_HIDE)."""
    try:
        u32 = ctypes.windll.user32
        defview = _find_defview()
        if not defview:
            return
        lv = u32.FindWindowExW(defview, None, "SysListView32", "FolderView")
        if lv:
            u32.ShowWindow(lv, 0)  # SW_HIDE
    except Exception:
        pass


def _set_wallpaper(path):
    try:
        if path and os.path.exists(path):
            # 배경 표시 방식을 채우기(Fill)로 — 편집기 object-cover 와 일치
            try:
                import winreg
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop",
                                   0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(k, "WallpaperStyle", 0, winreg.REG_SZ, "10")
                winreg.SetValueEx(k, "TileWallpaper",  0, winreg.REG_SZ, "0")
                winreg.CloseKey(k)
            except Exception:
                pass
            ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
    except Exception:
        pass


def _restore_original_wallpaper(clear=True):
    """원본 배경화면 복원. clear=True면 마커 제거(종료), False면 유지(임시 끄기)."""
    try:
        if not ORIGINAL_WALLPAPER_PATH.exists():
            return
        orig = ORIGINAL_WALLPAPER_PATH.read_text(encoding="utf-8").strip()
        _set_wallpaper(orig)
        if clear:
            ORIGINAL_WALLPAPER_PATH.unlink(missing_ok=True)
    except Exception:
        pass


def _apply_active_wallpaper():
    """현재 프리셋 배경화면으로 재적용 (임시 끄기 해제 시)."""
    try:
        if not ACTIVE_WALLPAPER_PATH.exists():
            return
        wp = ACTIVE_WALLPAPER_PATH.read_text(encoding="utf-8").strip()
        _set_wallpaper(wp)
    except Exception:
        pass


def _load_settings():
    d = {"mode": "free", "grid_cell_w": 110, "grid_cell_h": 130}
    sp = ENGINE_DIR / "settings.json"
    if sp.exists():
        try:
            with open(sp, 'r', encoding='utf-8') as f:
                return {**d, **json.load(f)}
        except: pass
    return d


def _load_gif_frames(path, target_size):
    try:
        from PIL import Image
    except ImportError:
        return [], 0, 0
    frames = []
    try:
        with Image.open(path) as im:
            r = target_size / im.width   # 너비 기준 (편집기 width:100% 와 일치)
            sw, sh = max(1, int(im.width*r)), max(1, int(im.height*r))
            for i in range(getattr(im, 'n_frames', 1)):
                im.seek(i)
                delay = max(50, im.info.get('duration', 50))
                raw = im.convert('RGBA').resize((sw, sh)).tobytes('raw','RGBA')
                qi  = QImage(raw, sw, sh, QImage.Format_RGBA8888)
                frames.append((QPixmap.fromImage(qi.copy()), int(delay)))
        return frames, sw, sh
    except:
        return [], 0, 0


# ── Qt 신호 (스레드 안전 통신용) ─────────────────────────────
class OverlaySignals(QObject):
    do_reload      = Signal()
    do_reposition  = Signal()


# ── IPC HTTP 서버 (백그라운드 스레드) ───────────────────────
class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/reload':
            self.send_response(200); self.end_headers()
            self.server.signals.do_reload.emit()
            print("  📥 /reload 수신")
        elif self.path == '/reposition':
            self.send_response(200); self.end_headers()
            self.server.signals.do_reposition.emit()
            print("  📥 /reposition 수신")
        elif self.path == '/ping':
            self.send_response(200); self.end_headers()
            self.wfile.write(b'pong')
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, *args): pass   # 로그 억제


class _IPCServer(HTTPServer):
    def __init__(self, signals):
        self.signals = signals
        super().__init__(('127.0.0.1', CTRL_PORT), _Handler)


def start_ipc_server(signals):
    try:
        srv = _IPCServer(signals)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        print(f"  IPC 서버 포트 {CTRL_PORT} 시작")
    except Exception as e:
        print(f"  IPC 서버 실패: {e}")


# ── CustomIcon ───────────────────────────────────────────────
class CustomIcon(QWidget):
    def __init__(self, icon_data, parent=None):
        super().__init__(parent)
        self.icon_data   = icon_data
        self.drag_start  = None
        self.show_name   = icon_data.get('show_name', True)
        self.image_path  = icon_data['image_path']
        # 캔버스 좌표 → 실제 화면(Qt) 좌표 매핑 준비 (배율/해상도 독립)
        self._cw = icon_data.get('canvas_w', 1920) or 1920
        self._ch = icon_data.get('canvas_h', 1080) or 1080
        self._sw, self._sh = _screen_size()
        self._scale = _cover_scale(self._cw, self._ch, self._sw, self._sh)
        self._icon_size  = max(1, int(round(icon_data.get('size', 80) * self._scale)))
        self.gif_frames  = []
        self.gif_idx     = 0
        self._gif_active = False
        self.cur_frame   = None
        self.img_w = self._icon_size
        self.img_h = self._icon_size

        self.setWindowFlags(Qt.FramelessWindowHint |
                            Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.img_label = QLabel(self)
        self.img_label.setStyleSheet("background: transparent; border: none;")

        self._load_image()
        self._calc_size()

        mx, my = _canvas_to_screen(icon_data['x'], icon_data['y'],
                                   self._cw, self._ch, self._sw, self._sh)
        self.move(int(round(mx)), int(round(my)))
        self.show()
        if self.gif_frames:
            QTimer.singleShot(150, self._start_gif)
        print(f"  ✓ [{icon_data.get('name')}] {self.width()}x{self.height()}")

    def _calc_size(self):
        # 위젯 너비 = 이미지 너비. 좌우 PAD 여백을 제거해 이미지 좌상단이
        # 저장된 (x, y)에 정확히 오도록 한다(편집기 미리보기 앵커와 일치).
        total_w = self.img_w
        if self.show_name:
            # 2줄 높이 계산 (폰트 기반)
            fm = QFontMetrics(QFont(
                self.icon_data.get('font_family', 'Segoe UI'),
                self.icon_data.get('font_size', 9),
                QFont.Bold if self.icon_data.get('font_bold', True) else QFont.Normal))
            text_h = fm.height() * 2 + fm.leading() + 8
            total_h = self.img_h + TEXT_GAP + text_h
        else:
            total_h = self.img_h + 2
        self.setFixedSize(total_w, total_h)
        self.img_label.setGeometry((total_w-self.img_w)//2, 0, self.img_w, self.img_h)

    def _load_image(self):
        s = self._icon_size
        if not os.path.exists(self.image_path):
            self.img_label.setFixedSize(s, s); return
        if self.image_path.lower().endswith('.gif'):
            frames, w, h = _load_gif_frames(self.image_path, s)
            self.img_w, self.img_h = (w,h) if w>0 else (s,s)
            self.img_label.hide()
            if frames:
                self.gif_frames = frames
                self.cur_frame  = frames[0][0]
        else:
            raw = QPixmap(self.image_path)
            px  = raw.scaledToWidth(s, Qt.SmoothTransformation) if not raw.isNull() else (lambda p: (p.fill(BG_COLOR), p)[1])(QPixmap(s,s))
            self.img_label.setFixedSize(px.width(), px.height())
            self.img_label.setPixmap(px)
            self.img_w, self.img_h = px.width(), px.height()

    def _start_gif(self):
        if self.gif_frames and not self._gif_active:
            self._gif_active = True
            self._sched()

    def _sched(self):
        if self.gif_frames and self._gif_active:
            QTimer.singleShot(self.gif_frames[self.gif_idx][1], self._adv)

    def _adv(self):
        if not self.gif_frames or not self._gif_active: return
        self.gif_idx = (self.gif_idx+1) % len(self.gif_frames)
        self.cur_frame = self.gif_frames[self.gif_idx][0]
        self.repaint(); self._sched()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # 투명 배경 (WA_TranslucentBackground)
        p.setCompositionMode(QPainter.CompositionMode_Clear)
        p.fillRect(self.rect(), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        if self.cur_frame and not self.cur_frame.isNull():
            p.drawPixmap((self.width()-self.img_w)//2, 0, self.cur_frame)
        if self.show_name:
            p.setRenderHint(QPainter.TextAntialiasing)
            raw_name = self.icon_data.get('name', '')
            font = QFont(self.icon_data.get('font_family', 'Segoe UI'),
                         self.icon_data.get('font_size', 9),
                         QFont.Bold if self.icon_data.get('font_bold', True) else QFont.Normal)
            font.setItalic(self.icon_data.get('font_italic', False))
            p.setFont(font)
            fm   = QFontMetrics(font)
            text_area_w = self.width() - PAD * 2
            # 최대 2줄 + 말줄임 처리
            name = _wrap_2lines(raw_name, fm, text_area_w)
            rect = QRect(PAD, self.img_h + TEXT_GAP,
                         text_area_w, self.height() - self.img_h - TEXT_GAP)
            oc = QColor(self.icon_data.get('outline_color', '#000000')); oc.setAlpha(220)
            p.setPen(oc)
            _flags = Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap | Qt.TextWrapAnywhere
            for dx, dy in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]:
                p.drawText(rect.translated(dx, dy), _flags, name)
            p.setPen(QColor(self.icon_data.get('font_color', '#ffffff')))
            p.drawText(rect, _flags, name)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            # self.pos()는 Qt 논리좌표, globalPosition()도 Qt 논리좌표 → 일관성 유지
            self.drag_start = e.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self.drag_start:
            p = e.globalPosition().toPoint() - self.drag_start
            # Qt move() → self.pos() 동기화 유지 (다음 드래그 시 튕김 방지)
            self.move(p)
            # 화면 좌표 → 캔버스 좌표로 역변환해 저장 (config 는 캔버스 좌표 유지)
            cx, cy = _screen_to_canvas(p.x(), p.y(), self._cw, self._ch, self._sw, self._sh)
            self.icon_data['x'] = int(round(cx))
            self.icon_data['y'] = int(round(cy))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            if self.drag_start:
                self.drag_start = None
                if self.parent(): self.parent().save_config()
            else:
                self.execute_icon()

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton: self.execute_icon()

    def closeEvent(self, e):
        self._gif_active = False
        super().closeEvent(e)

    def execute_icon(self):
        try:
            t = self.icon_data.get('target_path')
            if t and os.path.exists(t): os.startfile(t)
        except: pass

    def show_context_menu(self, pos):
        m = QMenu()
        r  = m.addAction("✏️ 이름 바꾸기")
        tn = m.addAction("이름 숨기기" if self.show_name else "이름 표시")
        st = m.addAction("📂 실행 파일 설정")
        m.addSeparator()
        dl = m.addAction("❌ 삭제")
        a  = m.exec_(self.mapToGlobal(pos))
        if a==r: self.rename_icon()
        elif a==tn: self.toggle_name()
        elif a==st: self.set_target_path()
        elif a==dl: self.delete_icon()

    def rename_icon(self):
        n,ok = QInputDialog.getText(self,"이름 바꾸기","새 이름:",text=self.icon_data.get('name',''))
        if ok and n.strip():
            self.icon_data['name'] = n.strip()
            self._calc_size()
            if self.parent(): self.parent().save_config()
            self.update()

    def toggle_name(self):
        self.show_name = not self.show_name
        self.icon_data['show_name'] = self.show_name
        self._calc_size()
        if self.parent(): self.parent().save_config()
        self.update()

    def set_target_path(self):
        fp,_ = QFileDialog.getOpenFileName(self,"실행 파일 선택",str(Path.home()),"모든 파일 (*.*)")
        if fp:
            self.icon_data['target_path'] = fp
            if self.parent(): self.parent().save_config()

    def delete_icon(self):
        self._gif_active = False
        if self.parent(): self.parent().remove_icon(self)
        self.close()


# ── IconOverlay ──────────────────────────────────────────────
class IconOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.hide()
        self.icons   = []
        self.settings = _load_settings()
        self._saving  = False
        self._off     = False   # 임시 끄기 상태
        self._toggle_action = None

        # Qt 신호 (스레드 안전)
        self.signals = OverlaySignals()
        self.signals.do_reload.connect(self._full_reload)
        self.signals.do_reposition.connect(self._reposition_icons)

        # IPC 서버 시작
        start_ipc_server(self.signals)

        # PID 기록
        try: PID_PATH.write_text(str(os.getpid()))
        except: pass

        self.load_config()
        self.setup_tray()

        # ── config mtime 폴링 (IPC 실패 시 fallback, 500ms마다 확인) ──
        self._config_mtime = CONFIG_PATH.stat().st_mtime if CONFIG_PATH.exists() else 0
        self._poll = QTimer(self)
        self._poll.timeout.connect(self._poll_config)
        self._poll.start(500)

        print(f"\n✅ 오버레이 준비 완료 (IPC 포트 {CTRL_PORT})\n")

    def _full_reload(self):
        # JSON에서 새 설정 미리 읽어서 로그
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                new_list = json.load(f)
            sizes = [d.get('size', 80) for d in new_list]
            print(f"  🔄 전체 재로드: {len(new_list)}개 아이콘, sizes={sizes}")
        except Exception as e:
            print(f"  🔄 전체 재로드 (읽기 오류: {e})")

        for i in self.icons: i._gif_active = False; i.close()
        self.icons.clear()
        self.settings = _load_settings()
        self.load_config()
        # 재로드 후 mtime 갱신 (중복 트리거 방지)
        if CONFIG_PATH.exists():
            self._config_mtime = CONFIG_PATH.stat().st_mtime
        print(f"  ✅ 재로드 완료: {len(self.icons)}개 표시")

    def _reposition_icons(self):
        print("  위치 재배치 실행...")
        try:
            with open(CONFIG_PATH,'r',encoding='utf-8') as f:
                new_list = json.load(f)
        except Exception as e:
            print(f"  config 읽기 실패: {e}"); return
        id_map = {d.get('id'):d for d in new_list if d.get('id')}
        moved = 0
        for icon in self.icons:
            iid = icon.icon_data.get('id')
            if iid and iid in id_map:
                nd = id_map[iid]
                nx, ny = nd.get('x', icon.icon_data['x']), nd.get('y', icon.icon_data['y'])
                if nx != icon.icon_data['x'] or ny != icon.icon_data['y']:
                    icon.icon_data['x'] = nx
                    icon.icon_data['y'] = ny
                    # 캔버스 좌표 → 실제 화면 좌표로 매핑 후 이동 (Qt 좌표계 일치)
                    mx, my = _canvas_to_screen(nx, ny, icon._cw, icon._ch, icon._sw, icon._sh)
                    icon.move(int(round(mx)), int(round(my)))
                    moved += 1
        print(f"  위치 재배치 완료: {moved}개 이동")

    def load_config(self):
        if not CONFIG_PATH.exists(): return
        try:
            with open(CONFIG_PATH,'r',encoding='utf-8') as f:
                icon_list = json.load(f)
            for d in icon_list:
                if d.get('image_path') and os.path.exists(d['image_path']):
                    self.icons.append(CustomIcon(d, self))
        except Exception as e:
            print(f"ERROR: {e}")

        # [진단] Qt가 실제로 쓰는 화면 크기 + 아이콘 실제 위치를 파일로 남김
        try:
            scr = QApplication.primaryScreen()
            geo = scr.geometry() if scr else None
            dbg = {
                "qt_screen": [geo.width(), geo.height()] if geo else None,
                "device_pixel_ratio": (scr.devicePixelRatio() if scr else None),
                "icons": [{
                    "name": ic.icon_data.get("name"),
                    "config_xy": [ic.icon_data.get("x"), ic.icon_data.get("y")],
                    "config_size": ic.icon_data.get("size"),
                    "actual_pos": [ic.x(), ic.y()],
                    "actual_wh": [ic.width(), ic.height()],
                } for ic in self.icons[:8]],
            }
            with open(ENGINE_DIR / ".overlay_debug.json", "w", encoding="utf-8") as f:
                json.dump(dbg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"debug dump err: {e}")

    def save_config(self):
        if self._saving: return
        self._saving = True
        try:
            with open(CONFIG_PATH,'w',encoding='utf-8') as f:
                json.dump([i.icon_data for i in self.icons], f, ensure_ascii=False, indent=2)
            # 자체 저장 후 mtime 갱신 (폴링 재로드 방지)
            if CONFIG_PATH.exists():
                self._config_mtime = CONFIG_PATH.stat().st_mtime
        finally:
            self._saving = False

    def remove_icon(self, icon):
        if icon in self.icons:
            self.icons.remove(icon)
            self.save_config()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("커스텀 아이콘")
        px = QPixmap(16,16); px.fill(QColor(70,130,180))
        self.tray_icon.setIcon(QIcon(px))
        menu = QMenu()
        menu.addAction("🔄 새로고침").triggered.connect(lambda: self._full_reload())
        # 끄기/켜기: 프로세스는 살려둔 채 잠깐 원래 바탕화면으로 되돌림
        self._toggle_action = menu.addAction("⏸️ 끄기")
        self._toggle_action.triggered.connect(lambda: self.toggle_off())
        menu.addSeparator()
        # 종료: 완전 종료 + 기본 아이콘 표시 + 원본 배경화면 복원
        menu.addAction("❌ 종료").triggered.connect(lambda: self.quit_app())
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def toggle_off(self):
        """임시 끄기/켜기 토글. 프로세스는 유지한다."""
        if not self._off:
            # 끄기: 오버레이 숨김 + 기본 아이콘 표시 + 원본 배경 복원(마커 유지)
            for i in self.icons: i.hide()
            _show_desktop_icons()
            _restore_original_wallpaper(clear=False)
            self._off = True
            if self._toggle_action: self._toggle_action.setText("▶️ 켜기")
        else:
            # 켜기: 기본 아이콘 숨김 + 프리셋 배경 재적용 + 오버레이 표시
            _hide_desktop_icons()
            _apply_active_wallpaper()
            for i in self.icons: i.show()
            self._off = False
            if self._toggle_action: self._toggle_action.setText("⏸️ 끄기")

    def _poll_config(self):
        """mtime 폴링: IPC 실패해도 JSON 변경 감지해서 재로드"""
        if not CONFIG_PATH.exists():
            return
        try:
            mtime = CONFIG_PATH.stat().st_mtime
            if mtime != self._config_mtime:
                old_mtime = self._config_mtime
                self._config_mtime = mtime  # 먼저 갱신 (중복 방지)
                if self._saving:
                    return  # 자체 저장 무시
                print(f"  📂 mtime 변경 감지 ({old_mtime:.1f} → {mtime:.1f}) → 재로드")
                self._full_reload()
        except Exception as e:
            print(f"  폴링 오류: {e}")

    def quit_app(self, restore=True):
        """오버레이 종료. restore=True면 기본 아이콘 + 원본 배경화면을 복구."""
        try: PID_PATH.unlink(missing_ok=True)
        except: pass
        self._poll.stop()
        for i in self.icons: i.close()
        if restore:
            _show_desktop_icons()
            _restore_original_wallpaper()
        QApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    print("="*50 + f"\n=== 커스텀 아이콘 오버레이 (IPC:{CTRL_PORT}) ===\n" + "="*50)
    overlay = IconOverlay()
    sys.exit(app.exec())
