# backend/main.py - 완전 수정 버전

# ── DPI 인식 선언 (Windows 아이콘 배치 보호) ─────────────────
import ctypes as _ctypes
try:
    _ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware v2
except Exception:
    try:
        _ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import subprocess
import os
import sys
import json
import uuid
import ctypes
import psutil
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image
from io import BytesIO

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 경로 설정
BACKEND_DIR = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent
ENGINE_DIR = PROJECT_ROOT / "engine"

# 아이콘 체인저 경로
ICON_CONFIG_PATH = ENGINE_DIR / "icons_config.json"
OVERLAY_PID_PATH  = ENGINE_DIR / ".overlay.pid"
SIG_RELOAD        = ENGINE_DIR / ".sig_reload"       # 전체 재로드 신호
SIG_REPOSITION    = ENGINE_DIR / ".sig_reposition"   # 위치만 업데이트 신호
SETTINGS_PATH    = ENGINE_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "mode":         "free",   # "free" | "grid"
    "grid_cell_w":  110,      # 격자 셀 너비 (px)
    "grid_cell_h":  130,      # 격자 셀 높이 (px)
    "grid_cols":    0,        # 0 = 자동 계산
}

def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except:
            pass
    return dict(DEFAULT_SETTINGS)

def save_settings(settings: dict):
    with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
CUSTOM_ICONS_DIR = ENGINE_DIR / "custom_icons"
DESKTOP_ICONS_CACHE = ENGINE_DIR / "desktop_icons_cache"

CUSTOM_ICONS_DIR.mkdir(exist_ok=True)
DESKTOP_ICONS_CACHE.mkdir(exist_ok=True)

# Windows subprocess 플래그
if sys.platform == "win32":
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0

# 정적 파일 마운트
app.mount("/custom_icons", StaticFiles(directory=str(CUSTOM_ICONS_DIR)), name="custom_icons")
app.mount("/desktop_cache", StaticFiles(directory=str(DESKTOP_ICONS_CACHE)), name="desktop_cache")


# =============================================================================
# Windows API - 바탕화면 아이콘 숨김/표시
# =============================================================================

user32 = ctypes.windll.user32
SW_HIDE = 0
SW_SHOW = 5


def find_desktop_icon_listview():
    """바탕화면 아이콘 ListView 찾기"""
    progman = user32.FindWindowW("Progman", None)
    defview = user32.FindWindowExW(progman, None, "SHELLDLL_DefView", None)

    if not defview:
        worker = None
        while True:
            worker = user32.FindWindowExW(None, worker, "WorkerW", None)
            if not worker:
                break
            defview = user32.FindWindowExW(worker, None, "SHELLDLL_DefView", None)
            if defview:
                break

    if not defview:
        return None

    listview = user32.FindWindowExW(defview, None, "SysListView32", "FolderView")
    return listview


def set_desktop_icons_visible(visible: bool):
    """바탕화면 아이콘 숨김/표시"""
    listview = find_desktop_icon_listview()
    if not listview:
        print("❌ 바탕화면 아이콘 핸들을 찾을 수 없습니다.")
        return False

    user32.ShowWindow(listview, SW_SHOW if visible else SW_HIDE)
    print(f"{'✅ 바탕화면 아이콘 표시' if visible else '✅ 바탕화면 아이콘 숨김'}")
    return True


# =============================================================================
# 오버레이 프로세스 관리
# =============================================================================

overlay_process = None


def send_signal(sig_path: Path):
    """오버레이에 신호 파일 전송"""
    try:
        sig_path.write_text("1")
        print(f"✅ 신호 전송: {sig_path.name}")
        return True
    except Exception as e:
        print(f"❌ 신호 전송 실패: {e}")
        return False


def notify_overlay(path: str) -> bool:
    """오버레이 IPC 서버에 명령 전송"""
    import urllib.request
    try:
        req = urllib.request.Request(
            f'http://127.0.0.1:19876{path}',
            data=b'', method='POST'
        )
        urllib.request.urlopen(req, timeout=1)
        print(f"✅ 오버레이 IPC 전송: {path}")
        return True
    except Exception as e:
        print(f"  IPC 실패 ({path}): {e}")
        return False


