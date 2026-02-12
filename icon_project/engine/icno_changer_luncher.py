"""
desktop_launcher.py (v3.1 - Code Review)

PySide6와 pywin32를 사용한 커스텀 바탕화면 아이콘 런처입니다.

이 어플리케이션은 Windows의 기본 바탕화면 아이콘을 대체하는 것을 목표로 합니다.
사용자의 바탕화면에 있는 모든 항목(파일, 폴더, .lnk)을 자동으로 스캔하여,
GIF 및 이미지로 커스터마이징 가능한 아이콘을 생성합니다.

주요 기능:
- 첫 실행 시 바탕화면의 '모든 항목' 자동 스캔 및 config 생성
- 아이콘(위젯) 드래그 앤 드롭으로 위치 이동 및 저장
- 아이콘 더블 클릭으로 모든 파일/폴더/프로그램 열기 (os.startfile)
- 아이콘 우클릭 시 '네이티브 기능' (관리자 실행, 속성 등) 재현 메뉴
- 아이콘 우클릭으로 개별 아이콘 이미지 변경 및 삭제
- 모든 설정은 .json 파일을 통해 영구 저장됩니다.

아키텍처 (Model-View-Controller 패턴):
- Model: ConfigManager (설정 관리), DesktopScanner (데이터 스캔 로직)
- View: DraggableIcon (사용자에게 보여지는 아이콘 창)
- Controller: AppManager (모델과 뷰를 총괄하고 비즈니스 로직을 처리)
"""

# --- 1. 표준 라이브러리 임포트 ---
import sys
import os
import json
import subprocess
import glob 
from typing import Dict, Optional, List  # 타입 힌팅을 위한 임포트

# --- 2. 서드파티 라이브러리 임포트 (Third-party) ---
try:
    # Windows API를 직접 호출하기 위한 라이브러리
    import win32api
    # .lnk 파일 분석 및 'SpecialFolders' 접근을 위한 COM 객체
    import win32com.client  # 'Dispatch' (WScript.Shell 생성)을 위해 필요
    # '속성' 창 호출 등 Windows Shell 기능을 위해 필요
    from win32com.shell import shell, shellcon
except ImportError:
    # 프로그램의 핵심 의존성이므로, 없으면 즉시 종료
    print("="*50)
    print("오류: 'pywin32' 라이브러리가 설치되지 않았습니다.")
    print("터미널에 [ pip install pywin32 ]를 입력하여 설치해주세요.")
    print("="*50)
    sys.exit(1)

# --- 3. Qt (PySide6) 라이브러리 임포트 ---
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QMenu, QFileDialog
)
from PySide6.QtGui import QMovie, QPixmap, QMouseEvent, QAction, QIcon
from PySide6.QtCore import Qt, QPoint, QRect, QSize

# --- 4. 전역 상수 (Global Constants) ---
# 하드코딩된 값을 상수로 분리하면, 향후 유지보수가 매우 용이합니다.
SAVE_FILE = "icons_config.json"  # 아이콘 설정 저장 경로
DEFAULT_ICON = "resourse/dun.png"        # 기본 아이콘 이미지 (스캔 시, 아이콘 변경 실패 시 사용)
ICON_WIDTH = 100                 # 아이콘 가로 크기
ICON_HEIGHT = 100                # 아이콘 세로 크기
GRID_SPACING = 10                # 스캔 시 아이콘 간 격자 간격
SCREEN_WIDTH_LIMIT = 1500        # 스캔 시 자동 줄바꿈 기준 너비 (실제 모니터 너비로 대체 가능)

# =============================================================================
# --- 5. Model (모델): 설정 파일 관리 ---
# =============================================================================

