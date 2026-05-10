"""Taskbar with start button, window list with icons, and system tray."""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QFrame, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QIcon


class Colors:
    BLUE = "#89b4fa"
    GREEN = "#a6e3a1"
    MAUVE = "#cba6f7"
    SAPPHIRE = "#74c7ec"
    TEAL = "#94e2d5"
    PEACH = "#fab387"
    TEXT = "#cdd6f4"
    SURFACE0 = "#313244"
    SURFACE1 = "#45475a"
    SURFACE2 = "#585b70"
    BASE = "#1e1e2e"
    MANTLE = "#181825"


class IconFactory:
    """Small icon factory for taskbar buttons."""

    @staticmethod
    def _pixmap(size, draw_fn):
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        draw_fn(p, size)
        p.end()
        return px

    @staticmethod
    def _bg(p, size, color):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(color + "25"))
        p.drawRoundedRect(2, 2, size - 4, size - 4, 6, 6)

    @staticmethod
    def folder(size=24):
        def draw(p, s):
            IconFactory._bg(p, s, Colors.BLUE)
            p.setPen(QColor(Colors.BLUE))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(5, 8, 14, 10, 2, 2)
            p.setBrush(QColor(Colors.BLUE))
            p.drawRoundedRect(7, 6, 5, 3, 1, 1)
        return IconFactory._pixmap(size, draw)

    @staticmethod
    def terminal(size=24):
        def draw(p, s):
            IconFactory._bg(p, s, Colors.GREEN)
            p.setPen(QColor(Colors.GREEN))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(4, 6, 16, 12, 2, 2)
            p.drawLine(8, 10, 11, 13)
            p.drawLine(11, 13, 8, 16)
            p.drawLine(13, 16, 17, 16)
        return IconFactory._pixmap(size, draw)

    @staticmethod
    def chart(size=24):
        def draw(p, s):
            IconFactory._bg(p, s, Colors.MAUVE)
            p.setPen(QColor(Colors.MAUVE))
            p.setBrush(QColor(Colors.MAUVE + "80"))
            p.drawRect(5, 13, 4, 7)
            p.drawRect(10, 10, 4, 10)
            p.drawRect(15, 7, 4, 13)
        return IconFactory._pixmap(size, draw)

    @staticmethod
    def monitor(size=24):
        def draw(p, s):
            IconFactory._bg(p, s, Colors.SAPPHIRE)
            p.setPen(QColor(Colors.SAPPHIRE))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(4, 5, 16, 10, 2, 2)
            p.drawLine(9, 15, 9, 18)
            p.drawLine(15, 15, 15, 18)
            p.drawLine(7, 18, 17, 18)
        return IconFactory._pixmap(size, draw)

    @staticmethod
    def memory(size=24):
        def draw(p, s):
            IconFactory._bg(p, s, Colors.TEAL)
            p.setPen(QColor(Colors.TEAL))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(5, 8, 14, 8, 2, 2)
            for y in [10, 12, 14]:
                p.drawLine(8, y, 16, y)
        return IconFactory._pixmap(size, draw)

    @staticmethod
    def document(size=24):
        def draw(p, s):
            IconFactory._bg(p, s, Colors.PEACH)
            p.setPen(QColor(Colors.PEACH))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(7, 4, 10, 16, 1, 1)
            for y in [8, 11, 14, 17]:
                p.drawLine(9, y, 15, y)
        return IconFactory._pixmap(size, draw)

    @staticmethod
    def start_icon(size=24):
        def draw(p, s):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(Colors.BLUE))
            # 4 squares like Windows logo but cleaner
            p.drawRoundedRect(3, 3, 8, 8, 2, 2)
            p.drawRoundedRect(13, 3, 8, 8, 2, 2)
            p.drawRoundedRect(3, 13, 8, 8, 2, 2)
            p.drawRoundedRect(13, 13, 8, 8, 2, 2)
        return IconFactory._pixmap(size, draw)


APP_ICONS = {
    "file_manager": IconFactory.folder,
    "terminal": IconFactory.terminal,
    "process_monitor": IconFactory.chart,
    "device_manager": IconFactory.monitor,
    "memory_monitor": IconFactory.memory,
    "documents": IconFactory.document,
}


