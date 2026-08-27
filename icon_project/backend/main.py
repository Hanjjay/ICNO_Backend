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
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from PIL import Image
from io import BytesIO

# ── 개발/릴리스 모드 ─────────────────────────────────────────────
# 릴리스에서는 ICNO_DEV=0 으로 실행해 /docs, /openapi 를 비활성화한다.
# (공격자가 API 명세를 읽어 자동화 공격에 쓰는 것을 방지)
IS_DEV = os.environ.get("ICNO_DEV", "1") != "0"

app = FastAPI(
    docs_url="/docs" if IS_DEV else None,
    redoc_url="/redoc" if IS_DEV else None,
    openapi_url="/openapi.json" if IS_DEV else None,
)

# ── 허용 Origin (CSRF 방지) ───────────────────────────────────────
# 프론트 개발 서버 + (배포 시) 실제 프론트 도메인. 환경변수로 추가 가능.
ALLOWED_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",   # Vite 개발서버(Lovable 기본 포트)
    "http://127.0.0.1:8080",
}
if IS_DEV:
    ALLOWED_ORIGINS |= {"http://127.0.0.1:8000", "http://localhost:8000"}  # Swagger 용
_extra = os.environ.get("ICNO_ALLOWED_ORIGINS", "").strip()
if _extra:
    ALLOWED_ORIGINS |= {o.strip() for o in _extra.split(",") if o.strip()}

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    # 개발 모드에선 localhost/127.0.0.1/[::1] 의 어떤 포트든 허용
    # (Vite 포트가 5173/8080 등으로 바뀌어도 이미지 fetch 가 CORS 로 막히지 않게)
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|\[::1\]):\d+" if IS_DEV else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Origin 검증 미들웨어 (CSRF 방어) ──────────────────────────────
# 상태 변경 요청(POST/PUT/PATCH/DELETE)과 민감 GET(pick-file)에 대해,
# 브라우저가 보낸 Origin 이 허용 목록에 없으면 403 으로 차단한다.
# Origin 이 없는 요청(비브라우저 도구/동일 출처)은 통과시킨다.
_SENSITIVE_GET_PATHS = {"/api/icons/pick-file"}

@app.middleware("http")
async def origin_guard(request, call_next):
    method = request.method.upper()
    path = request.url.path
    if method in ("POST", "PUT", "PATCH", "DELETE") or path in _SENSITIVE_GET_PATHS:
        origin = request.headers.get("origin")
        if origin is not None and origin not in ALLOWED_ORIGINS:
            return JSONResponse(status_code=403, content={"detail": "Origin not allowed"})
    return await call_next(request)

# ── Vary: Origin 강제 ─────────────────────────────────────────────
# 이미지가 <img>(비-CORS, Origin 없음)로 먼저 캐시되면, 이후 fetch()(CORS,
# Origin 있음)가 그 CORS 헤더 없는 캐시본을 재사용해 CORS 에러가 난다.
# Vary: Origin 을 붙여 브라우저가 두 요청을 캐시에서 구분하게 한다.
@app.middleware("http")
async def add_vary_origin(request, call_next):
    response = await call_next(request)
    vary = response.headers.get("vary")
    if not vary:
        response.headers["Vary"] = "Origin"
    elif "origin" not in vary.lower():
        response.headers["Vary"] = vary + ", Origin"
    return response

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
    "mode":             "free",   # "free" | "grid"
    "grid_cell_w":      110,      # 격자 셀 너비 (px)
    "grid_cell_h":      130,      # 격자 셀 높이 (px)
    "grid_cols":        0,        # 0 = 자동 계산
    "overlay_autostart": False,   # 앱 시작 시 오버레이 자동 시작
    "restore_on_exit":   True,    # 앱 종료 시 기본 데스크톱 아이콘 복원
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

# ── 신규 저장소 (Phase A/B/B2/C) ─────────────────────────────────────────
LIBRARY_PATH   = ENGINE_DIR / "library.json"    # 보관함 아이콘 메타데이터
WALLPAPER_LIBRARY_PATH = ENGINE_DIR / "wallpaper_library.json"  # 보관함 배경화면 메타데이터
PRESETS_PATH   = ENGINE_DIR / "presets.json"    # 프리셋(배치/매핑 참조) - 로컬 저장
WALLPAPERS_DIR = ENGINE_DIR / "wallpapers"      # 업로드된 배경화면 원본
BACKUP_DIR     = ENGINE_DIR / ".backup"         # apply-local 롤백용 백업
# 프리셋을 처음 적용하기 직전의 '원래' 배경화면(1회 저장) - 끄기/종료 시 복원용
ORIGINAL_WALLPAPER_PATH = ENGINE_DIR / ".original_wallpaper.txt"
# 현재 적용된 프리셋의 배경화면 경로 - 오버레이 '켜기' 때 재적용용
ACTIVE_WALLPAPER_PATH   = ENGINE_DIR / ".active_wallpaper.txt"
# 현재 적용된 프리셋 id - 홈 화면 '현재 적용 중' 표시용
ACTIVE_PRESET_PATH      = ENGINE_DIR / ".active_preset.txt"

WALLPAPERS_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)


def _load_json(path: Path, default):
    if not path.exists():
        return default() if callable(default) else default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default() if callable(default) else default


def _save_json(path: Path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_library() -> list:
    data = _load_json(LIBRARY_PATH, list)
    return data if isinstance(data, list) else []


def save_library(assets: list):
    _save_json(LIBRARY_PATH, assets)


def load_wallpaper_library() -> list:
    data = _load_json(WALLPAPER_LIBRARY_PATH, list)
    return data if isinstance(data, list) else []


def save_wallpaper_library(assets: list):
    _save_json(WALLPAPER_LIBRARY_PATH, assets)


def load_presets() -> list:
    data = _load_json(PRESETS_PATH, list)
    return data if isinstance(data, list) else []


def save_presets(presets: list):
    _save_json(PRESETS_PATH, presets)


def load_mappings() -> list:
    data = _load_json(ICON_CONFIG_PATH, list)
    return data if isinstance(data, list) else []


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(content: bytes) -> str:
    import hashlib
    return hashlib.sha256(content).hexdigest()


# ── 보안 헬퍼 (파일/이미지 검증) ─────────────────────────────────────────
MAX_ICON_BYTES      = 15 * 1024 * 1024   # 아이콘 업로드 상한 15MB
MAX_WALLPAPER_BYTES = 40 * 1024 * 1024   # 배경화면 업로드 상한 40MB
# PIL 디컴프레션 봄(decompression bomb) 방지: 지나치게 큰 이미지 거부
try:
    Image.MAX_IMAGE_PIXELS = 64_000_000  # 약 8000x8000
except Exception:
    pass


def _is_within(base: Path, target: Path) -> bool:
    """target 경로가 base 폴더 안에 있는지 검증 (경로 탈출 '../' 방지)."""
    try:
        base_r = base.resolve()
        target_r = target.resolve()
        return target_r == base_r or base_r in target_r.parents
    except Exception:
        return False


def _validate_image_bytes(content: bytes, allowed_formats: set) -> str:
    """PIL로 실제 이미지인지 검증하고 포맷을 반환. 확장자 위조/손상 파일 차단."""
    try:
        with Image.open(BytesIO(content)) as im:
            fmt = (im.format or "").upper()
            im.verify()  # 손상/위조 검사
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="유효한 이미지 파일이 아닙니다.")
    if fmt not in allowed_formats:
        raise HTTPException(status_code=400, detail=f"허용되지 않은 이미지 형식: {fmt}")
    return fmt