def is_overlay_running() -> bool:
    """IPC 포트로 실행 여부 확인 (가장 확실)"""
    import socket
    try:
        with socket.socket() as s:
            s.settimeout(0.5)
            return s.connect_ex(('127.0.0.1', 19876)) == 0
    except:
        pass
    # 폴백: PID 파일
    """PID 파일로 오버레이 실행 여부 확인 (가장 신뢰성 높음)"""
    if not OVERLAY_PID_PATH.exists():
        return False
    try:
        pid = int(OVERLAY_PID_PATH.read_text().strip())
        p = psutil.Process(pid)
        return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
    except:
        return False


def kill_overlay_processes():
    """오버레이 프로세스 종료 (PID 파일 우선, psutil 폴백)"""
    killed_count = 0

    # 방법 1: PID 파일로 직접 종료 (가장 확실)
    if OVERLAY_PID_PATH.exists():
        try:
            pid = int(OVERLAY_PID_PATH.read_text().strip())
            p = psutil.Process(pid)
            p.kill()
            killed_count += 1
            print(f"✅ PID 파일로 종료: PID {pid}")
        except Exception as e:
            print(f"  PID 파일 종료 실패: {e}")
        try:
            OVERLAY_PID_PATH.unlink(missing_ok=True)
        except:
            pass

    # 방법 2: cmdline 스캔 (폴백)
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline') or []
            if 'icon_overlay.py' in ' '.join(cmdline):
                proc.kill()
                killed_count += 1
                print(f"✅ cmdline 스캔으로 종료: PID {proc.pid}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return killed_count


# =============================================================================
# 오버레이 재시작 헬퍼
# =============================================================================

def restart_overlay_if_running():
    """오버레이가 실행 중이면 재시작, 아니면 아무것도 안 함"""
    import time
    killed = kill_overlay_processes()
    if killed > 0:
        time.sleep(0.4)
        script_path = ENGINE_DIR / "icon_overlay.py"
        if script_path.exists():
            if sys.platform == "win32":
                subprocess.Popen(
                    [sys.executable, str(script_path)],
                    cwd=str(ENGINE_DIR),
                    creationflags=CREATE_NO_WINDOW
                )
            else:
                subprocess.Popen(
                    [sys.executable, str(script_path)],
                    cwd=str(ENGINE_DIR)
                )
    return killed

# =============================================================================
# 바탕화면 아이콘 추출
# =============================================================================

def extract_icon_from_file(file_path: str, output_path: str):
    """파일에서 아이콘 추출"""
    try:
        import win32api
        import win32con
        import win32ui
        import win32gui
        
        # 아이콘 추출
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)
        
        large, small = win32gui.ExtractIconEx(file_path, 0)
        
        if large:
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
            hdc = hdc.CreateCompatibleDC()
            hdc.SelectObject(hbmp)
            hdc.DrawIcon((0, 0), large[0])
            
            # 비트맵을 PIL Image로 변환
            bmpstr = hbmp.GetBitmapBits(True)
            img = Image.frombuffer('RGB', (ico_x, ico_y), bmpstr, 'raw', 'BGRX', 0, 1)
            img.save(output_path, 'PNG')
            
            # 리소스 정리
            win32gui.DestroyIcon(large[0])
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ 아이콘 추출 실패: {e}")
        return False


# =============================================================================
# [기능 1: 계산기]
# =============================================================================

class CalcRequest(BaseModel):
    expression: str

@app.post("/api/calculate")
async def calculate(request: CalcRequest):
    try:
        result = eval(request.expression)
        return {"result": str(result)}
    except Exception:
        raise HTTPException(status_code=400, detail="잘못된 수식입니다.")


# =============================================================================
# [기능 2: 데스크톱 런처]
# =============================================================================

