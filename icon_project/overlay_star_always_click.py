import sys
import os
import json
import subprocess

# --- (필수) pywin32 라이브러리 임포트 ---
try:
    import win32api
    from win32com.shell import shell, shellcon
except ImportError:
    print("="*50)
    print("오류: 'pywin32' 라이브러리가 설치되지 않았습니다.")
    print("터미널에 [ pip install pywin32 ]를 입력하여 설치해주세요.")
    print("="*50)
    sys.exit(1) # 라이브러리 없으면 즉시 종료

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QMenu, QFileDialog
)
from PySide6.QtGui import QMovie, QPixmap, QMouseEvent, QAction, QIcon
from PySide6.QtCore import Qt, QPoint, QRect, QSize

# --- 설정 파일 ---
SAVE_FILE = "icons_config.json"
DEFAULT_ICON = "star.png" 

# --- 1. 드래그 가능한 '아이콘 창' 위젯 ---
class DraggableIcon(QWidget):
    def __init__(self, manager, icon_id: str, image_path: str, program_path: str, pos: QPoint):
        super().__init__()
        self.manager = manager
        self.icon_id = icon_id
        self.dragging = False
        self.offset = QPoint()

        self.image_path = image_path
        self.program_path = program_path

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.label = QLabel(self)
        self.label.setScaledContents(True)

        self.set_icon(self.image_path) 
        self.setFixedSize(100, 100)
        self.label.setFixedSize(100, 100)
        
        self.move(pos)
        self.update_tooltip()
        self.show()

    def set_icon(self, image_path: str):
        self.image_path = image_path
        
        if hasattr(self, 'movie') and self.movie:
            self.movie.stop()

        if not os.path.exists(image_path):
            print(f"경고: '{image_path}' 없음. 기본값 '{DEFAULT_ICON}'로 대체.")
            image_path = DEFAULT_ICON
            self.image_path = DEFAULT_ICON
            if not os.path.exists(DEFAULT_ICON):
                print(f"오류: 기본 아이콘 '{DEFAULT_ICON}'조차 없습니다.")
                return

        if image_path.lower().endswith('.gif'):
            self.movie = QMovie(image_path)
            self.movie.setScaledSize(QSize(100, 100))
            self.label.setMovie(self.movie)
            self.movie.start()
        else:
            pixmap = QPixmap(image_path)
            self.label.setPixmap(pixmap)
            self.movie = None
            
    def update_tooltip(self):
        if self.program_path:
            self.setToolTip(f"실행: {os.path.basename(self.program_path)}")
        else:
            self.setToolTip("연결된 프로그램 없음 (우클릭 > 프로그램 연결)")

    # --- 2. 드래그 기능 (이전과 동일) ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.raise_()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.offset)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.manager.update_icon_position(self.icon_id, self.pos())

    # --- 3. 더블 클릭 실행 기능 ---
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.run_program() # 일반 실행

    # --- 4. (핵심) '네이티브 재현' 우클릭 메뉴 ---
    def contextMenuEvent(self, event: QMouseEvent):
        menu = QMenu(self)
        
        # 프로그램 경로가 유효한지 확인
        has_valid_path = bool(self.program_path and os.path.exists(self.program_path))

        # --- 네이티브 기능 재현 ---
        open_action = QAction("열기 (Open)", self)
        open_action.triggered.connect(self.run_program)
        open_action.setEnabled(has_valid_path) # 경로가 없으면 비활성화
        menu.addAction(open_action)

        admin_action = QAction("관리자 권한으로 실행", self)
        admin_action.triggered.connect(self.run_program_admin)
        admin_action.setEnabled(has_valid_path)
        menu.addAction(admin_action)
        
        menu.addSeparator()

        loc_action = QAction("파일 위치 열기", self)
        loc_action.triggered.connect(self.open_file_location)
        loc_action.setEnabled(has_valid_path)
        menu.addAction(loc_action)
        
        prop_action = QAction("속성", self)
        prop_action.triggered.connect(self.show_properties)
        prop_action.setEnabled(has_valid_path)
        menu.addAction(prop_action)
        
        menu.addSeparator()

        # --- 런처 고유 기능 ---
        link_action = QAction("프로그램 연결하기...", self)
        link_action.triggered.connect(self.link_program)
        menu.addAction(link_action)

        change_icon_action = QAction("아이콘 변경하기...", self)
        change_icon_action.triggered.connect(self.change_icon)
        menu.addAction(change_icon_action)

        menu.addSeparator()

        delete_action = QAction("이 아이콘 삭제하기", self)
        delete_action.triggered.connect(self.delete_icon)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        quit_action = QAction("모든 런처 종료", self)
        quit_action.triggered.connect(self.manager.quit_app)
        menu.addAction(quit_action)

        menu.exec(event.globalPos())

    # --- 5. (신규) '네이티브 기능' 헬퍼 함수들 ---
    def run_program(self):
        """일반 '열기' 실행"""
        if not self.program_path or not os.path.exists(self.program_path):
            print("오류: 프로그램 경로가 설정되지 않았거나 파일을 찾을 수 없습니다.")
            return
        try:
            print(f"Executing: {self.program_path}")
            subprocess.Popen([self.program_path], cwd=os.path.dirname(self.program_path))
        except Exception as e:
            print(f"프로그램 실행 오류: {e}")

    def run_program_admin(self):
        """'관리자 권한으로 실행' (pywin32 사용)"""
        if not self.program_path or not os.path.exists(self.program_path):
            return
        try:
            print(f"Executing as admin: {self.program_path}")
            win32api.ShellExecute(
                0,           # 부모 창 핸들 (없음)
                'runas',     # (핵심) 관리자 권한으로 실행
                self.program_path, # 실행 파일
                None,        # 매개변수 (없음)
                os.path.dirname(self.program_path), # 작업 디렉토리
                1            # 창 표시
            )
        except Exception as e:
            print(f"관리자 실행 오류: {e}")

    def open_file_location(self):
        """'파일 위치 열기' (탐색기 사용)"""
        if not self.program_path or not os.path.exists(self.program_path):
            return
        try:
            # '/select,' 플래그는 해당 파일을 선택한 상태로 탐색기를 엽니다.
            subprocess.Popen(f'explorer /select,"{self.program_path}"')
        except Exception as e:
            print(f"파일 위치 열기 오류: {e}")
            
    def show_properties(self):
        """'속성' 창 열기 (pywin32 사용)"""
        if not self.program_path or not os.path.exists(self.program_path):
            return
        try:
            # (핵심) 'properties' 동사를 사용하여 속성 창을 엽니다.
            shell.ShellExecuteEx(
                lpVerb='properties',
                lpFile=self.program_path,
                nShow=shellcon.SW_SHOWNORMAL
            )
        except Exception as e:
            print(f"속성 창 열기 오류: {e}")

    # --- 6. (기존) 런처 고유 기능 함수들 ---
    def link_program(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "실행할 프로그램 선택", "", "실행 파일 (*.exe);;바로 가기 (*.lnk);;모든 파일 (*.*)"
        )
        if file_path:
            # (수정) .lnk 파일일 경우 대상 경로를 읽어옴
            if file_path.lower().endswith(".lnk"):
                target_path = self.resolve_lnk(file_path)
                if target_path:
                    self.program_path = target_path
                else:
                    print(".lnk 파일 대상 경로 읽기 실패. 원본 .lnk 경로를 저장합니다.")
                    self.program_path = file_path # 실패 시 .lnk 자체 저장
            else:
                self.program_path = file_path
                
            self.update_tooltip()
            self.manager.update_icon_data(self.icon_id, "program_path", self.program_path)
            print(f"프로그램 연결됨: {self.program_path}")

    def change_icon(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "아이콘 이미지 선택", "", "이미지 파일 (*.png *.jpg *.jpeg *.gif);;모든 파일 (*.*)"
        )
        if file_path:
            self.set_icon(file_path)
            self.manager.update_icon_data(self.icon_id, "image_path", file_path)
            print(f"아이콘 변경됨: {self.image_path}")

    def delete_icon(self):
        self.manager.remove_icon(self.icon_id)
        self.close()

    def resolve_lnk(self, lnk_path):
        """(신규) .lnk(바로 가기) 파일의 실제 대상 경로를 반환합니다. (pywin32 사용)"""
        try:
            shortcut = shell.Dispatch("WScript.Shell").CreateShortCut(lnk_path)
            return shortcut.TargetPath
        except Exception as e:
            print(f".lnk 파일 분석 오류: {e}")
            return None