def _adopt_orphan_icons() -> list:
    """custom_icons 폴더에 있으나 library.json에 없는 파일을 흡수.

    asset_id 안정성: 파일 내용 sha256을 계산해, 같은 내용이 이미 등록돼 있으면
    기존 asset_id를 재사용한다(새 id 남발 방지). 기존 항목의 파일이 사라졌다면
    이 파일로 복구(repoint)해 참조 깨짐을 최소화한다. 없을 때만 새 id 발급."""
    library = load_library()
    known = {a.get("storage_filename") for a in library}
    # 내용 해시 → 기존 asset (해시가 기록된 항목만)
    sha_map = {a.get("sha256"): a for a in library if a.get("sha256")}
    changed = False
    for f in sorted(CUSTOM_ICONS_DIR.glob("*")):
        if f.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.gif']:
            continue
        if f.name in known:
            continue
        try:
            sha = _sha256_bytes(f.read_bytes())
        except Exception:
            sha = ""

        existing = sha_map.get(sha) if sha else None
        if existing:
            # 같은 내용이 이미 등록됨 → 기존 asset 재사용.
            old_name = existing.get("storage_filename", "")
            if not (CUSTOM_ICONS_DIR / old_name).exists():
                # 기존 파일이 사라졌으면 이 파일로 복구(repoint)
                existing["storage_filename"] = f.name
                existing["local_image_path"] = str(f)
                existing["updated_at"] = _now_iso()
                known.add(f.name)
                changed = True
            # 파일이 살아있으면 중복 내용이므로 새 항목을 만들지 않음
            continue

        # 신규 내용 → 새 asset 발급 (sha256 기록)
        entry = {
            "asset_id":         str(uuid.uuid4()),
            "display_name":     f.stem,
            "storage_filename": f.name,
            "local_image_path": str(f),
            "origin":           "local-engine",
            "pack_id":          None,
            "sha256":           sha,
            "created_at":       _now_iso(),
            "updated_at":       _now_iso(),
        }
        library.append(entry)
        known.add(f.name)
        if sha:
            sha_map[sha] = entry
        changed = True
    if changed:
        save_library(library)
    return library


def _adopt_orphan_wallpapers() -> list:
    """wallpapers 폴더에 있으나 wallpaper_library.json에 없는 파일을 흡수.
    (프리셋에 딸려 저장됐거나 이전 버전에서 업로드된 배경을 보관함에 노출)
    _adopt_orphan_icons 와 동일한 sha256 안정화 로직 사용."""
    library = load_wallpaper_library()
    known = {a.get("storage_filename") for a in library}
    sha_map = {a.get("sha256"): a for a in library if a.get("sha256")}
    changed = False
    for f in sorted(WALLPAPERS_DIR.glob("*")):
        if f.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.gif']:
            continue
        if f.name in known:
            continue
        try:
            sha = _sha256_bytes(f.read_bytes())
        except Exception:
            sha = ""

        existing = sha_map.get(sha) if sha else None
        if existing:
            old_name = existing.get("storage_filename", "")
            if not (WALLPAPERS_DIR / old_name).exists():
                existing["storage_filename"] = f.name
                existing["local_image_path"] = str(f)
                existing["updated_at"] = _now_iso()
                known.add(f.name)
                changed = True
            continue

        entry = {
            "asset_id":         str(uuid.uuid4()),
            "display_name":     f.stem,
            "storage_filename": f.name,
            "local_image_path": str(f),
            "origin":           "local-engine",
            "sha256":           sha,
            "created_at":       _now_iso(),
            "updated_at":       _now_iso(),
        }
        library.append(entry)
        known.add(f.name)
        if sha:
            sha_map[sha] = entry
        changed = True
    if changed:
        save_wallpaper_library(library)
    return library

# Windows subprocess 플래그
if sys.platform == "win32":
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0

# 정적 파일 마운트
app.mount("/custom_icons", StaticFiles(directory=str(CUSTOM_ICONS_DIR)), name="custom_icons")
app.mount("/desktop_cache", StaticFiles(directory=str(DESKTOP_ICONS_CACHE)), name="desktop_cache")
app.mount("/wallpapers", StaticFiles(directory=str(WALLPAPERS_DIR)), name="wallpapers")


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
    """업로드된 이미지 목록 (asset_id 포함 - 보관함 흡수용)"""
    try:
        library = _adopt_orphan_icons()
        by_name = {a.get("storage_filename"): a for a in library}
        images = []

        if CUSTOM_ICONS_DIR.exists():
            for file in CUSTOM_ICONS_DIR.glob("*"):
                if file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
                    a = by_name.get(file.name, {})
                    images.append({
                        'filename': file.name,
                        'path': str(file),
                        'url': f"/custom_icons/{file.name}",
                        'asset_id': a.get('asset_id'),
                        'storage_filename': file.name,
                        'display_name': a.get('display_name'),
                    })

        return {"images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/icons/upload")
async def upload_icon_image(file: UploadFile = File(...)):
    """이미지 업로드 (Phase A: sha256 중복 방지 + library.json 기록)

    응답에 asset_id / local_image_path / storage_filename / duplicate 를 추가.
    기존 필드(success/filename/url)는 하위호환을 위해 그대로 유지한다.
    """
    try:
        ext = Path(file.filename).suffix.lower()
        if ext not in ['.png', '.jpg', '.jpeg', '.gif']:
            raise HTTPException(status_code=400, detail="지원하지 않는 형식")

        content = await file.read()
        if len(content) > MAX_ICON_BYTES:
            raise HTTPException(status_code=400, detail="파일이 너무 큽니다 (최대 15MB)")
        # 실제 이미지인지 검증 (확장자 위조/손상 파일 차단)
        _validate_image_bytes(content, {"PNG", "JPEG", "GIF"})
        sha = _sha256_bytes(content)

        # ── 중복 방지: 동일 sha256 이 이미 보관함에 있으면 재저장 없이 반환 ──
        library = load_library()
        for a in library:
            if a.get("sha256") == sha and (CUSTOM_ICONS_DIR / a.get("storage_filename", "")).exists():
                return {
                    "success": True,
                    "duplicate": True,
                    "asset_id": a.get("asset_id"),
                    "storage_filename": a.get("storage_filename"),
                    "local_image_path": a.get("local_image_path"),
                    "display_name": a.get("display_name"),
                    "filename": a.get("storage_filename"),          # 하위호환
                    "url": f"/custom_icons/{a.get('storage_filename')}",
                }

        # 파일명을 순수 UUID로 생성 (원본 파일명 미사용 → 경로 탈출/위조 차단)
        is_gif = (ext == '.gif')
        unique_name = f"{uuid.uuid4().hex}{'.gif' if is_gif else '.png'}"
        save_path = CUSTOM_ICONS_DIR / unique_name
        if not _is_within(CUSTOM_ICONS_DIR, save_path):
            raise HTTPException(status_code=400, detail="잘못된 저장 경로")

        if is_gif:
            # GIF는 원본 그대로 저장 (변환하면 애니메이션 프레임 소실)
            with open(save_path, 'wb') as f:
                f.write(content)
        else:
            # 정적 이미지만 RGBA 변환 + 리사이즈
            img = Image.open(BytesIO(content))
            img = img.convert('RGBA')
            orig_w, orig_h = img.size
            max_dim = max(orig_w, orig_h)
            if max_dim > 1024:
                ratio = 1024 / max_dim
                img = img.resize(
                    (int(orig_w * ratio), int(orig_h * ratio)),
                    Image.Resampling.LANCZOS)
            img.save(save_path, 'PNG')

        asset_id = str(uuid.uuid4())
        display_name = Path(file.filename).stem
        entry = {
            "asset_id":         asset_id,
            "display_name":     display_name,
            "storage_filename": unique_name,
            "local_image_path": str(save_path),
            "origin":           "user-upload",
            "pack_id":          None,
            "sha256":           sha,
            "created_at":       _now_iso(),
            "updated_at":       _now_iso(),
        }
        library.append(entry)
        save_library(library)

        return {
            "success": True,
            "duplicate": False,
            "asset_id": asset_id,
            "storage_filename": unique_name,
            "local_image_path": str(save_path),
            "display_name": display_name,
            "filename": unique_name,          # 하위호환
            "url": f"/custom_icons/{unique_name}",
        }
    except HTTPException:
        raise
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
    # 모두 Optional → 보낸 필드만 부분 업데이트(grid 저장이 오버레이 설정을 덮지 않도록)
    mode:              Optional[str]  = None
    grid_cell_w:       Optional[int]  = None
    grid_cell_h:       Optional[int]  = None
    grid_cols:         Optional[int]  = None
    overlay_autostart: Optional[bool] = None
    restore_on_exit:   Optional[bool] = None