class ConfigManager:
    """
    Model (Persistence Layer - 영속성 계층).
    
    'icons_config.json' 파일의 읽기(load), 쓰기(save), 수정(update)을
    전담하는 클래스입니다. (단일 책임 원칙)
    
    이 클래스는 '어떻게' 스캔하는지, '무엇을' 보여주는지 알 필요가 없습니다.
    오직 파일 I/O 책임만 집니다.
    """
    
    def __init__(self, filepath: str):
        """
        ConfigManager를 초기화합니다.

        :param filepath: 저장할 JSON 설정 파일의 경로
        """
        self.filepath = filepath
        # config_data: { "icon_id": { "image_path": "...", "program_path": "...", ... } }
        self.config_data: Dict[str, Dict] = {}

    def load(self) -> bool:
        """
        설정 파일을 읽어 메모리(self.config_data)에 로드합니다.

        :return: 로드 성공 시 True, 파일이 없거나 오류 발생 시 False
        """
        if not os.path.exists(self.filepath):
            print(f"정보: 설정 파일 '{self.filepath}'이(가) 존재하지 않습니다.")
            return False  # 파일이 없는 것은 오류가 아니라 '첫 실행' 신호
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            print(f"정보: 기존 설정 파일 '{self.filepath}'을(를) 로드했습니다.")
            return True
        except json.JSONDecodeError as e:
            # JSON 파일이 손상되었을 경우
            print(f"오류: 설정 파일 읽기 실패 (JSON 파싱 오류): {e}")
            return False
        except Exception as e:
            print(f"오류: 설정 파일 읽기 실패 (알 수 없는 오류): {e}")
            return False

    def save(self):
        """현재 메모리의 config_data를 JSON 파일로 즉시 저장합니다."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                # indent=4: 가독성을 위해 4칸 들여쓰기
                # ensure_ascii=False: 한글 경로가 깨지지 않도록 함
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"오류: 설정 파일 저장 실패 (I/O 오류): {e}")
        except Exception as e:
            print(f"오류: 설정 파일 저장 실패 (알 수 없는 오류): {e}")

    def get_all_data(self) -> Dict[str, Dict]:
        """모든 아이콘 설정 데이터를 반환합니다."""
        return self.config_data

    def set_all_data(self, data: Dict[str, Dict]):
        """설정 데이터 전체를 교체합니다 (예: 스캔 직후)."""
        self.config_data = data

    def update_position(self, icon_id: str, pos: QPoint):
        """
        특정 아이콘의 위치(pos_x, pos_y)를 업데이트하고 즉시 저장합니다.
        (이벤트 기반으로 실시간 저장)
        
        :param icon_id: 수정할 아이콘의 고유 ID (e.g., 'Chrome')
        :param pos: PySide6의 QPoint 객체
        """
        if icon_id in self.config_data:
            self.config_data[icon_id]["pos_x"] = pos.x()
            self.config_data[icon_id]["pos_y"] = pos.y()
            self.save()

    def update_data(self, icon_id: str, key: str, value: str):
        """
        특정 아이콘의 데이터(image_path, program_path)를 업데이트하고 즉시 저장합니다.

        :param icon_id: 수정할 아이콘의 고유 ID
        :param key: 수정할 설정 키 (e.g., 'image_path')
        :param value: 새로운 값
        """
        if icon_id in self.config_data:
            self.config_data[icon_id][key] = value
            self.save()

    def remove(self, icon_id: str):
        """특정 아이콘을 설정에서 제거하고 즉시 저장합니다."""
        if icon_id in self.config_data:
            del self.config_data[icon_id]
            self.save()

# =============================================================================
# --- 6. Model (모델): 바탕화면 스캐너 ---
# =============================================================================

class DesktopScanner:
    """
    Model (Business Logic Layer - 비즈니스 로직 계층).
    
    Windows 바탕화면을 스캔하고, .lnk 파일의 경로를 분석하는
    모든 'Windows 종속적' 로직을 전담하는 클래스입니다. (단일 책임 원칙)
    """
    
    def __init__(self):
        """
        스캐너를 초기화하고, 핵심 도구인 WScript.Shell 객체를 생성합니다.
        이 객체는 COM을 사용하므로 생성 비용이 비싸, 한 번만 생성해 재사용합니다.
        """
        try:
            self.wscript_shell = win32com.client.Dispatch("WScript.Shell")
        except Exception as e:
            print(f"치명적 오류: WScript.Shell 객체 생성 실패: {e}")
            print("바탕화면 스캔 및 .lnk 분석 기능이 작동하지 않습니다.")
            self.wscript_shell = None

    def resolve_lnk(self, lnk_path: str) -> Optional[str]:
        """
        (pywin32) .lnk(바로 가기) 파일의 실제 대상 프로그램 경로를 반환합니다.

        :param lnk_path: 분석할 .lnk 파일의 전체 경로
        :return: 대상 프로그램 경로(str) 또는 실패 시 None
        """
        if not self.wscript_shell:
            return None
        try:
            shortcut = self.wscript_shell.CreateShortCut(lnk_path)
            # .TargetPath가 비어있는 경우(예: '내 PC')를 대비해 확인
            if shortcut.TargetPath:
                return shortcut.TargetPath
            else:
                return None
        except Exception as e:
            # COM 오류는 매우 다양하게 발생할 수 있으므로 포괄적으로 처리
            print(f"정보: .lnk 파일 분석 오류 ({lnk_path}): {e}")
            return None
            
    def _get_desktop_paths(self) -> List[str]:
        """
        현재 사용자의 바탕화면 폴더와 공용 바탕화면 폴더 경로를
        리스트로 반환합니다.

        :return: 바탕화면 폴더 경로들의 리스트
        """
        paths = []
        if not self.wscript_shell:
            return paths
            
        try:
            # 'SpecialFolders'는 Windows의 특수 폴더 경로를 안전하게 가져옵니다.
            user_desktop = self.wscript_shell.SpecialFolders("Desktop")
            paths.append(user_desktop)
        except Exception:
            # WScript가 실패할 경우, 환경 변수를 이용한 폴백(Fallback)
            paths.append(os.path.join(os.path.expanduser('~'), 'Desktop'))
            
        try:
            public_desktop = self.wscript_shell.SpecialFolders("AllUsersDesktop")
            paths.append(public_desktop)
        except Exception:
            paths.append(os.path.join(os.environ.get('PUBLIC', 'C:\\Users\\Public'), 'Desktop'))
            
        # 존재하는 디렉토리만 필터링하여 반환
        return [path for path in paths if os.path.isdir(path)]

    def scan_desktop_items(self) -> Dict[str, Dict]:
        """
        (핵심 기능)
        바탕화면의 '모든 항목'(파일, 폴더, .lnk)을 스캔하여
        config 딕셔너리를 생성해 반환합니다.
        아이콘들은 격자(Grid) 형태로 자동 배치됩니다.

        :return: 'ConfigManager'가 사용할 수 있는 아이콘 설정 딕셔너리
        """
        if not self.wscript_shell:
            return {}
            
        new_config_data: Dict[str, Dict] = {}
        desktop_paths = self._get_desktop_paths()
        print(f"정보: 스캔 중인 경로: {desktop_paths}")

        # 격자 배치를 위한 변수
        pos_x, pos_y = GRID_SPACING, GRID_SPACING
        # 중복 스캔 방지 (예: 공용 바탕화면과 개인 바탕화면에 동일한 .lnk가 있을 때)
        scanned_files: set[str] = set()

        for path in desktop_paths:
            # glob(os.path.join(path, "*")): 해당 폴더의 모든 항목(파일/폴더)을 가져옴
            all_item_paths = glob.glob(os.path.join(path, "*"))
            
            for item_path in all_item_paths:
                file_name = os.path.basename(item_path)
                
                # 1. 시스템 파일 필터링 (e.g., 'desktop.ini')
                if file_name.lower() == 'desktop.ini':
                    continue
                
                # 2. 중복 아이템 필터링
                if file_name in scanned_files:
                    continue
                scanned_files.add(file_name)
                
                # 3. 고유 ID 및 대상 경로 결정
                # (참고) ID를 파일명/폴더명 자체로 사용 (더 안전함)
                icon_id = file_name
                target_path_to_store = None

                # 4. 분기: 바로가기(.lnk)인가? 일반 파일/폴더인가?
                if file_name.lower().endswith(".lnk"):
                    # 바로가기(.lnk)인 경우: 대상 경로를 분석
                    target_path_to_store = self.resolve_lnk(item_path)
                else:
                    # 일반 파일/폴더인 경우: 항목 자체를 경로로 지정
                    target_path_to_store = item_path

                # 5. 유효한 대상만 config에 추가
                if not target_path_to_store:
                    print(f"정보: 스킵: '{file_name}' (대상이 없는 바로가기 또는 분석 실패)")
                    continue

                # 6. 새 설정 데이터 생성
                new_config_data[icon_id] = {
                    "image_path": DEFAULT_ICON,       # 스캔 시에는 모두 기본 아이콘
                    "program_path": target_path_to_store, # 실제 열릴 경로
                    "pos_x": pos_x,                   # 격자 X 위치
                    "pos_y": pos_y                    # 격자 Y 위치
                }
                
                # 7. 다음 아이콘 위치를 격자 형태로 계산
                pos_x += (ICON_WIDTH + GRID_SPACING)
                if pos_x > SCREEN_WIDTH_LIMIT: # 화면 너비를 넘어가면
                    pos_x = GRID_SPACING       # 다음 줄 맨 앞으로
                    pos_y += (ICON_HEIGHT + GRID_SPACING)

        print(f"정보: 총 {len(new_config_data)}개의 항목(파일/폴더/바로가기)을 스캔했습니다.")
        return new_config_data

# =============================================================================
# --- 7. 뷰 (View): 드래그 가능한 아이콘 ---
# =============================================================================

class DraggableIcon(QWidget):
    """
    View (UI Layer - UI 계층).
    
    사용자에게 보여지는 아이콘 '창' 그 자체입니다.
    이 클래스는 QWidget을 상속받아, 테두리 없는 투명한 창으로 작동합니다.
    
    모든 '로직' 처리는 Controller (AppManager)에게 위임(delegate)합니다.
    (예: '실행해줘', '위치 저장해줘')
    """
    
    def __init__(self, controller: 'AppManager', icon_id: str, 
                 image_path: str, program_path: str, pos: QPoint):
        """
        DraggableIcon 위젯(창)을 초기화합니다.

        :param controller: 자신을 관리하는 AppManager(컨트롤러) 객체
        :param icon_id: 이 아이콘의 고유 ID (e.g., 'Chrome.lnk')
        :param image_path: 표시할 이미지/GIF의 경로
        :param program_path: 더블 클릭 시 실행할 프로그램의 경로
        :param pos: 아이콘이 표시될 화면 상의 위치 (QPoint)
        """
        super().__init__()
        # 'controller'는 이 뷰가 상호작용해야 할 상위 관리자입니다.
        self.controller = controller 
        self.icon_id = icon_id
        
        self.dragging = False  # 현재 드래그 중인지 여부
        self.offset = QPoint() # 드래그 시작 시 마우스와 창 좌상단의 차이

        self.image_path = image_path
        self.program_path = program_path

        # --- 1. 윈도우 스타일 설정 ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |    # 테두리 없는 창
            Qt.WindowType.WindowStaysOnTopHint |   # 항상 위에 표시 (바탕화면 대체)
            Qt.WindowType.Tool                     # 작업 표시줄에 아이콘 숨기기
        )
        # 창 배경을 투명하게 설정 (필수)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # --- 2. 내용물 (QLabel) 설정 ---
        # QWidget 자체는 이미지를 표시할 수 없으므로,
        # QLabel을 자식으로 두어 이미지를 표시합니다.
        self.label = QLabel(self)
        self.label.setScaledContents(True) # 이미지를 라벨 크기에 맞춤

        # --- 3. 위젯 속성 설정 ---
        self.set_icon(image_path) # 이미지/GIF 로드
        self.setFixedSize(ICON_WIDTH, ICON_HEIGHT)
        self.label.setFixedSize(ICON_WIDTH, ICON_HEIGHT)
        self.move(pos) # 컨트롤러가 지정한 위치로 이동
        self.update_tooltip()
        self.show()

    def set_icon(self, image_path: str):
        """(View) 아이콘의 이미지를 설정합니다 (GIF/일반 이미지 자동 감지)."""
        self.image_path = image_path
        
        # 기존에 재생 중인 QMovie(GIF)가 있다면 정지
        if hasattr(self, 'movie') and self.movie:
            self.movie.stop()

        # 이미지가 존재하지 않으면, 기본 아이콘(dun.png)으로 대체
        if not os.path.exists(image_path):
            image_path = DEFAULT_ICON
            self.image_path = DEFAULT_ICON
            # 기본 아이콘조차 없으면 아무것도 하지 않음
            if not os.path.exists(DEFAULT_ICON): 
                print(f"치명적 오류: 기본 아이콘 '{DEFAULT_ICON}'조차 없습니다.")
                return

        # GIF 파일인 경우
        if image_path.lower().endswith('.gif'):
            self.movie = QMovie(image_path)
            self.movie.setScaledSize(QSize(ICON_WIDTH, ICON_HEIGHT))
            self.label.setMovie(self.movie)
            self.movie.start()
        # 일반 이미지(PNG, JPG)인 경우
        else:
            pixmap = QPixmap(image_path)
            self.label.setPixmap(pixmap)
            self.movie = None # GIF가 아님을 명시
            
    def update_tooltip(self):
        """(View) 프로그램 경로에 맞춰 마우스 오버 툴팁을 업데이트합니다."""
        if self.program_path:
            self.setToolTip(f"열기: {os.path.basename(self.program_path)}")
        else:
            self.setToolTip("연결된 파일/프로그램 없음 (우클릭 > 연결)")

    # --- 1. Qt 마우스 이벤트 핸들러 (Overrides) ---

    def mousePressEvent(self, event: QMouseEvent):
        """(Qt Override) 마우스 왼쪽 버튼을 누르면 '드래그 시작' 상태로 변경합니다."""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            # 창의 좌상단으로부터 마우스 커서의 상대 위치를 기억
            self.offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.raise_() # 드래그 시 다른 아이콘보다 위에 표시

    def mouseMoveEvent(self, event: QMouseEvent):
        """(Qt Override) 마우스를 누른 채 움직이면 창을 이동시킵니다."""
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.offset)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """(Qt Override) 마우스 버튼을 떼면 '드래그 종료' 상태로 변경하고,
        컨트롤러에게 위치 저장을 요청합니다.
        """
        if event.button() == Qt.LeftButton:
            self.dragging = False
            # (Controller에 위임) 위치 변경 사항을 컨트롤러에 알림
            self.controller.update_icon_position(self.icon_id, self.pos())

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """(Qt Override) 더블 클릭 시 컨트롤러에게 프로그램 실행을 요청합니다."""
        if event.button() == Qt.LeftButton:
            # (Controller에 위임) 프로그램 실행을 컨트롤러에 요청
            self.controller.request_run_program(self.program_path)

    def contextMenuEvent(self, event: QMouseEvent):
        """(Qt Override) 우클릭 시 '네이티브 재현' 컨텍스트 메뉴를 생성합니다."""
        menu = QMenu(self)
        
        # 프로그램 경로가 유효한 경우에만 '열기', '속성' 등을 활성화
        has_valid_path = bool(self.program_path and os.path.exists(self.program_path))

        # --- 1. 네이티브 기능 (Controller에 위임) ---
        open_action = QAction("열기 (Open)", self)
        # triggered.connect에 lambda를 사용하여, '요청 시점'에 컨트롤러 함수가 호출되도록 함
        open_action.triggered.connect(lambda: self.controller.request_run_program(self.program_path))
        open_action.setEnabled(has_valid_path)
        menu.addAction(open_action)

        admin_action = QAction("관리자 권한으로 실행", self)
        admin_action.triggered.connect(lambda: self.controller.request_run_admin(self.program_path))
        admin_action.setEnabled(has_valid_path)
        menu.addAction(admin_action)
        
        menu.addSeparator()

        loc_action = QAction("파일 위치 열기", self)
        loc_action.triggered.connect(lambda: self.controller.request_open_location(self.program_path))
        loc_action.setEnabled(has_valid_path)
        menu.addAction(loc_action)
        
        prop_action = QAction("속성", self)
        prop_action.triggered.connect(lambda: self.controller.request_show_properties(self.program_path))
        prop_action.setEnabled(has_valid_path)
        menu.addAction(prop_action)
        
        # --- 2. 런처 고유 기능 ---
        menu.addSeparator()

        link_action = QAction("파일/프로그램 연결...", self)
        link_action.triggered.connect(self.link_program) # 이 뷰가 직접 처리
        menu.addAction(link_action)

        change_icon_action = QAction("아이콘 변경하기...", self)
        change_icon_action.triggered.connect(self.change_icon) # 이 뷰가 직접 처리
        menu.addAction(change_icon_action)

        menu.addSeparator()

        delete_action = QAction("이 아이콘 삭제하기", self)
        delete_action.triggered.connect(self.delete_icon) # 이 뷰가 직접 처리
        menu.addAction(delete_action)
        
        # --- 3. 어플리케이션 제어 ---
        menu.addSeparator()
        
        quit_action = QAction("모든 런처 종료", self)
        quit_action.triggered.connect(self.controller.quit_app) # 컨트롤러에 종료 요청
        menu.addAction(quit_action)

        menu.exec(event.globalPos()) # 현재 마우스 커서 위치에 메뉴 표시

    # --- 2. 메뉴 기능 (Controller와 상호작용) ---

    def link_program(self):
        """(View) '파일/프로그램 연결' 파일 대화상자를 엽니다.
        선택된 파일 경로는 컨트롤러에게 전달합니다.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "연결할 파일, 프로그램, 폴더 선택", "", 
            "모든 파일 (*.*)" # 모든 항목을 연결할 수 있도록 함
        )
        if not file_path:
            return  # 사용자가 '취소'를 누름

        # (Controller에 위임) .lnk 분석 및 경로 저장을 컨트롤러에 요청
        self.controller.link_program_to_icon(self.icon_id, file_path)
            
    def change_icon(self):
        """(View) '아이콘 변경' 파일 대화상자를 엽니다.
        선택된 이미지 경로는 컨트롤러에게 전달하고, 스스로의 모습도 변경합니다.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "아이콘 이미지 선택", "", 
            "이미지 파일 (*.png *.jpg *.jpeg *.gif);;모든 파일 (*.*)"
        )
        if file_path:
            # (Controller에 위임) 아이콘 경로 저장을 컨트롤러에 요청
            self.controller.update_icon_data(self.icon_id, "image_path", file_path)
            # (View) 스스로의 모습을 변경
            self.set_icon(file_path)

    def delete_icon(self):
        """(View) 아이콘 삭제를 컨트롤러에 요청하고 스스로를 닫습니다."""
        self.controller.remove_icon(self.icon_id)
        self.close() # 위젯(창) 닫기

    def update_linked_program(self, new_path: str):
        """(Controller가 호출) 링크가 변경되었으니 툴팁 등을 업데이트합니다."""
        self.program_path = new_path
        self.update_tooltip()

# =============================================================================
# --- 8. 컨트롤러 (Controller): 어플리케이션 관리자 ---
# =============================================================================

class AppManager:
    """
    Controller (Application Layer - 어플리케이션 계층).
    
    어플리케이션의 메인 컨트롤러 (지휘자)입니다.
    모든 객체(Model, View)를 소유하고, 모델과 뷰 사이의 상호작용을 지휘합니다.
    (예: View가 '실행'을 요청하면, Controller가 받아서 '실행' 로직을 수행)
    """
    
    def __init__(self, app: QApplication):
        """
        AppManager를 초기화합니다.

        :param app: PySide6의 QApplication 객체
        """
        self.app = app
        # 트레이 아이콘이 없으므로, 마지막 아이콘 창이 닫혀도
        # 프로그램이 종료되지 않도록 설정해야 합니다. (필수)
        self.app.setQuitOnLastWindowClosed(False)
        
        # --- Model 소유 ---
        # 컨트롤러는 모델 객체들의 인스턴스를 소유합니다.
        self.config = ConfigManager(SAVE_FILE)
        self.scanner = DesktopScanner()
        
        # --- View 관리 ---
        # {icon_id: DraggableIcon_widget} 형식으로 뷰 객체들을 관리
        self.icon_windows: Dict[str, DraggableIcon] = {}

    def start(self):
        """어플리케이션을 시작합니다 (메인 로직)."""
        
        # 1. 설정 파일 로드를 시도
        if not self.config.load():
            # 2. 실패 시 (첫 실행), 바탕화면 스캔
            print(f"정보: 설정 파일 '{SAVE_FILE}' 없음. 바탕화면 스캔을 시작합니다...")
            scanned_data = self.scanner.scan_desktop_items() # '모든 항목' 스캔
            self.config.set_all_data(scanned_data)
            self.config.save() # 스캔 결과를 즉시 저장
        
        # 3. 로드된/스캔된 설정을 기반으로 아이콘(View) 생성
        self.create_windows_from_config()
        
        if not self.icon_windows:
            print("경고: 로드할 아이콘이 없습니다. (바탕화면에 파일/폴더가 없거나 설정이 비어있습니다)")
        print("정보: 바탕화면 런처가 실행되었습니다.")

    def create_windows_from_config(self):
        """현재 config 데이터 기준으로 모든 아이콘(View)을 생성합니다."""
        all_data = self.config.get_all_data()
        print(f"정보: 총 {len(all_data)}개의 아이콘을 로드합니다.")
        
        for icon_id, data in all_data.items():
            # 이미 생성된 뷰가 있다면 닫고 새로 생성 (설정 리로드 시 대비)
            if icon_id in self.icon_windows:
                self.icon_windows[icon_id].close()
                
            icon_widget = DraggableIcon(
                controller=self,  # 컨트롤러 자신을 뷰에 주입 (의존성 주입)
                icon_id=icon_id,
                image_path=data.get("image_path", DEFAULT_ICON),
                program_path=data.get("program_path", ""),
                pos=QPoint(data.get("pos_x", 10), data.get("pos_y", 10))
            )
            # 생성된 뷰(아이콘)를 관리 목록에 추가
            self.icon_windows[icon_id] = icon_widget
            
    def quit_app(self):
        """어플리케이션을 종료합니다."""
        print("정보: 런처를 종료합니다...")
        self.app.quit()

    # --- 1. View(DraggableIcon)가 호출하는 '업데이트' 인터페이스 ---

    def update_icon_position(self, icon_id: str, pos: QPoint):
        """(View 요청) 아이콘 위치를 모델(Config)에 저장합니다."""
        self.config.update_position(icon_id, pos)

    def update_icon_data(self, icon_id: str, key: str, value: str):
        """(View 요청) 아이콘 데이터를 모델(Config)에 저장합니다."""
        self.config.update_data(icon_id, key, value)

    def remove_icon(self, icon_id: str):
        """(View 요청) 아이콘을 모델(Config)과 컨트롤러(View 목록)에서 제거합니다."""
        self.config.remove(icon_id)
        if icon_id in self.icon_windows:
            del self.icon_windows[icon_id] # 뷰 관리 목록에서 제거

    def link_program_to_icon(self, icon_id: str, file_path: str):
        """(View 요청) .lnk 파일을 분석(Scanner)하고 모델(Config)에 저장합니다."""
        target_path = file_path
        
        # .lnk 파일인 경우, 스캐너에게 대상 경로 분석을 요청
        if file_path.lower().endswith(".lnk"):
            resolved_path = self.scanner.resolve_lnk(file_path)
            if resolved_path:
                target_path = resolved_path
            else:
                print(f"경고: .lnk 파일 대상 경로 읽기 실패. 원본 '{file_path}' 경로를 저장합니다.")
        
        # 1. 모델(Config) 업데이트
        self.update_icon_data(icon_id, "program_path", target_path)
        
        # 2. 뷰(Icon)에게 변경 사항 알림 (툴팁 업데이트 등)
        if icon_id in self.icon_windows:
            self.icon_windows[icon_id].update_linked_program(target_path)
        print(f"정보: 프로그램 연결됨: {target_path}")

    # --- 2. View(DraggableIcon)가 호출하는 'Windows API 로직' 인터페이스 ---
    #    (이 로직들은 View가 아닌 Controller가 수행하는 것이 올바른 설계입니다)

    def request_run_program(self, program_path: str):
        """
        (View 요청) 프로그램을 '열기'로 실행합니다. (os.startfile)
        .exe, .txt, .pdf, 폴더 등 Windows가 열 수 있는 모든 항목을 지원합니다.
        """
        if not program_path:
            print("오류: 연결된 파일이 없습니다. (우클릭 > 파일/프로그램 연결)")
            return
        if not os.path.exists(program_path):
             # os.path.exists는 파일과 폴더 모두에 작동합니다.
            print(f"오류: 파일 또는 폴더를 찾을 수 없습니다: {program_path}")
            return
        try:
            print(f"정보: 열기 (startfile): {program_path}")
            # (핵심) os.startfile: Windows 탐색기에서 파일을 더블 클릭하는 것과
            # 동일한 효과를 냅니다. (연결 프로그램 자동 실행)
            os.startfile(program_path)
        except Exception as e:
            print(f"오류: 파일 열기 실패: {e}")

    def request_run_admin(self, program_path: str):
        """(View 요청) 프로그램을 관리자 권한으로 실행합니다. (pywin32)"""
        if not program_path or not os.path.exists(program_path): return
        try:
            print(f"정보: 실행 (관리자): {program_path}")
            # 'runas' 동사(verb)를 사용하여 관리자 권한 상승(UAC)을 요청
            win32api.ShellExecute(
                0,                          # 부모 창 핸들 (없음)
                'runas',                    # (핵심) 관리자 권한으로 실행
                program_path,               # 실행 파일
                None,                       # 매개변수 (없음)
                os.path.dirname(program_path), # 작업 디렉토리
                1                           # 창 표시 (SW_SHOWNORMAL)
            )
        except Exception as e:
            # 사용자가 UAC 프롬프트에서 '아니오'를 누르면 에러(1223)가 발생할 수 있습니다.
            print(f"정보: 관리자 실행 실패 (UAC 거부 또는 오류): {e}")

    def request_open_location(self, program_path: str):
        """(View 요청) 프로그램의 파일 위치를 탐색기에서 엽니다."""
        if not program_path or not os.path.exists(program_path): return
        try:
            # '/select,' 플래그는 해당 파일을 '선택한 상태로' 탐색기를 엽니다.
            subprocess.Popen(f'explorer /select,"{program_path}"')
        except Exception as e:
            print(f"오류: 파일 위치 열기 실패: {e}")
            
    def request_show_properties(self, program_path: str):
        """(View 요청) 프로그램의 '속성' 창을 엽니다. (pywin32)"""
        if not program_path or not os.path.exists(program_path): return
        try:
            # 'properties' 동사(verb)를 사용하여 파일 속성 창을 직접 호출
            shell.ShellExecuteEx(
                lpVerb='properties',
                lpFile=program_path,
                nShow=shellcon.SW_SHOWNORMAL
            )
        except Exception as e:
            print(f"오류: 속성 창 열기 실패: {e}")

# =============================================================================
# --- 9. 메인 실행 (Main Execution) ---
# =============================================================================

def main():
    """어플리케이션을 초기화하고 실행하는 메인 진입점입니다."""
    
    # (필수) 기본 아이콘 파일이 없으면 실행을 중단합니다. (Guard Clause)
    if not os.path.exists(DEFAULT_ICON):
        print(f"치명적 오류: 기본 아이콘 '{DEFAULT_ICON}' 파일을 찾을 수 없습니다.")
        print(f"프로그램을 실행하기 전에 '{DEFAULT_ICON}' 파일을 준비해주세요.")
        return

    # 1. Qt 어플리케이션 객체 생성 (프로세스 당 1개 필수)
    app = QApplication(sys.argv)
    
    # 2. 메인 컨트롤러(AppManager) 생성
    #    AppManager가 ConfigManager, DesktopScanner 등을 내부적으로 생성/소유
    manager = AppManager(app)
    
    # 3. 어플리케이션 시작 (스캔, 뷰 생성 등)
    manager.start()
    
    # 4. Qt 이벤트 루프 진입
    #    프로그램이 사용자의 입력을 기다리며 종료되지 않도록 대기합니다.
    sys.exit(app.exec())


if __name__ == "__main__":
    # 이 스크립트가 'python desktop_launcher.py'처럼 직접 실행되었을 때만
    # main() 함수를 호출합니다. (다른 파일에서 import될 때는 실행되지 않음)
    main()