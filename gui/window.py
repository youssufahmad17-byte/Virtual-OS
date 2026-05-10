"""Base Window class for all virtual OS applications."""
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon, QMouseEvent


class BaseWindow(QMainWindow):
    """Base window with custom title bar, minimize, maximize, close buttons."""

    window_closed = pyqtSignal()
    window_minimized = pyqtSignal()

    def __init__(self, title, kernel, width=800, height=600, icon=None):
        super().__init__()
        self.kernel = kernel
        self.setWindowTitle(title)
        self.resize(width, height)
        self.setMinimumSize(400, 300)

        # Remove native window frame to use custom title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Drag state
        self._drag_pos = None

        # Style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 8px;
            }
        """)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Custom title bar
        self.title_bar = self._create_title_bar(title)
        self.main_layout.addWidget(self.title_bar)

        # Content area
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.addWidget(self.content)

        if icon:
            self.setWindowIcon(icon)

    def _create_title_bar(self, title):
        bar = QFrame()
        bar.setObjectName("titleBar")
        bar.setStyleSheet("""
            QFrame#titleBar {
                background-color: #313244;
                border-bottom: 1px solid #45475a;
                border-radius: 8px 8px 0 0;
            }
            QLabel#titleLabel {
                color: #cdd6f4;
                font-size: 13px;
                font-weight: 600;
                padding-left: 12px;
            }
            QPushButton {
                background-color: transparent;
                color: #a6adc8;
                border: none;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45475a;
                color: #cdd6f4;
            }
            QPushButton#minBtn:hover {
                background-color: #585b70;
                color: #cdd6f4;
            }
            QPushButton#maxBtn:hover {
                background-color: #585b70;
                color: #cdd6f4;
            }
            QPushButton#closeBtn {
                color: #a6adc8;
            }
            QPushButton#closeBtn:hover {
                background-color: #f38ba8;
                color: #1e1e2e;
            }
        """)
        bar.setFixedHeight(36)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(8, 0, 4, 0)
        bar_layout.setSpacing(2)

        # Window icon
        icon_label = QLabel("")
        icon_label.setFixedSize(20, 20)
        bar_layout.addWidget(icon_label)

        # Title label
        title_label = QLabel(title)
        title_label.setObjectName("titleLabel")
        bar_layout.addWidget(title_label)

        bar_layout.addStretch()

        # Window controls
        min_btn = QPushButton("─")
        min_btn.setObjectName("minBtn")
        min_btn.setFixedSize(36, 28)
        min_btn.clicked.connect(self.showMinimized)
        min_btn.clicked.connect(self.window_minimized.emit)
        bar_layout.addWidget(min_btn)

        max_btn = QPushButton("□")
        max_btn.setObjectName("maxBtn")
        max_btn.setFixedSize(36, 28)
        max_btn.clicked.connect(self._toggle_maximize)
        bar_layout.addWidget(max_btn)

        close_btn = QPushButton("×")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(36, 28)
        close_btn.clicked.connect(self.close)
        bar_layout.addWidget(close_btn)

        return bar

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on the title bar
            if self.title_bar.geometry().contains(event.pos()):
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def closeEvent(self, event):
        self.window_closed.emit()
        super().closeEvent(event)