@app.post("/api/settings")
async def update_settings(s: SettingsModel):
    settings = load_settings()
    settings.update(s.dict(exclude_unset=True, exclude_none=True))  # 보낸 값만 반영
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
    """Windows 네이티브 파일 선택 대화상자(comdlg32 GetOpenFileNameW) - 절대경로 반환.
    Qt QFileDialog는 별도 스레드에서 불안정하므로 ctypes 네이티브 API 사용."""
    import threading, queue
    result_q = queue.Queue()

    def _show_dialog():
        try:
            import ctypes
            from ctypes import wintypes

            desktop = Path.home() / "Desktop"
            if not desktop.exists():
                public = os.environ.get('PUBLIC', r'C:\Users\Public')
                desktop = Path(public) / "Desktop"

            class OPENFILENAMEW(ctypes.Structure):
                _fields_ = [
                    ("lStructSize", wintypes.DWORD),
                    ("hwndOwner", wintypes.HWND),
                    ("hInstance", wintypes.HINSTANCE),
                    ("lpstrFilter", wintypes.LPCWSTR),
                    ("lpstrCustomFilter", wintypes.LPWSTR),
                    ("nMaxCustFilter", wintypes.DWORD),
                    ("nFilterIndex", wintypes.DWORD),
                    ("lpstrFile", wintypes.LPWSTR),
                    ("nMaxFile", wintypes.DWORD),
                    ("lpstrFileTitle", wintypes.LPWSTR),
                    ("nMaxFileTitle", wintypes.DWORD),
                    ("lpstrInitialDir", wintypes.LPCWSTR),
                    ("lpstrTitle", wintypes.LPCWSTR),
                    ("Flags", wintypes.DWORD),
                    ("nFileOffset", wintypes.WORD),
                    ("nFileExtension", wintypes.WORD),
                    ("lpstrDefExt", wintypes.LPCWSTR),
                    ("lCustData", wintypes.LPARAM),
                    ("lpfnHook", wintypes.LPVOID),
                    ("lpTemplateName", wintypes.LPCWSTR),
                    ("pvReserved", wintypes.LPVOID),
                    ("dwReserved", wintypes.DWORD),
                    ("FlagsEx", wintypes.DWORD),
                ]

            buf = ctypes.create_unicode_buffer(1024)
            ofn = OPENFILENAMEW()
            ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
            try:
                ofn.hwndOwner = ctypes.windll.user32.GetForegroundWindow()
            except Exception:
                ofn.hwndOwner = 0
            ofn.lpstrFile = ctypes.cast(buf, wintypes.LPWSTR)
            ofn.nMaxFile = 1024
            ofn.lpstrTitle = "실행 파일/폴더 선택"
            ofn.lpstrInitialDir = str(desktop)
            # OFN_FILEMUSTEXIST(0x1000)|OFN_HIDEREADONLY(0x4)|OFN_EXPLORER(0x80000)|OFN_NOCHANGEDIR(0x8)
            ofn.Flags = 0x1000 | 0x4 | 0x80000 | 0x8

            ok = ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(ofn))
            result_q.put(buf.value if ok else "")
        except Exception as e:
            print(f"파일 선택 오류: {e}")
            result_q.put("")

    t = threading.Thread(target=_show_dialog)
    t.start()
    t.join(timeout=120)

    file_path = result_q.get() if not result_q.empty() else ""
    name = Path(file_path).stem if file_path else ""
    return {"file_path": file_path, "name": name}


@app.get("/api/icons/pick-folder")
async def pick_folder_dialog():
    """Windows 네이티브 폴더 선택 대화상자(SHBrowseForFolderW) - 폴더 절대경로 반환.
    아이콘 대상으로 '폴더'를 지정할 때 사용(클릭 시 탐색기로 폴더 열림)."""
    import threading, queue
    result_q = queue.Queue()

    def _show_dialog():
        try:
            import ctypes
            from ctypes import wintypes

            class BROWSEINFO(ctypes.Structure):
                _fields_ = [
                    ("hwndOwner", wintypes.HWND),
                    ("pidlRoot", ctypes.c_void_p),
                    ("pszDisplayName", wintypes.LPWSTR),
                    ("lpszTitle", wintypes.LPCWSTR),
                    ("ulFlags", wintypes.UINT),
                    ("lpfn", ctypes.c_void_p),
                    ("lParam", wintypes.LPARAM),
                    ("iImage", ctypes.c_int),
                ]

            shell32 = ctypes.windll.shell32
            ole32   = ctypes.windll.ole32
            try:
                ole32.OleInitialize(None)   # BIF_NEWDIALOGSTYLE 요구사항
            except Exception:
                pass

            shell32.SHBrowseForFolderW.restype  = ctypes.c_void_p
            shell32.SHBrowseForFolderW.argtypes = [ctypes.c_void_p]
            shell32.SHGetPathFromIDListW.argtypes = [ctypes.c_void_p, wintypes.LPWSTR]

            display = ctypes.create_unicode_buffer(260)
            bi = BROWSEINFO()
            try:
                bi.hwndOwner = ctypes.windll.user32.GetForegroundWindow()
            except Exception:
                bi.hwndOwner = 0
            bi.pidlRoot = None
            bi.pszDisplayName = ctypes.cast(display, wintypes.LPWSTR)
            bi.lpszTitle = "폴더 선택"
            # BIF_RETURNONLYFSDIRS(0x1) | BIF_NEWDIALOGSTYLE(0x40)
            bi.ulFlags = 0x0001 | 0x0040

            pidl = shell32.SHBrowseForFolderW(ctypes.byref(bi))
            path = ""
            if pidl:
                path_buf = ctypes.create_unicode_buffer(1024)
                if shell32.SHGetPathFromIDListW(pidl, path_buf):
                    path = path_buf.value
                try:
                    ole32.CoTaskMemFree(pidl)
                except Exception:
                    pass
            try:
                ole32.OleUninitialize()
            except Exception:
                pass
            result_q.put(path)
        except Exception as e:
            print(f"폴더 선택 오류: {e}")
            result_q.put("")

    t = threading.Thread(target=_show_dialog)
    t.start()
    t.join(timeout=120)

    folder_path = result_q.get() if not result_q.empty() else ""
    name = Path(folder_path).name if folder_path else ""
    return {"file_path": folder_path, "name": name}


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


