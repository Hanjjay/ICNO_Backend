"""
apply_window_app.py - WebEngine 버전
PySide6 QWebEngineView로 React 앱을 네이티브 창으로 감쌈 (Discord 방식)
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PySide6.QtCore import QUrl, Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QColor

REACT_URL = "http://localhost:5173"   # Vite dev server


class ApplyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("커스텀 아이콘")
        self.setMinimumSize(980, 680)
        self.resize(1100, 720)

        # 타이틀바 아이콘
        px = QPixmap(32, 32); px.fill(QColor(99, 102, 241))
        self.setWindowIcon(QIcon(px))

        # WebEngineView
        self.view = QWebEngineView()
        self.view.setUrl(QUrl(REACT_URL))

        # 로딩 중 배경
        self.view.setStyleSheet("background: #1e1f2e;")

        self.setCentralWidget(self.view)

        # 다크 스타일 타이틀바 (Windows 11)
        self._apply_dark_titlebar()

    def _apply_dark_titlebar(self):
        try:
            import ctypes
            hwnd = int(self.winId())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int))
        except:
            pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("커스텀 아이콘")
    app.setStyle("Fusion")
    window = ApplyWindow()
    window.show()
    sys.exit(app.exec())
