"""
아이콘 오버레이 - IPC 버전
오버레이 안에 HTTP 서버 (포트 19876) 띄워서 백엔드가 직접 명령 전송
- /reload     → 전체 재로드 (수정 반영)
- /reposition → 위치만 업데이트 (그리드 정렬)
"""

import ctypes, json, sys, os, threading
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
    try:
        ctypes.windll.user32.SetWindowPos(
            hwnd, None, x, y, 0, 0, 0x0001 | 0x0004 | 0x0010)
    except: pass


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
            r = min(target_size / im.width, target_size / im.height)
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
        self._icon_size  = icon_data.get('size', 80)
        self.gif_frames  = []
        self.gif_idx     = 0
        self._gif_active = False
        self.cur_frame   = None
        self.img_w = self._icon_size
        self.img_h = self._icon_size

        self.setWindowFlags(Qt.WindowStaysOnBottomHint | Qt.FramelessWindowHint |
                            Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.img_label = QLabel(self)
        self.img_label.setStyleSheet(f"background-color: {BG_CSS}; border: none;")

        self._load_image()
        self._calc_size()

        self.move(icon_data['x'], icon_data['y'])
        self.show()
        _apply_colorkey(int(self.winId()))

        if self.gif_frames:
            QTimer.singleShot(150, self._start_gif)
        print(f"  ✓ [{icon_data.get('name')}] {self.width()}x{self.height()}")

    def _calc_size(self):
        # 너비: 이미지 기준 고정 (텍스트 길이와 무관 → 그리드 정렬 일관성)
        total_w = self.img_w + PAD * 2
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
            px  = raw.scaled(s,s, Qt.KeepAspectRatio, Qt.SmoothTransformation) if not raw.isNull() else (lambda p: (p.fill(BG_COLOR), p)[1])(QPixmap(s,s))
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
        p.fillRect(self.rect(), BG_COLOR)
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
            self.drag_start = e.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self.drag_start:
            p = e.globalPosition().toPoint() - self.drag_start
            _win32_move(int(self.winId()), p.x(), p.y())
            self.icon_data['x'] = p.x()
            self.icon_data['y'] = p.y()

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
        print(f"\n✅ 오버레이 준비 완료 (IPC 포트 {CTRL_PORT})\n")

    def _full_reload(self):
        print("  전체 재로드 실행...")
        for i in self.icons: i._gif_active = False; i.close()
        self.icons.clear()
        self.settings = _load_settings()
        self.load_config()
        print("  전체 재로드 완료")

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
                    _win32_move(int(icon.winId()), nx, ny)
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

    def save_config(self):
        if self._saving: return
        self._saving = True
        try:
            with open(CONFIG_PATH,'w',encoding='utf-8') as f:
                json.dump([i.icon_data for i in self.icons], f, ensure_ascii=False, indent=2)
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
        menu.addAction("🔄 새로고침").triggered.connect(self._full_reload)
        menu.addSeparator()
        menu.addAction("❌ 종료").triggered.connect(self.quit_app)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def quit_app(self):
        try: PID_PATH.unlink(missing_ok=True)
        except: pass
        for i in self.icons: i.close()
        QApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    print("="*50 + f"\n=== 커스텀 아이콘 오버레이 (IPC:{CTRL_PORT}) ===\n" + "="*50)
    overlay = IconOverlay()
    sys.exit(app.exec())