# =============================================================================
# [Phase B] 보관함 메타데이터 API (library.json)
# =============================================================================

def _model_dump(m) -> dict:
    return m.model_dump() if hasattr(m, "model_dump") else m.dict()


@app.get("/api/icons/library")
async def get_icon_library():
    """보관함 아이콘 목록. 실제 파일 존재 여부(file_exists)를 함께 반환.
    custom_icons 폴더의 미등록 파일은 asset_id를 부여해 흡수한다."""
    library = _adopt_orphan_icons()
    for a in library:
        a["file_exists"] = (CUSTOM_ICONS_DIR / a.get("storage_filename", "")).exists()
    return {"assets": library}


class LibraryPatchModel(BaseModel):
    display_name: str


@app.patch("/api/icons/library/{asset_id}")
async def update_library_asset(asset_id: str, data: LibraryPatchModel):
    """표시 이름(display_name)만 변경. 파일명/경로는 불변."""
    library = load_library()
    found = False
    for a in library:
        if a.get("asset_id") == asset_id:
            a["display_name"] = data.display_name
            a["updated_at"] = _now_iso()
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="보관함 아이콘을 찾을 수 없음")
    save_library(library)
    return {"success": True, "asset_id": asset_id, "display_name": data.display_name}


def _find_asset_references(asset: dict) -> dict:
    """이 아이콘을 참조하는 프리셋 / 활성 매핑 / 파일 공유 항목을 조사."""
    asset_id = asset.get("asset_id")
    local_path = asset.get("local_image_path")
    storage = asset.get("storage_filename")

    preset_refs = []
    for p in load_presets():
        for ic in p.get("icons", []):
            if ic.get("asset_id") == asset_id:
                preset_refs.append(p.get("id"))
                break

    mapping_refs = []
    for m in load_mappings():
        if local_path and m.get("image_path") == local_path:
            mapping_refs.append(m.get("id"))

    shared = [
        a.get("asset_id") for a in load_library()
        if a.get("asset_id") != asset_id and a.get("storage_filename") == storage
    ]
    return {"presets": preset_refs, "active_mappings": mapping_refs, "shared_assets": shared}


@app.delete("/api/icons/library/{asset_id}")
async def delete_library_asset(asset_id: str, force: bool = False):
    """보관함 아이콘 삭제. 참조가 있으면 409. force=true 로 강제 삭제."""
    library = load_library()
    asset = next((a for a in library if a.get("asset_id") == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="보관함 아이콘을 찾을 수 없음")

    refs = _find_asset_references(asset)
    in_use = bool(refs["presets"] or refs["active_mappings"])
    if in_use and not force:
        return JSONResponse(
            status_code=409,
            content={"detail": "Icon asset is still in use", "references": refs},
        )

    library = [a for a in library if a.get("asset_id") != asset_id]
    still_shared = any(
        a.get("storage_filename") == asset.get("storage_filename") for a in library
    )
    save_library(library)

    deleted_file = False
    if not still_shared:
        try:
            fp = CUSTOM_ICONS_DIR / asset.get("storage_filename", "")
            if _is_within(CUSTOM_ICONS_DIR, fp) and fp.exists():
                fp.unlink()
                deleted_file = True
        except Exception as e:
            print(f"⚠️ 파일 삭제 실패: {e}")

    return {"success": True, "deleted_file": deleted_file, "forced": bool(in_use and force)}


# =============================================================================
# [Phase B2] 프리셋 로컬 저장 API (presets.json)
# =============================================================================

class PresetIconModel(BaseModel):
    asset_id:         str  = ""
    icon_name:        str  = ""
    target_path:      str  = ""
    x:                float = 0
    y:                float = 0
    size:             float = 72
    show_name:        bool = True
    hover_image_path: str  = ""
    font_family:      str  = "맑은 고딕"
    font_size:        int  = 10
    font_bold:        bool = True
    font_italic:      bool = False
    font_color:       str  = "#ffffff"
    outline_color:    str  = "#000000"


class PresetSettingsModel(BaseModel):
    mode:        str = "free"
    grid_cell_w: int = 110
    grid_cell_h: int = 130
    grid_cols:   int = 0


class CanvasModel(BaseModel):
    w: int = 1920
    h: int = 1080


class PresetModel(BaseModel):
    id:             str = ""
    name:           str = ""
    wallpaper_path: str = ""
    settings:       PresetSettingsModel = Field(default_factory=PresetSettingsModel)
    canvas:         CanvasModel = Field(default_factory=CanvasModel)
    icons:          list[PresetIconModel] = Field(default_factory=list)


def _enrich_preset(p: dict, lib: dict = None) -> dict:
    """프리셋에 렌더용 상대 URL을 추가(저장은 안 함).
    - wallpaper_url: /wallpapers/<파일명>
    - icons[].image_url: asset_id → library → /custom_icons/<파일명>
    프론트는 localEngineUrl()로 접두어를 붙여 썸네일/미리보기를 렌더한다."""
    if lib is None:
        lib = {a.get("asset_id"): a for a in load_library()}
    q = dict(p)
    wp = p.get("wallpaper_path", "") or ""
    q["wallpaper_url"] = f"/wallpapers/{os.path.basename(wp)}" if wp else ""
    icons = []
    for ic in p.get("icons", []):
        ic2 = dict(ic)
        a = lib.get(ic.get("asset_id"))
        ic2["image_url"] = f"/custom_icons/{a.get('storage_filename')}" if a and a.get("storage_filename") else ""
        icons.append(ic2)
    q["icons"] = icons
    return q


@app.get("/api/presets")
async def list_presets():
    lib = {a.get("asset_id"): a for a in load_library()}
    return {"presets": [_enrich_preset(p, lib) for p in load_presets()]}


@app.get("/api/active-preset")
async def get_active_preset():
    """현재 적용 중인 프리셋(홈 화면 표시용). 없으면 active=None."""
    try:
        if not ACTIVE_PRESET_PATH.exists():
            return {"active": None}
        pid = ACTIVE_PRESET_PATH.read_text(encoding="utf-8").strip()
        p = next((x for x in load_presets() if x.get("id") == pid), None)
        return {"active": _enrich_preset(p) if p else None}
    except Exception:
        return {"active": None}


@app.get("/api/presets/{preset_id}")
async def get_preset(preset_id: str):
    p = next((x for x in load_presets() if x.get("id") == preset_id), None)
    if not p:
        raise HTTPException(status_code=404, detail="프리셋을 찾을 수 없음")
    return _enrich_preset(p)


@app.post("/api/presets")
async def create_preset(preset: PresetModel):
    presets = load_presets()
    data = _model_dump(preset)
    # id는 항상 서버가 발급 (클라이언트가 보낸 id로 기존 프리셋을 덮어쓰는 것 방지)
    data["id"] = str(uuid.uuid4())
    data["created_at"] = _now_iso()
    data["updated_at"] = _now_iso()
    presets.append(data)
    save_presets(presets)
    return {"success": True, "id": data["id"], "preset": data}


@app.put("/api/presets/{preset_id}")
async def update_preset(preset_id: str, preset: PresetModel):
    presets = load_presets()
    existing = next((x for x in presets if x.get("id") == preset_id), None)
    data = _model_dump(preset)
    data["id"] = preset_id
    data["created_at"] = existing.get("created_at") if existing else _now_iso()
    data["updated_at"] = _now_iso()
    presets = [x for x in presets if x.get("id") != preset_id]
    presets.append(data)
    save_presets(presets)
    return {"success": True, "id": preset_id, "preset": data}


@app.delete("/api/presets/{preset_id}")
async def delete_preset(preset_id: str):
    presets = load_presets()
    if not any(x.get("id") == preset_id for x in presets):
        raise HTTPException(status_code=404, detail="프리셋을 찾을 수 없음")
    presets = [x for x in presets if x.get("id") != preset_id]
    save_presets(presets)
    return {"success": True}


@app.patch("/api/presets/{preset_id}")
async def patch_preset(preset_id: str, patch: dict):
    """프리셋 부분 수정 (이름 변경 등). 허용 필드만, 스키마 검증 후 병합.

    대량 할당 방지: 중첩 값(settings/canvas/icons)을 타입 모델로 재검증해
    선언되지 않은(미사용) 필드가 주입/저장되지 않도록 한다.
    """
    presets = load_presets()
    p = next((x for x in presets if x.get("id") == preset_id), None)
    if not p:
        raise HTTPException(status_code=404, detail="프리셋을 찾을 수 없음")
    try:
        for k in ("name", "wallpaper_path", "settings", "canvas", "icons"):
            if k not in patch:
                continue
            v = patch[k]
            if k == "settings":
                p[k] = _model_dump(PresetSettingsModel(**(v or {})))
            elif k == "canvas":
                p[k] = _model_dump(CanvasModel(**(v or {})))
            elif k == "icons":
                p[k] = [_model_dump(PresetIconModel(**(ic or {}))) for ic in (v or [])]
            else:  # name, wallpaper_path — 문자열만 허용
                p[k] = str(v) if v is not None else ""
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"잘못된 프리셋 데이터: {e}")
    p["updated_at"] = _now_iso()
    save_presets(presets)
    return {"success": True, "id": preset_id, "preset": _enrich_preset(p)}