@app.post("/api/launch-launcher")
async def launch_launcher():
    try:
        script_path = ENGINE_DIR / "icno_changer_luncher.py"
        
        if not script_path.exists():
            raise HTTPException(status_code=404, detail=f"런처 파일을 찾을 수 없습니다: {script_path}")

        subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(script_path.parent),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        
        return {"status": "success", "message": "런처가 성공적으로 실행되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# [기능 3: 아이콘 체인저]
# =============================================================================

class IconMapping(BaseModel):
    icon_name: str
    image_path: str
    hover_image_path: str = ""
    target_path: str = ""
    x: int = 100
    y: int = 100
    size: int = 80
    show_name: bool = True
    font_family:   str  = "Segoe UI"
    font_size:     int  = 9
    font_bold:     bool = True
    font_italic:   bool = False
    font_color:    str  = "#ffffff"
    outline_color: str  = "#000000"


@app.get("/api/icons/desktop")
async def get_desktop_icons():
    """바탕화면 아이콘 목록 (아이콘 이미지 포함)"""
    try:
        import win32com.client
        
        # 개인 바탕화면 + 공용 바탕화면 둘 다 읽기
        public_folder = os.environ.get('PUBLIC', r'C:\Users\Public')
        desktops = [
            Path.home() / "Desktop",
            Path(public_folder) / "Desktop",
        ]
        icons = []
        seen = set()   # 중복 방지
        
        all_items = []
        for desktop in desktops:
            if desktop.exists():
                for item in desktop.iterdir():
                    if item.name not in seen:
                        seen.add(item.name)
                        all_items.append(item)
        
        if all_items:
            shell = win32com.client.Dispatch("WScript.Shell")
            
            for idx, item in enumerate(sorted(all_items)):
                if item.name.startswith('.') or item.name.startswith(' ') or item.name == 'desktop.ini':
                    continue
                
                # 위치 계산
                col = idx % 10
                row = idx // 10
                x = 20 + col * 100
                y = 20 + row * 100
                
                icon_info = {
                    'path': str(item),
                    'name': item.name.replace('.lnk', '').replace('.exe', ''),
                    'x': x,
                    'y': y,
                    'target_path': str(item)
                }
                
                # 아이콘 이미지 추출
                try:
                    cache_name = f"{item.stem}_{uuid.uuid4().hex[:8]}.png"
                    cache_path = DESKTOP_ICONS_CACHE / cache_name
                    
                    if item.suffix == '.lnk':
                        # 바로가기
                        shortcut = shell.CreateShortCut(str(item))
                        target = shortcut.TargetPath
                        icon_info['target_path'] = target if target else str(item)
                        
                        # 아이콘 추출
                        if target and os.path.exists(target):
                            if extract_icon_from_file(target, str(cache_path)):
                                icon_info['icon_url'] = f"/desktop_cache/{cache_name}"
                    
                    elif item.suffix == '.exe':
                        # 실행 파일
                        if extract_icon_from_file(str(item), str(cache_path)):
                            icon_info['icon_url'] = f"/desktop_cache/{cache_name}"
                    
                    # 아이콘 추출 실패 시 기본 아이콘
                    if 'icon_url' not in icon_info:
                        # 폴더인 경우
                        if item.is_dir():
                            icon_info['icon_url'] = None
                        else:
                            icon_info['icon_url'] = None
                            
                except Exception as e:
                    print(f"⚠️ 아이콘 추출 실패: {item.name} - {e}")
                    icon_info['icon_url'] = None
                
                icons.append(icon_info)
        
        return {"icons": icons}
        
    except Exception as e:
        print(f"❌ 바탕화면 아이콘 목록 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/icons/images")
async def get_custom_images():
    """업로드된 이미지 목록"""
    try:
        images = []
        
        if CUSTOM_ICONS_DIR.exists():
            for file in CUSTOM_ICONS_DIR.glob("*"):
                if file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
                    images.append({
                        'filename': file.name,
                        'path': str(file),
                        'url': f"/custom_icons/{file.name}"
                    })
        
        return {"images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/icons/upload")
async def upload_icon_image(file: UploadFile = File(...)):
    """이미지 업로드"""
    try:
        ext = Path(file.filename).suffix.lower()
        if ext not in ['.png', '.jpg', '.jpeg', '.gif']:
            raise HTTPException(status_code=400, detail="지원하지 않는 형식")
        
        unique_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        save_path = CUSTOM_ICONS_DIR / unique_name
        
        content = await file.read()

        if ext == '.gif':
            # GIF는 원본 그대로 저장 (변환하면 애니메이션 프레임 소실)
            with open(save_path, 'wb') as f:
                f.write(content)
        else:
            # 정적 이미지만 RGBA 변환 + 리사이즈
            img = Image.open(BytesIO(content))
            img = img.convert('RGBA')
            # 원본 해상도 최대한 보존 (사용자가 슬라이더로 크기 조절)
            # 매우 큰 이미지만 1024px로 제한 (메모리 절약)
            orig_w, orig_h = img.size
            max_dim = max(orig_w, orig_h)
            if max_dim > 1024:
                ratio = 1024 / max_dim
                img = img.resize(
                    (int(orig_w * ratio), int(orig_h * ratio)),
                    Image.Resampling.LANCZOS)
            img.save(save_path, 'PNG')

        return {
            "success": True,
            "filename": unique_name,
            "url": f"/custom_icons/{unique_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/icons/mappings")
async def get_icon_mappings():
    """현재 매핑 목록"""
    try:
        if not ICON_CONFIG_PATH.exists():
            return {"mappings": []}
        
        with open(ICON_CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            return {"mappings": []}
        
        return {"mappings": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/icons/mapping")
async def create_icon_mapping(mapping: IconMapping):
    """아이콘 매핑 생성"""
    try:
        print(f"\n매핑 생성: {mapping.icon_name}")
        
        if ICON_CONFIG_PATH.exists():
            try:
                with open(ICON_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                mappings = data if isinstance(data, list) else []
            except:
                mappings = []
        else:
            mappings = []
        
        # 같은 이름이 있으면 제거
        mappings = [m for m in mappings if isinstance(m, dict) and m.get('name') != mapping.icon_name]
        
        # 새 매핑 추가
        new_mapping = {
            'id':            str(uuid.uuid4()),
            'name':          mapping.icon_name,
            'image_path':    mapping.image_path,
            'target_path':   mapping.target_path,
            'x':             mapping.x,
            'y':             mapping.y,
            'size':          mapping.size,
            'hover_image_path': mapping.hover_image_path,
            'show_name':     mapping.show_name,
            'font_family':   mapping.font_family,
            'font_size':     mapping.font_size,
            'font_bold':     mapping.font_bold,
            'font_italic':   mapping.font_italic,
            'font_color':    mapping.font_color,
            'outline_color': mapping.outline_color,
        }
        
        mappings.append(new_mapping)
        
        with open(ICON_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 매핑 저장 완료 (실행 경로: {mapping.target_path})")
        
        # 오버레이에 IPC로 재로드 알림 (프로세스 재시작 없이 즉시 반영)
        notify_overlay("/reload")
        
        return {"success": True, "message": "매핑 저장됨"}
        
    except Exception as e:
        import traceback
        print(f"❌ 매핑 오류:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


class IconMappingUpdate(BaseModel):
    name:              str  = ""
    image_path:        str  = ""
    hover_image_path:  str  = ""
    target_path:       str  = ""
    size:              int  = 80
    show_name:         bool = True
    font_family:   str  = "Segoe UI"
    font_size:     int  = 9
    font_bold:     bool = True
    font_italic:   bool = False
    font_color:    str  = "#ffffff"
    outline_color: str  = "#000000"

@app.patch("/api/icons/mapping/{icon_id}")
async def update_icon_mapping(icon_id: str, data: IconMappingUpdate):
    """아이콘 수정 (이름, 이미지, 폰트 등)"""
    try:
        if not ICON_CONFIG_PATH.exists():
            raise HTTPException(status_code=404, detail="설정 파일 없음")

        with open(ICON_CONFIG_PATH, 'r', encoding='utf-8') as f:
            mappings = json.load(f)

        updated = False
        for m in mappings:
            if m.get('id') == icon_id:
                if data.name:          m['name']          = data.name
                if data.image_path:    m['image_path']    = data.image_path
                if data.target_path:   m['target_path']   = data.target_path
                m['size']          = data.size
                m['hover_image_path'] = data.hover_image_path
                m['show_name']     = data.show_name
                m['font_family']   = data.font_family
                m['font_size']     = data.font_size
                m['font_bold']     = data.font_bold
                m['font_italic']   = data.font_italic
                m['font_color']    = data.font_color
                m['outline_color'] = data.outline_color
                updated = True
                break

        if not updated:
            raise HTTPException(status_code=404, detail="아이콘을 찾을 수 없음")

        with open(ICON_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, ensure_ascii=False, indent=2)

        saved_size = next((m.get('size') for m in mappings if m.get('id') == icon_id), None)
        print(f"✅ 아이콘 수정 완료: {icon_id} | size={saved_size}")

        # 오버레이에 재로드 명령 전송 (실패해도 mtime 폴링이 백업)
        notify_overlay("/reload")
        return {"success": True, "message": "수정 완료", "saved_size": saved_size}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/icons/mapping/{icon_id}")
async def delete_icon_mapping(icon_id: str):
    """아이콘 매핑 삭제"""
    try:
        if not ICON_CONFIG_PATH.exists():
            raise HTTPException(status_code=404, detail="설정 파일 없음")
        
        with open(ICON_CONFIG_PATH, 'r', encoding='utf-8') as f:
            mappings = json.load(f)
        
        mappings = [m for m in mappings if m.get('id') != icon_id]
        
        with open(ICON_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, ensure_ascii=False, indent=2)
        
        # 오버레이에 IPC로 재로드 알림
        notify_overlay("/reload")
        
        return {"success": True, "message": "삭제 완료"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/icons/hide-desktop")
async def hide_desktop_icons():
    """바탕화면 아이콘 숨김"""
    try:
        success = set_desktop_icons_visible(False)
        
        if success:
            return {"success": True, "message": "바탕화면 아이콘 숨김 완료"}
        else:
            raise HTTPException(status_code=500, detail="바탕화면 아이콘을 찾을 수 없습니다")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/icons/show-desktop")
async def show_desktop_icons():
    """바탕화면 아이콘 표시 + 오버레이 종료"""
    try:
        # 1. 오버레이 프로세스 종료
        killed = kill_overlay_processes()
        print(f"✅ {killed}개 오버레이 프로세스 종료")
        
        # 2. 바탕화면 아이콘 표시
        success = set_desktop_icons_visible(True)
        
        if success:
            return {
                "success": True, 
                "message": f"바탕화면 복구 완료 (오버레이 {killed}개 종료)"
            }
        else:
            raise HTTPException(status_code=500, detail="바탕화면 아이콘을 찾을 수 없습니다")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 설정 관리 ──────────────────────────────────────────────────────────
@app.get("/api/settings")
async def get_settings():
    return load_settings()

class SettingsModel(BaseModel):
    mode:        str = "free"
    grid_cell_w: int = 110
    grid_cell_h: int = 130
    grid_cols:   int = 0

@app.post("/api/settings")
async def update_settings(s: SettingsModel):
    settings = load_settings()
    settings.update(s.dict())
    save_settings(settings)
    return {"success": True, "settings": settings}


# ── 그리드 정렬 ────────────────────────────────────────────────────────
def get_work_area():
    """작업 표시줄 제외 바탕화면 영역
    DPI-aware 앱에서 SystemParametersInfoW는 이미 논리픽셀 반환 - 변환 불필요"""
    import ctypes.wintypes as wt
    rect = wt.RECT()
    ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)
    return rect.left, rect.top, rect.right, rect.bottom

@app.post("/api/icons/arrange-grid")
async def arrange_grid():
    """모든 아이콘을 그리드에 맞춰 재배치 후 오버레이 재시작"""
    try:
        settings = load_settings()
        cell_w   = int(settings.get("grid_cell_w", 110))
        cell_h   = int(settings.get("grid_cell_h", 130))

        left, top, right, bottom = get_work_area()
        avail_h = bottom - top

        # 윈도우처럼 세로로 먼저 채움 (한 열에 들어갈 행 수 계산)
        rows_per_col = max(1, (avail_h - 20) // cell_h)

        if not ICON_CONFIG_PATH.exists():
            return {"success": True, "message": "아이콘 없음"}

        with open(ICON_CONFIG_PATH, 'r', encoding='utf-8') as f:
            icons = json.load(f)

        for i, icon in enumerate(icons):
            row = i % rows_per_col
            col = i // rows_per_col
            icon['x'] = left + 10 + col * cell_w
            icon['y'] = top  + 10 + row * cell_h

        with open(ICON_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(icons, f, ensure_ascii=False, indent=2)

        print(f"✅ 그리드 정렬: {len(icons)}개, {rows_per_col}행, 셀={cell_w}x{cell_h}")
        # 오버레이에 재배치 명령 전송 (깜빡임 없이 이동)
        notify_overlay("/reposition")
        return {"success": True,
                "message": f"{len(icons)}개 아이콘 그리드 정렬 완료 ({rows_per_col}행)"}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/icons/overlay-status")
async def get_overlay_status():
    """오버레이 실행 여부 - IPC 포트 19876 응답 여부로 판단"""
    import socket
    try:
        with socket.socket() as s:
            s.settimeout(0.5)
            running = s.connect_ex(('127.0.0.1', 19876)) == 0
    except:
        running = False
    print(f"  overlay-status: {running}")
    return {"running": running}


@app.get("/api/icons/pick-file")
async def pick_file_dialog():
    """QFileDialog로 파일 선택 - 기본 경로: 바탕화면 (공용 포함)"""
    import threading, queue
    result_q = queue.Queue()

    def _show_dialog():
        try:
            from PySide6.QtWidgets import QApplication, QFileDialog
            from PySide6.QtCore import Qt

            app = QApplication.instance()
            if not app:
                import sys
                app = QApplication(sys.argv)

            # 바탕화면 경로 (개인 우선)
            desktop = Path.home() / "Desktop"
            if not desktop.exists():
                public = os.environ.get('PUBLIC', r'C:\Users\Public')
                desktop = Path(public) / "Desktop"

            file_path, _ = QFileDialog.getOpenFileName(
                None,
                "실행 파일 선택",
                str(desktop),
                "모든 파일 (*.*)"
            )
            result_q.put(file_path or "")
        except Exception as e:
            print(f"파일 선택 오류: {e}")
            result_q.put("")

    t = threading.Thread(target=_show_dialog)
    t.start()
    t.join(timeout=60)

    file_path = result_q.get() if not result_q.empty() else ""
    name = Path(file_path).stem if file_path else ""
    return {"file_path": file_path, "name": name}


@app.post("/api/icons/reload-overlay")
async def reload_icon_overlay():
    """오버레이 재시작 - 무조건 kill 후 start"""
    global overlay_process
    import time

    # psutil 방식 + taskkill 이중으로 종료
    kill_overlay_processes()
    try:
        # 혹시 못 잡은 프로세스를 taskkill로도 시도
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/FI", "WINDOWTITLE eq 커스텀 아이콘 오버레이*"],
                capture_output=True
            )
    except:
        pass

    time.sleep(0.5)

    script_path = ENGINE_DIR / "icon_overlay.py"
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="오버레이 파일 없음")

    try:
        if sys.platform == "win32":
            overlay_process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(ENGINE_DIR),
                creationflags=CREATE_NO_WINDOW
            )
        else:
            overlay_process = subprocess.Popen(
                [sys.executable, str(script_path)], cwd=str(ENGINE_DIR))

        print(f"✅ 오버레이 재시작: PID {overlay_process.pid}")
        return {"success": True, "message": "오버레이 재시작 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/icons/start-overlay")
async def start_icon_overlay():
    """커스텀 아이콘 오버레이 시작"""
    global overlay_process
    
    try:
        script_path = ENGINE_DIR / "icon_overlay.py"
        
        if not script_path.exists():
            raise HTTPException(status_code=404, detail=f"오버레이 파일을 찾을 수 없습니다: {script_path}")
        
        if sys.platform == "win32":
            overlay_process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(ENGINE_DIR),
                creationflags=CREATE_NO_WINDOW
            )
        else:
            overlay_process = subprocess.Popen([sys.executable, str(script_path)], cwd=str(ENGINE_DIR))
        
        print(f"✅ 오버레이 시작: PID {overlay_process.pid}")
        
        return {"success": True, "message": "오버레이가 시작되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/icons/launch-apply-window")
async def launch_apply_window():
    """적용창 앱 실행"""
    try:
        app_path = PROJECT_ROOT / "apply_window_app.py"
        
        if not app_path.exists():
            raise HTTPException(status_code=404, detail=f"적용창 앱을 찾을 수 없습니다: {app_path}")
        
        pythonw_exe = Path(sys.executable).parent / "pythonw.exe"
        if not pythonw_exe.exists():
            pythonw_exe = sys.executable
        
        if sys.platform == "win32":
            subprocess.Popen(
                [str(pythonw_exe), str(app_path)],
                cwd=str(PROJECT_ROOT),
                creationflags=CREATE_NO_WINDOW
            )
        else:
            subprocess.Popen([str(pythonw_exe), str(app_path)], cwd=str(PROJECT_ROOT))
        
        return {"success": True, "message": "적용창 앱이 시작되었습니다"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