# --- 7. 아이콘 설정(JSON) 관리자 (이전 코드와 거의 동일) ---
class IconManager:
    def __init__(self, app: QApplication):
        self.app = app
        self.icons_windows = {}
        self.config_data = {}
        self.load_config()

    def load_config(self):
        if not os.path.exists(SAVE_FILE):
            print(f"설정 파일 '{SAVE_FILE}' 없음. 예시 파일 생성.")
            self.config_data = {
                "my_first_icon": {
                    "image_path": DEFAULT_ICON,
                    "program_path": "",
                    "pos_x": 100,
                    "pos_y": 100
                }
            }
            self.save_config()
        else:
            try:
                with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
            except Exception as e:
                print(f"설정 파일 읽기 오류: {e}")
                self.config_data = {}

        for icon_id, data in self.config_data.items():
            self.create_icon_window(icon_id, data)

    def create_icon_window(self, icon_id, data):
        if icon_id in self.icons_windows:
            self.icons_windows[icon_id].close()

        icon_widget = DraggableIcon(
            manager=self,
            icon_id=icon_id,
            image_path=data.get("image_path", DEFAULT_ICON),
            program_path=data.get("program_path", ""),
            pos=QPoint(data.get("pos_x", 10), data.get("pos_y", 10))
        )
        self.icons_windows[icon_id] = icon_widget

    def save_config(self):
        try:
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"설정 파일 저장 오류: {e}")

    def update_icon_position(self, icon_id, pos: QPoint):
        if icon_id in self.config_data:
            self.config_data[icon_id]["pos_x"] = pos.x()
            self.config_data[icon_id]["pos_y"] = pos.y()
            self.save_config()

    def update_icon_data(self, icon_id, key: str, value: str):
        if icon_id in self.config_data:
            self.config_data[icon_id][key] = value
            self.save_config()

    def remove_icon(self, icon_id):
        if icon_id in self.config_data:
            del self.config_data[icon_id]
        if icon_id in self.icons_windows:
            del self.icons_windows[icon_id]
        self.save_config()
            
    def quit_app(self):
        print("런처를 종료합니다...")
        self.app.quit()

# --- 8. 메인 실행 (이전 코드와 동일) ---
def main():
    if not os.path.exists(DEFAULT_ICON):
        print(f"오류: 기본 아이콘 '{DEFAULT_ICON}' 파일을 찾을 수 없습니다.")
        print(f"프로그램을 실행하기 전에 '{DEFAULT_ICON}' 파일을 준비해주세요.")
        return

    app = QApplication(sys.argv)
    
    app.setQuitOnLastWindowClosed(False)

    manager = IconManager(app)
    
    if not manager.icons_windows:
        print("로드할 아이콘이 없습니다. 'icons_config.json'을 확인하세요.")
        print("프로그램을 종료합니다.")
        return

    sys.exit(app.exec())


if __name__ == "__main__":
    main()