# =============================================================================
# [Phase 5] 마켓 다운로드 → 보관함 import
# =============================================================================
MARKET_MAX_ICONS           = 30
MARKET_MAX_ICON_BYTES      = 5 * 1024 * 1024    # 아이콘당 5MB
MARKET_MAX_WALLPAPER_BYTES = 15 * 1024 * 1024   # 배경 15MB (버킷 상한과 동일)
MARKET_MAX_TOTAL_BYTES     = 50 * 1024 * 1024   # 프리셋 전체 50MB


def _store_icon_bytes(content: bytes) -> dict:
    """이미지 바이트를 검증·재인코딩·저장하고 library 항목을 반환.
    동일 sha256 이 이미 보관함에 있으면 재사용(중복 저장 방지)."""
    if len(content) > MARKET_MAX_ICON_BYTES:
        raise HTTPException(status_code=400, detail="아이콘 이미지가 너무 큽니다 (최대 5MB)")
    fmt = _validate_image_bytes(content, {"PNG", "JPEG", "GIF"})
    sha = _sha256_bytes(content)
    library = load_library()
    for a in library:
        if a.get("sha256") == sha and (CUSTOM_ICONS_DIR / a.get("storage_filename", "")).exists():
            return a  # 이미 있음 → 재사용
    is_gif = (fmt == "GIF")
    unique_name = f"{uuid.uuid4().hex}{'.gif' if is_gif else '.png'}"
    save_path = CUSTOM_ICONS_DIR / unique_name
    if not _is_within(CUSTOM_ICONS_DIR, save_path):
        raise HTTPException(status_code=400, detail="잘못된 저장 경로")
    if is_gif:
        with open(save_path, 'wb') as f:
            f.write(content)
    else:
        img = Image.open(BytesIO(content)).convert('RGBA')
        ow, oh = img.size
        m = max(ow, oh)
        if m > 1024:
            r = 1024 / m
            img = img.resize((int(ow * r), int(oh * r)), Image.Resampling.LANCZOS)
        img.save(save_path, 'PNG')
    entry = {
        "asset_id":         str(uuid.uuid4()),
        "display_name":     "market",
        "storage_filename": unique_name,
        "local_image_path": str(save_path),
        "origin":           "market-download",
        "pack_id":          None,
        "sha256":           sha,
        "created_at":       _now_iso(),
        "updated_at":       _now_iso(),
    }
    library.append(entry)
    save_library(library)
    return entry


def _store_wallpaper_bytes(content: bytes) -> str:
    """배경 바이트를 검증·재인코딩·저장하고 로컬 절대경로를 반환."""
    if len(content) > MARKET_MAX_WALLPAPER_BYTES:
        raise HTTPException(status_code=400, detail="배경 이미지가 너무 큽니다 (최대 15MB)")
    fmt = _validate_image_bytes(content, {"PNG", "JPEG", "GIF"})
    is_gif = (fmt == "GIF")
    unique = f"{uuid.uuid4().hex}{'.gif' if is_gif else '.png'}"
    save_path = WALLPAPERS_DIR / unique
    if not _is_within(WALLPAPERS_DIR, save_path):
        raise HTTPException(status_code=400, detail="잘못된 저장 경로")
    if is_gif:
        with open(save_path, 'wb') as f:
            f.write(content)
    else:
        Image.open(BytesIO(content)).convert('RGB').save(save_path, 'PNG')
    return str(save_path)


