"""VirtualOS - A fully functional virtual operating system with PyQt6 GUI."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedLayout, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QScreen

from core.kernel import Kernel
from gui.desktop import DesktopWidget
from gui.taskbar import Taskbar
from gui.terminal import TerminalWindow
from gui.file_manager import FileManagerWindow
from gui.process_monitor import ProcessMonitorWindow
from gui.device_manager_ui import DeviceManagerWindow
from gui.memory_monitor import MemoryMonitorWindow
from gui.text_editor import TextEditorWindow


class VirtualOS(QMainWindow):
    """Main VirtualOS window."""

    def __init__(self):
        super().__init__()
        self.kernel = Kernel()
        self.windows = {}
        self.window_counter = 0

        self.setWindowTitle("VirtualOS 1.0")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen.width(), screen.height())

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QStackedLayout(central)

        # Desktop
        self.desktop = DesktopWidget(self.kernel)
        self.desktop.open_app.connect(self.open_app)
        self.desktop.open_path.connect(self.open_path)
        layout.addWidget(self.desktop)

        # Taskbar
        self.taskbar = Taskbar(self.kernel)
        self.taskbar.setParent(self)
        self.taskbar.move(0, screen.height() - 44)
        self.taskbar.resize(screen.width(), 44)
        self.taskbar.launch_app.connect(self.open_app)
        self.taskbar.shutdown.connect(self.shutdown)

        # System update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_system)
        self.update_timer.start(1000)

    def _update_system(self):
        self.kernel.update()
        # Refresh desktop icons if Desktop directory changed
        self.desktop.refresh_desktop()

    def open_app(self, app_id):
        """Open an application window."""
        self.window_counter += 1
        window_id = f"{app_id}_{self.window_counter}"

        app_map = {
            "terminal": lambda: TerminalWindow(self.kernel),
            "file_manager": lambda: self._create_file_manager(),
            "process_monitor": lambda: ProcessMonitorWindow(self.kernel),
            "device_manager": lambda: DeviceManagerWindow(self.kernel),
            "memory_monitor": lambda: MemoryMonitorWindow(self.kernel),
            "documents": lambda: self._create_file_manager("/home/user/Documents"),
        }

        if app_id in app_map:
            window = app_map[app_id]()
            offset = (self.window_counter % 5) * 30
            window.move(50 + offset, 30 + offset)
            window.window_closed.connect(lambda wid=window_id: self._window_closed(wid))
            window.show()

            self.windows[window_id] = window
            self.taskbar.add_window(window_id, window.windowTitle(), window, app_id=app_id)

    def _create_file_manager(self, path="/home/user"):
        fm = FileManagerWindow(self.kernel)
        fm.open_file.connect(self.open_file)
        if path != "/home/user":
            fm.list_widget.refresh(path)
            fm.path_edit.setText(path)
        return fm

    def open_file(self, file_path):
        """Open a file in text editor or a directory in file manager."""
        entry = self.kernel.filesystem._resolve_path(file_path)
        if entry is None:
            return

        if entry.is_dir:
            # Open file manager navigated to this directory
            self.window_counter += 1
            window_id = f"fm_{self.window_counter}"
            fm = FileManagerWindow(self.kernel)
            fm.open_file.connect(self.open_file)
            fm.list_widget.refresh(file_path)
            fm.path_edit.setText(file_path)
            offset = (self.window_counter % 5) * 30
            fm.move(50 + offset, 30 + offset)
            fm.window_closed.connect(lambda wid=window_id: self._window_closed(wid))
            fm.show()
            self.windows[window_id] = fm
            self.taskbar.add_window(window_id, f"Files - {entry.name}", fm, app_id="file_manager")
        else:
            # Open file in text editor
            success, content, error = self.kernel.filesystem.read_file(file_path)
            if success:
                self.window_counter += 1
                window_id = f"editor_{self.window_counter}"
                editor = TextEditorWindow(self.kernel, file_path, content)
                offset = (self.window_counter % 5) * 30
                editor.move(80 + offset, 50 + offset)
                editor.window_closed.connect(lambda wid=window_id: self._window_closed(wid))
                editor.show()
                self.windows[window_id] = editor
                self.taskbar.add_window(window_id, editor.windowTitle(), editor, app_id="documents")

    def open_path(self, path):
        """Open a path - routes to file manager or text editor based on type."""
        resolved = self.kernel.filesystem._resolve_path(path)
        if resolved is None:
            return
        if resolved.is_dir:
            self.window_counter += 1
            window_id = f"fm_{self.window_counter}"
            fm = FileManagerWindow(self.kernel)
            fm.open_file.connect(self.open_file)
            fm.list_widget.refresh(path)
            fm.path_edit.setText(path)
            offset = (self.window_counter % 5) * 30
            fm.move(50 + offset, 30 + offset)
            fm.window_closed.connect(lambda wid=window_id: self._window_closed(wid))
            fm.show()
            self.windows[window_id] = fm
            self.taskbar.add_window(window_id, f"Files - {resolved.name}", fm, app_id="file_manager")
        else:
            self.open_file(path)

    def _window_closed(self, window_id):
        if window_id in self.windows:
            del self.windows[window_id]
        self.taskbar.remove_window(window_id)

    def shutdown(self):
        QApplication.instance().quit()


def main():
    """Entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    app.setStyleSheet("""
        * {
            font-family: 'Segoe UI', 'Arial', sans-serif;
        }
    """)

    os = VirtualOS()
    os.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