class StartMenu(QMenu):
    """Start menu with application launcher."""

    launch_app = pyqtSignal(str)
    shutdown = pyqtSignal()
    restart = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QMenu {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px;
                min-width: 280px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
                margin: 2px 4px;
            }
            QMenu::item:selected {
                background-color: #313244;
            }
            QMenu::separator {
                height: 1px;
                background-color: #45475a;
                margin: 6px 8px;
            }
            QLabel {
                color: #89b4fa;
                font-size: 16px;
                font-weight: bold;
                padding: 8px;
            }
        """)
        self._build_menu()

    def _build_menu(self):
        header = QLabel("  VirtualOS")
        self.addAction(header.text())
        self.addSeparator()

        apps = [
            ("File Manager", "file_manager"),
            ("Terminal", "terminal"),
            ("Process Monitor", "process_monitor"),
            ("Device Manager", "device_manager"),
            ("Memory Monitor", "memory_monitor"),
        ]
        for label, app_id in apps:
            action = self.addAction(label)
            action.triggered.connect(lambda checked=False, aid=app_id: self.launch_app.emit(aid))

        self.addSeparator()
        self.addAction("Shut Down").triggered.connect(self.shutdown.emit)
        self.addAction("Restart").triggered.connect(self.restart.emit)

    def show_menu(self, pos):
        self.exec(pos)


class Taskbar(QWidget):
    """Bottom taskbar."""

    launch_app = pyqtSignal(str)
    shutdown = pyqtSignal()

    def __init__(self, kernel, parent=None):
        super().__init__(parent)
        self.kernel = kernel
        self.open_windows = {}

        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.MANTLE};
                border-top: 1px solid {Colors.SURFACE0};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # Start button with icon
        self.start_btn = QPushButton()
        self.start_btn.setFixedSize(44, 36)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.SURFACE0};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SURFACE1};
            }}
            QPushButton:pressed {{
                background-color: {Colors.SURFACE2};
            }}
        """)
        self.start_btn.setIcon(QIcon(IconFactory.start_icon(24)))
        self.start_btn.clicked.connect(self._toggle_start_menu)
        layout.addWidget(self.start_btn)

        # Window list area
        self.window_frame = QFrame()
        self.window_frame.setStyleSheet("QFrame { background: transparent; }")
        self.window_layout = QHBoxLayout(self.window_frame)
        self.window_layout.setContentsMargins(4, 0, 4, 0)
        self.window_layout.setSpacing(4)
        layout.addWidget(self.window_frame, 1)

        # System tray
        tray_frame = QFrame()
        tray_frame.setStyleSheet("QFrame { background: transparent; }")
        tray_layout = QHBoxLayout(tray_frame)
        tray_layout.setContentsMargins(8, 0, 0, 0)
        tray_layout.setSpacing(8)

        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setStyleSheet(f"color: {Colors.GREEN}; font-size: 11px;")
        tray_layout.addWidget(self.cpu_label)

        self.ram_label = QLabel("RAM: 0%")
        self.ram_label.setStyleSheet(f"color: {Colors.BLUE}; font-size: 11px;")
        tray_layout.addWidget(self.ram_label)

        self.clock_label = QLabel("")
        self.clock_label.setStyleSheet(f"color: {Colors.TEXT}; font-size: 12px; font-weight: bold;")
        tray_layout.addWidget(self.clock_label)

        layout.addWidget(tray_frame)

        # Start menu
        self.start_menu = StartMenu(self)
        self.start_menu.launch_app.connect(self.launch_app.emit)
        self.start_menu.shutdown.connect(self._shutdown)
        self.start_menu.restart.connect(self._restart)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._update_stats)
        self.stats_timer.start(2000)

        self._update_clock()
        self._update_stats()

    def _toggle_start_menu(self):
        pos = self.start_btn.mapToGlobal(self.start_btn.rect().bottomLeft())
        self.start_menu.show_menu(pos)

    def add_window(self, window_id, title, window_ref, app_id=None):
        """Add a window button with icon to the taskbar."""
        btn = QPushButton()
        btn.setFixedSize(36, 36)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.SURFACE0};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SURFACE1};
            }}
            QPushButton#active {{
                background-color: {Colors.SURFACE1};
                border-bottom: 2px solid {Colors.BLUE};
            }}
        """)

        # Set icon
        if app_id and app_id in APP_ICONS:
            btn.setIcon(QIcon(APP_ICONS[app_id](24)))

        btn.setToolTip(title)
        btn.clicked.connect(lambda: self._activate_window(window_id))
        btn.setObjectName("active")

        self.window_layout.addWidget(btn)
        self.open_windows[window_id] = (btn, window_ref)

    def remove_window(self, window_id):
        if window_id in self.open_windows:
            btn, _ = self.open_windows[window_id]
            btn.deleteLater()
            del self.open_windows[window_id]

    def _activate_window(self, window_id):
        if window_id in self.open_windows:
            btn, window_ref = self.open_windows[window_id]
            if window_ref.isMinimized():
                window_ref.showNormal()
            window_ref.raise_()
            window_ref.activateWindow()

    def _update_clock(self):
        now = QDateTime.currentDateTime()
        self.clock_label.setText(now.toString("HH:mm:ss"))

    def _update_stats(self):
        usage = self.kernel.memory_manager.get_usage()
        ram_pct = int(usage["usage_percent"])
        cpu_pct = min(100, int(self.kernel.process_manager.get_total_cpu()))
        self.ram_label.setText(f"RAM: {ram_pct}%")
        self.cpu_label.setText(f"CPU: {cpu_pct}%")

        if ram_pct > 80:
            self.ram_label.setStyleSheet(f"color: {Colors.RED}; font-size: 11px;")
        elif ram_pct > 60:
            self.ram_label.setStyleSheet(f"color: {Colors.PEACH}; font-size: 11px;")
        else:
            self.ram_label.setStyleSheet(f"color: {Colors.BLUE}; font-size: 11px;")

    def _shutdown(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Shut Down", "Are you sure you want to shut down VirtualOS?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.shutdown.emit()

    def _restart(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Restart", "Are you sure you want to restart VirtualOS?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.shutdown.emit()