@app.post("/api/market/import")
async def import_market_preset(
    manifest: str = Form(...),
    files: list[UploadFile] = File(default=[]),
):
    """다운로드한 마켓 프리셋을 내 보관함에 저장한다.

    보안 원칙:
    - 모든 이미지를 서버측에서 재검증 + 재인코딩(EXIF/은닉 페이로드 제거).
    - target_path(실행 매핑)는 절대 저장하지 않음 → 다운로드 프리셋엔 실행 연결이 없다.
      (프로그램 연결은 사용자가 자기 PC에서 직접)
    - 원본 파일명/절대경로 미사용, 저장 파일명은 UUID.
    - 아이콘 개수·개별/전체 용량 상한.

    manifest(JSON):
      { name, canvas:{w,h}, wallpaper_key?, icons:[{file_key, x,y,size,show_name, font_*...}] }
    files: 각 UploadFile.filename == manifest 의 file_key / wallpaper_key
    """
    try:
        m = json.loads(manifest)
    except Exception:
        raise HTTPException(status_code=400, detail="manifest 파싱 실패")
    if not isinstance(m, dict):
        raise HTTPException(status_code=400, detail="manifest 형식 오류")

    name = (str(m.get("name") or "다운로드한 프리셋")).strip()[:60] or "다운로드한 프리셋"
    canvas = m.get("canvas") or {}
    icons_meta = m.get("icons") or []
    if not isinstance(icons_meta, list):
        raise HTTPException(status_code=400, detail="icons 형식 오류")
    if len(icons_meta) > MARKET_MAX_ICONS:
        raise HTTPException(status_code=400, detail=f"아이콘 개수 초과 (최대 {MARKET_MAX_ICONS})")

    # 업로드 파일을 filename(key) 로 매핑 + 총용량 검사
    file_map: dict[str, bytes] = {}
    total = 0
    for uf in files:
        content = await uf.read()
        total += len(content)
        if total > MARKET_MAX_TOTAL_BYTES:
            raise HTTPException(status_code=400, detail="전체 용량 초과 (최대 50MB)")
        file_map[uf.filename] = content

    # 배경 (선택)
    wallpaper_path = ""
    wp_key = m.get("wallpaper_key")
    if wp_key:
        if wp_key not in file_map:
            raise HTTPException(status_code=400, detail="배경 파일이 누락되었습니다")
        wallpaper_path = _store_wallpaper_bytes(file_map[wp_key])

    # 아이콘
    icon_models: list[PresetIconModel] = []
    for ic in icons_meta:
        if not isinstance(ic, dict):
            continue
        fkey = ic.get("file_key")
        if not fkey or fkey not in file_map:
            raise HTTPException(status_code=400, detail="아이콘 파일이 누락되었습니다")
        entry = _store_icon_bytes(file_map[fkey])
        icon_models.append(PresetIconModel(
            asset_id      = entry["asset_id"],
            icon_name     = (str(ic.get("icon_name") or "")).strip()[:100],
            target_path   = "",                       # ★ 실행 매핑 제외 (강제)
            x             = float(ic.get("x") or 0),
            y             = float(ic.get("y") or 0),
            size          = float(ic.get("size") or 72),
            show_name     = bool(ic.get("show_name", True)),
            font_family   = str(ic.get("font_family") or "맑은 고딕"),
            font_size     = int(ic.get("font_size") or 10),
            font_bold     = bool(ic.get("font_bold", True)),
            font_italic   = bool(ic.get("font_italic", False)),
            font_color    = str(ic.get("font_color") or "#ffffff"),
            outline_color = str(ic.get("outline_color") or "#000000"),
        ))

    # 프리셋 생성 (id 는 서버가 발급)
    preset = PresetModel(
        name           = name,
        wallpaper_path = wallpaper_path,
        canvas         = CanvasModel(w=int(canvas.get("w", 1920)), h=int(canvas.get("h", 1080))),
        icons          = icon_models,
    )
    data = _model_dump(preset)
    data["id"] = str(uuid.uuid4())
    data["created_at"] = _now_iso()
    data["updated_at"] = _now_iso()
    presets = load_presets()
    presets.append(data)
    save_presets(presets)
    return {"success": True, "id": data["id"], "preset": _enrich_preset(data)}


# =============================================================================
# [Phase C] 배경화면 + 프리셋 전체 적용 (apply-local)
# =============================================================================

SPI_SETDESKWALLPAPER = 20
SPI_GETDESKWALLPAPER = 0x0073


def get_display_metrics() -> dict:
    """디스플레이 물리/논리 해상도 + DPI 배율.
    오버레이(Qt)는 아이콘을 '논리 좌표'로 배치하므로 스케일은 논리 해상도 기준."""
    phys_w, phys_h = 1920, 1080
    dpi = 96
    try:
        phys_w = int(ctypes.windll.user32.GetSystemMetrics(0)) or 1920
        phys_h = int(ctypes.windll.user32.GetSystemMetrics(1)) or 1080
    except Exception:
        pass
    try:
        dpi = int(ctypes.windll.user32.GetDpiForSystem()) or 96
    except Exception:
        dpi = 96
    scale = (dpi / 96.0) if dpi else 1.0
    log_w = int(round(phys_w / scale)) if scale else phys_w
    log_h = int(round(phys_h / scale)) if scale else phys_h
    return {"physical": [phys_w, phys_h], "logical": [log_w, log_h],
            "dpi": dpi, "scale": round(scale, 4)}


def get_screen_size():
    """오버레이가 사용하는 논리 해상도(px). 실패 시 1920x1080 폴백."""
    dm = get_display_metrics()
    lw, lh = dm["logical"]
    return (lw or 1920), (lh or 1080)


def get_current_wallpaper() -> str:
    """현재 배경화면 경로. SPI 우선, 실패 시 레지스트리 폴백."""
    val = ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 1024, buf, 0)
        val = buf.value or ""
    except Exception:
        val = ""
    if val and os.path.exists(val):
        return val
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop")
        v, _ = winreg.QueryValueEx(k, "WallPaper")
        winreg.CloseKey(k)
        if v and os.path.exists(v):
            return v
    except Exception:
        pass
    return val


def _ensure_fill_style():
    """배경화면 표시 방식을 '채우기(Fill)'로 — 편집기 object-cover 와 일치."""
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop",
                           0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k, "WallpaperStyle", 0, winreg.REG_SZ, "10")
        winreg.SetValueEx(k, "TileWallpaper",  0, winreg.REG_SZ, "0")
        winreg.CloseKey(k)
    except Exception as e:
        print(f"⚠️ 배경 표시방식 설정 실패: {e}")


def set_wallpaper(path: str) -> bool:
    try:
        _ensure_fill_style()  # 편집기(object-cover)와 크롭 일치
        res = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, str(path), 3)
        return bool(res)
    except Exception as e:
        print(f"❌ 배경화면 적용 실패: {e}")
        return False


def capture_original_wallpaper_once():
    """프리셋 적용 직전의 배경화면을 1회 저장(파일 복사). TranscodedWallpaper
    캐시 덮어쓰기 대비. 못 읽으면 저장 안 하고 다음 기회에 재시도."""
    try:
        if ORIGINAL_WALLPAPER_PATH.exists():
            return
        cur = get_current_wallpaper()
        if not cur or not os.path.exists(cur):
            print(f"⚠️ 원본 배경화면을 읽지 못함(스킵): '{cur}'")
            return
        import shutil
        ext = os.path.splitext(cur)[1] or ".jpg"
        backup_img = BACKUP_DIR / f"original_wallpaper{ext}"
        try:
            shutil.copy2(cur, backup_img)
            ORIGINAL_WALLPAPER_PATH.write_text(str(backup_img), encoding="utf-8")
            print(f"✅ 원본 배경화면 복사 저장: {cur} → {backup_img}")
        except Exception:
            ORIGINAL_WALLPAPER_PATH.write_text(cur, encoding="utf-8")
    except Exception as e:
        print(f"⚠️ 원본 배경화면 저장 실패: {e}")


def restore_original_wallpaper() -> str:
    """저장된 원본 배경화면으로 복원 후 마커 제거. 복원한 경로 반환('' 가능)."""
    try:
        if not ORIGINAL_WALLPAPER_PATH.exists():
            return ""
        orig = ORIGINAL_WALLPAPER_PATH.read_text(encoding="utf-8").strip()
        if orig and os.path.exists(orig):
            set_wallpaper(orig)
        ORIGINAL_WALLPAPER_PATH.unlink(missing_ok=True)
        return orig
    except Exception as e:
        print(f"⚠️ 원본 배경화면 복원 실패: {e}")
        return ""


def _restart_overlay() -> bool:
    """오버레이 종료 후 재시작 (reload-overlay 로직과 동일)."""
    import time
    kill_overlay_processes()
    time.sleep(0.4)
    script_path = ENGINE_DIR / "icon_overlay.py"
    if not script_path.exists():
        return False
    if sys.platform == "win32":
        subprocess.Popen([sys.executable, str(script_path)],
                         cwd=str(ENGINE_DIR), creationflags=CREATE_NO_WINDOW)
    else:
        subprocess.Popen([sys.executable, str(script_path)], cwd=str(ENGINE_DIR))
    return True


@app.get("/api/display/info")
async def get_display_info():
    """현재 디스플레이 물리/논리 해상도 + DPI 배율."""
    return get_display_metrics()


@app.post("/api/wallpaper/upload")
async def upload_wallpaper(file: UploadFile = File(...)):
    """배경화면 파일 업로드 → 엔진 로컬 저장 + 보관함(wallpaper_library.json) 기록.

    아이콘 업로드와 동일하게 sha256 중복 방지 + asset_id 발급을 수행한다.
    응답에 asset_id/storage_filename/display_name 을 추가하고, 기존 필드
    (success/wallpaper_path/url)는 하위호환을 위해 유지한다."""
    # 허용: PNG, JPG/JPEG, GIF (WEBP/BMP/SVG 차단 — 공격면 축소, 아이콘 업로드와 통일)
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ['.png', '.jpg', '.jpeg', '.gif']:
        raise HTTPException(status_code=400, detail="지원하지 않는 형식")
    content = await file.read()
    if len(content) > MAX_WALLPAPER_BYTES:
        raise HTTPException(status_code=400, detail="파일이 너무 큽니다 (최대 40MB)")
    _validate_image_bytes(content, {"PNG", "JPEG", "GIF"})
    sha = _sha256_bytes(content)

    # ── 중복 방지: 동일 sha256 이 이미 보관함에 있으면 재저장 없이 반환 ──
    library = _adopt_orphan_wallpapers()
    for a in library:
        if a.get("sha256") == sha and (WALLPAPERS_DIR / a.get("storage_filename", "")).exists():
            return {
                "success": True,
                "duplicate": True,
                "asset_id": a.get("asset_id"),
                "storage_filename": a.get("storage_filename"),
                "wallpaper_path": a.get("local_image_path"),          # 하위호환
                "display_name": a.get("display_name"),
                "url": f"/wallpapers/{a.get('storage_filename')}",
            }

    is_gif = (ext == '.gif')
    unique = f"{uuid.uuid4().hex}{'.gif' if is_gif else '.png'}"
    save_path = WALLPAPERS_DIR / unique
    if not _is_within(WALLPAPERS_DIR, save_path):
        raise HTTPException(status_code=400, detail="잘못된 저장 경로")

    width = height = None
    if is_gif:
        # GIF는 원본 유지 (애니메이션 배경)
        with open(save_path, 'wb') as f:
            f.write(content)
        try:
            with Image.open(save_path) as im:
                width, height = im.size
        except Exception:
            pass
    else:
        # JPG/PNG → PNG로 재인코딩 (메타데이터/페이로드 제거). 배경은 원본 해상도 유지.
        img = Image.open(BytesIO(content)).convert('RGB')
        width, height = img.size
        img.save(save_path, 'PNG')

    asset_id = str(uuid.uuid4())
    display_name = Path(file.filename or "").stem or "배경화면"
    entry = {
        "asset_id":         asset_id,
        "display_name":     display_name,
        "storage_filename": unique,
        "local_image_path": str(save_path),
        "origin":           "user-upload",
        "sha256":           sha,
        "width":            width,
        "height":           height,
        "created_at":       _now_iso(),
        "updated_at":       _now_iso(),
    }
    library.append(entry)
    save_wallpaper_library(library)

    return {
        "success": True,
        "duplicate": False,
        "asset_id": asset_id,
        "storage_filename": unique,
        "wallpaper_path": str(save_path),          # 하위호환
        "display_name": display_name,
        "url": f"/wallpapers/{unique}",
    }


# ── 배경화면 보관함 (wallpaper_library.json) ─────────────────────────────────
@app.get("/api/wallpapers/library")
async def get_wallpaper_library():
    """보관함 배경화면 목록. 실제 파일 존재 여부(file_exists)를 함께 반환.
    wallpapers 폴더의 미등록 파일은 asset_id를 부여해 흡수한다."""
    library = _adopt_orphan_wallpapers()
    for a in library:
        sf = a.get("storage_filename", "")
        a["file_exists"] = (WALLPAPERS_DIR / sf).exists()
        a["url"] = f"/wallpapers/{sf}" if sf else ""   # 프론트 썸네일용 (정적 마운트)
    return {"assets": library}


@app.patch("/api/wallpapers/library/{asset_id}")
async def update_wallpaper_asset(asset_id: str, data: LibraryPatchModel):
    """표시 이름(display_name)만 변경. 파일명/경로는 불변."""
    library = load_wallpaper_library()
    found = False
    for a in library:
        if a.get("asset_id") == asset_id:
            a["display_name"] = data.display_name
            a["updated_at"] = _now_iso()
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="보관함 배경화면을 찾을 수 없음")
    save_wallpaper_library(library)
    return {"success": True, "asset_id": asset_id, "display_name": data.display_name}


@app.delete("/api/wallpapers/library/{asset_id}")
async def delete_wallpaper_asset(asset_id: str, force: bool = False):
    """보관함 배경화면 삭제. 프리셋이 참조 중이면 409. force=true 로 강제 삭제.
    동일 파일(sha256/파일명)을 공유하는 다른 항목이 없을 때만 실제 파일을 지운다."""
    library = load_wallpaper_library()
    asset = next((a for a in library if a.get("asset_id") == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="보관함 배경화면을 찾을 수 없음")

    storage = asset.get("storage_filename", "")
    local_path = asset.get("local_image_path", "")
    # 이 배경을 쓰는 프리셋 조사 (wallpaper_path 로 참조)
    preset_refs = [
        p.get("id") for p in load_presets()
        if p.get("wallpaper_path") and (
            os.path.basename(p.get("wallpaper_path", "")) == storage
            or p.get("wallpaper_path") == local_path
        )
    ]
    if preset_refs and not force:
        return JSONResponse(
            status_code=409,
            content={"detail": "Wallpaper is still in use", "references": {"presets": preset_refs}},
        )

    library = [a for a in library if a.get("asset_id") != asset_id]
    still_shared = any(a.get("storage_filename") == storage for a in library)
    save_wallpaper_library(library)

    deleted_file = False
    if not still_shared and storage:
        try:
            fp = WALLPAPERS_DIR / storage
            if _is_within(WALLPAPERS_DIR, fp) and fp.exists():
                fp.unlink()
                deleted_file = True
        except Exception as e:
            print(f"⚠️ 배경 파일 삭제 실패: {e}")

    return {"success": True, "deleted_file": deleted_file, "forced": bool(preset_refs and force)}


class WallpaperApplyModel(BaseModel):
    wallpaper_path: str


@app.post("/api/wallpaper/apply")
async def apply_wallpaper(data: WallpaperApplyModel):
    # 심층 방어: 요청받은 경로가 반드시 wallpapers 폴더 안이어야 함
    if not _is_within(WALLPAPERS_DIR, Path(data.wallpaper_path)):
        raise HTTPException(status_code=400, detail="허용되지 않은 배경화면 경로")
    if not os.path.exists(data.wallpaper_path):
        raise HTTPException(status_code=404, detail="배경화면 파일 없음")
    if not set_wallpaper(data.wallpaper_path):
        raise HTTPException(status_code=500, detail="배경화면 적용 실패")
    return {"success": True}


@app.post("/api/presets/{preset_id}/apply-local")
async def apply_preset_local(preset_id: str):
    """저장된 프리셋을 원자적으로 적용. 실패 시 전체 롤백."""
    import shutil

    preset = next((x for x in load_presets() if x.get("id") == preset_id), None)
    if not preset:
        raise HTTPException(status_code=404, detail="프리셋을 찾을 수 없음")

    # 0. 최초 원본 배경화면 1회 저장 (끄기/종료 시 복원용)
    capture_original_wallpaper_once()

    # 1. 백업 (icons_config.json, settings.json, 현재 배경화면 경로)
    prev_wallpaper = get_current_wallpaper()
    backup = {}
    try:
        if ICON_CONFIG_PATH.exists():
            shutil.copy2(ICON_CONFIG_PATH, BACKUP_DIR / "icons_config.json.bak")
            backup["icons"] = True
        if SETTINGS_PATH.exists():
            shutil.copy2(SETTINGS_PATH, BACKUP_DIR / "settings.json.bak")
            backup["settings"] = True
        (BACKUP_DIR / "wallpaper.txt").write_text(prev_wallpaper or "", encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"백업 실패: {e}")

    def _rollback():
        try:
            if backup.get("icons"):
                shutil.copy2(BACKUP_DIR / "icons_config.json.bak", ICON_CONFIG_PATH)
            if backup.get("settings"):
                shutil.copy2(BACKUP_DIR / "settings.json.bak", SETTINGS_PATH)
            if prev_wallpaper:
                set_wallpaper(prev_wallpaper)
        except Exception as e:
            print(f"⚠️ 롤백 실패: {e}")

    try:
        # 2. asset_id → local_image_path 해석 + 파일 검증
        library = {a.get("asset_id"): a for a in load_library()}
        canvas = preset.get("canvas") or {}
        cw = canvas.get("w") or 1920
        ch = canvas.get("h") or 1080
        dm = get_display_metrics()  # 참고용(디버그/응답). 좌표 매핑엔 사용하지 않음.
        # ★ 좌표는 원본 캔버스 좌표 그대로 기록한다. canvas→화면 cover 매핑은
        #   오버레이(Qt)가 '실제 화면 지오메트리' 기준으로 수행한다.
        #   (백엔드 ctypes DPI 추정이 Qt 실제 배율과 어긋나 드리프트가 났었음)
        new_mappings = []
        warnings = []
        for ic in preset.get("icons", []):
            asset = library.get(ic.get("asset_id"))
            image_path = asset.get("local_image_path") if asset else ""
            # 심층 방어: 저장된 경로가 custom_icons 폴더 안인지 검증 (library.json 변조 대비)
            if not image_path or not _is_within(CUSTOM_ICONS_DIR, Path(image_path)) or not os.path.exists(image_path):
                raise HTTPException(
                    status_code=400,
                    detail=f"아이콘 이미지 파일 없음: {ic.get('icon_name') or ic.get('asset_id')}",
                )
            tp = ic.get("target_path", "")
            if tp and not os.path.exists(tp):
                warnings.append(f"연결 대상 없음: {tp}")
            new_mappings.append({
                "id":               str(uuid.uuid4()),
                "name":             ic.get("icon_name", ""),
                "image_path":       image_path,
                "target_path":      tp,
                "x":                int(round(float(ic.get("x", 0)))),
                "y":                int(round(float(ic.get("y", 0)))),
                "size":             int(round(float(ic.get("size", 72)))),
                "canvas_w":         int(cw),
                "canvas_h":         int(ch),
                "hover_image_path": ic.get("hover_image_path", ""),
                "show_name":        ic.get("show_name", True),
                "font_family":      ic.get("font_family", "맑은 고딕"),
                "font_size":        ic.get("font_size", 10),
                "font_bold":        ic.get("font_bold", True),
                "font_italic":      ic.get("font_italic", False),
                "font_color":       ic.get("font_color", "#ffffff"),
                "outline_color":    ic.get("outline_color", "#000000"),
            })

        # 3. 매핑 일괄 교체
        _save_json(ICON_CONFIG_PATH, new_mappings)

        # [진단] 좌표 매핑 결과를 파일로 남김 (드리프트 원인 추적용)
        try:
            _save_json(ENGINE_DIR / ".apply_debug.json", {
                "display_metrics": dm,
                "canvas": [cw, ch],
                "note": "coords are raw canvas; overlay maps to Qt screen",
                "icons": [{"name": m["name"], "x": m["x"], "y": m["y"], "size": m["size"]}
                          for m in new_mappings[:8]],
            })
        except Exception:
            pass

        # 4. settings 저장
        settings = load_settings()
        settings.update(preset.get("settings") or {})
        save_settings(settings)

        # 5. 배경화면 적용
        wp = preset.get("wallpaper_path", "")
        if wp:
            if not _is_within(WALLPAPERS_DIR, Path(wp)) or not os.path.exists(wp):
                raise HTTPException(status_code=400, detail=f"배경화면 경로가 유효하지 않음: {wp}")
            if not set_wallpaper(wp):
                raise HTTPException(status_code=500, detail="배경화면 적용 실패")

        # 6. Windows 기본 아이콘 숨김
        set_desktop_icons_visible(False)

        # 7. 오버레이 재시작
        _restart_overlay()

        # 활성 배경화면 + 활성 프리셋 id 기록
        try:
            ACTIVE_WALLPAPER_PATH.write_text(wp or "", encoding="utf-8")
            ACTIVE_PRESET_PATH.write_text(preset_id, encoding="utf-8")
        except Exception:
            pass

        return {
            "success": True,
            "preset_id": preset_id,
            "applied_icons": len(new_mappings),
            "display": {"logical": dm["logical"], "physical": dm["physical"],
                        "dpi": dm["dpi"], "dpi_scale": dm["scale"]},
            "warnings": warnings,
        }
    except HTTPException:
        _rollback()
        raise
    except Exception as e:
        _rollback()
        raise HTTPException(status_code=500, detail=f"적용 실패(롤백됨): {e}")


@app.post("/api/overlay/deactivate")
async def deactivate_overlay():
    """프리셋 끄기 — 오버레이 종료 + 기본 아이콘 복원 + 원본 배경화면 복원."""
    killed = kill_overlay_processes()
    shown = set_desktop_icons_visible(True)
    restored = restore_original_wallpaper()
    try:
        ACTIVE_WALLPAPER_PATH.unlink(missing_ok=True)
        ACTIVE_PRESET_PATH.unlink(missing_ok=True)
    except Exception:
        pass
    return {
        "success": True,
        "killed": killed,
        "desktop_icons_restored": bool(shown),
        "wallpaper_restored_to": restored,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
