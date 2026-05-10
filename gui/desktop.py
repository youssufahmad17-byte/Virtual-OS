"""Desktop Widget with icons, context menu, desktop directory sync, and drag-and-drop."""
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QMenu, QGridLayout,
    QPushButton, QInputDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont
from gui.icons import IconFactory, Colors


class DesktopIcon(QWidget):
    """A single desktop icon with modern styling."""

    double_clicked = pyqtSignal()
    right_clicked = pyqtSignal()

    def __init__(self, icon_fn, label, color, item_path, is_dir, parent=None):
        super().__init__(parent)
        self.item_path = item_path
        self.is_dir = is_dir
        self.setFixedSize(80, 90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(48, 48)
        icon = icon_fn(color=color, size=48)
        if icon:
            self.icon_label.setPixmap(icon.pixmap(48, 48))
        layout.addWidget(self.icon_label)

        self.text_label = QLabel(label)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("""
            QLabel {
                color: #cdd6f4;
                font-size: 11px;
                background-color: transparent;
                padding: 2px 4px;
                border-radius: 3px;
            }
            QLabel:hover {
                background-color: rgba(69, 71, 90, 0.4);
            }
        """)
        self.text_label.setWordWrap(True)
        layout.addWidget(self.text_label)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit()
        super().mousePressEvent(event)


class DesktopWidget(QWidget):
    """Main desktop area with Desktop directory sync and drag-and-drop."""

    open_app = pyqtSignal(str)
    open_path = pyqtSignal(str)

    def __init__(self, kernel, parent=None):
        super().__init__(parent)
        self.kernel = kernel
        self.desktop_path = "/home/user/Desktop"
        self._last_desktop_items = None

        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e1e2e, stop:0.5 #181825, stop:1 #11111b);
            }
        """)

        # No layout - use absolute positioning for all icons
        self.grid_layout = None

        # Drag state
        self._dragging = False
        self._drag_widget = None
        self._drag_path = None
        self._drag_is_dir = False
        self._drag_offset = QPoint()
        self._highlight_widget = None

        self._create_app_shortcuts()
        self._create_icons()

        # Record initial directory state so timer doesn't trigger unnecessary refresh
        success, items, _ = self.kernel.filesystem.ls(self.desktop_path, long_format=True)
        if success:
            self._last_desktop_items = frozenset(item["name"] for item in items if not item["name"].startswith("."))

        self.setAcceptDrops(False)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _next_grid_position(self, row, col):
        """Calculate the next grid position for an icon."""
        x = 20 + col * 92
        y = 20 + row * 102
        col += 1
        if col >= 6:
            col = 0
            row += 1
        return x, y, row, col

    def _create_app_shortcuts(self):
        """Create the fixed app shortcut icons (never refreshed)."""
        app_shortcuts = [
            (IconFactory.folder, Colors.BLUE, "Files", "file_manager"),
            (IconFactory.terminal, Colors.GREEN, "Terminal", "terminal"),
            (IconFactory.chart, Colors.MAUVE, "Processes", "process_monitor"),
            (IconFactory.monitor, Colors.SAPPHIRE, "Devices", "device_manager"),
            (IconFactory.memory, Colors.TEAL, "Memory", "memory_monitor"),
            (IconFactory.document, Colors.PEACH, "Documents", "documents"),
        ]

        row, col = 0, 0
        for icon_fn, color, label, app_id in app_shortcuts:
            x, y, row, col = self._next_grid_position(row, col)
            icon_widget = DesktopIcon(icon_fn, label, color, "", False, parent=self)
            icon_widget.move(x, y)
            icon_widget.double_clicked.connect(lambda aid=app_id: self.open_app.emit(aid))

    def _create_icons(self):
        # Build set of expected desktop file/folder paths
        success, items, _ = self.kernel.filesystem.ls(self.desktop_path, long_format=True)
        expected_paths = set()
        if success:
            for item in items:
                if not item["name"].startswith("."):
                    expected_paths.add(self.desktop_path.rstrip("/") + "/" + item["name"])

        # Get all current desktop file/folder icons (snapshot)
        current_icons = {}
        for child in list(self.children()):
            if isinstance(child, DesktopIcon) and child.item_path:
                current_icons[child.item_path] = child

        # Remove icons for deleted items
        for path, widget in list(current_icons.items()):
            if path not in expected_paths:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        # Calculate starting position after app shortcuts (6 icons in row 0)
        row, col = 1, 0  # Start at row 1 since row 0 has app shortcuts

        # Add icons for new items
        existing_paths = set(current_icons.keys())
        if success:
            for item in items:
                if item["name"].startswith("."):
                    continue
                item_path = self.desktop_path.rstrip("/") + "/" + item["name"]
                if item_path not in existing_paths:
                    if item["is_dir"]:
                        icon_fn = IconFactory.folder
                        color = Colors.BLUE
                    else:
                        icon_fn = IconFactory.file
                        color = Colors.SUBTEXT0

                    x = 20 + col * 92
                    y = 20 + row * 102
                    col += 1
                    if col >= 6:
                        col = 0
                        row += 1

                    icon_widget = DesktopIcon(icon_fn, item["name"], color, item_path, item["is_dir"], parent=self)
                    icon_widget.move(x, y)
                    icon_widget.show()
                    icon_widget.double_clicked.connect(lambda p=item_path: self.open_path.emit(p))

    def refresh_desktop(self):
        # Get current directory contents
        success, items, _ = self.kernel.filesystem.ls(self.desktop_path, long_format=True)
        current_items = None
        if success:
            current_items = frozenset(item["name"] for item in items if not item["name"].startswith("."))

        # Skip refresh if contents haven't changed
        if current_items == self._last_desktop_items:
            return

        self._last_desktop_items = current_items

        # Save current positions of user-moved icons (those not in their original grid spot)
        saved_positions = {}
        for child in self.children():
            if isinstance(child, DesktopIcon) and child.item_path:
                saved_positions[child.item_path] = child.pos()

        self._clear_drag()
        self._create_icons()

        # Restore saved positions
        for child in self.children():
            if isinstance(child, DesktopIcon) and child.item_path in saved_positions:
                child.move(saved_positions[child.item_path])

    def _clear_drag(self):
        self._dragging = False
        self._drag_widget = None
        self._drag_path = None
        if self._highlight_widget:
            self._highlight_widget.setStyleSheet("")
            self._highlight_widget = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Find the icon under cursor
            for w in self.children():
                if isinstance(w, DesktopIcon) and w.geometry().contains(event.pos()):
                    if w.item_path:
                        self._dragging = True
                        self._drag_widget = w
                        self._drag_path = w.item_path
                        self._drag_is_dir = w.is_dir
                        self._drag_offset = event.pos() - w.pos()
                        w.raise_()
                        return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_widget:
            # Move widget with mouse using absolute position
            new_pos = event.pos() - self._drag_offset
            self._drag_widget.move(new_pos)
            self._drag_widget.update()

            # Find folder under cursor for drop highlight
            self._update_drop_target(event.pos())
            return  # Don't call super during drag
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging and self._drag_path:
            # Try to drop on a folder
            dropped = False
            if self._highlight_widget and self._highlight_widget.item_path:
                dest_path = self._highlight_widget.item_path.rstrip("/") + "/" + self._drag_path.split("/")[-1]
                source_path = self._drag_path
                if source_path != dest_path and self._highlight_widget.is_dir:
                    if self.kernel.filesystem.exists(source_path):
                        if not self.kernel.filesystem.exists(dest_path):
                            ok, err = self.kernel.filesystem.mv(source_path, dest_path)
                            if ok:
                                dropped = True

            # Save widget and position before clearing
            drop_widget = self._drag_widget
            if dropped and self._drag_widget:
                self._drag_widget.deleteLater()

            self._clear_drag()
            if dropped:
                self.refresh_desktop()
            elif drop_widget:
                # Force repaint to show the new position
                drop_widget.repaint()
                self.repaint()
            return
        super().mouseReleaseEvent(event)

    def _get_all_icons(self):
        """Get all DesktopIcon widgets."""
        return [child for child in self.children() if isinstance(child, DesktopIcon)]

    def _update_drop_target(self, pos):
        # Clear previous highlight
        if self._highlight_widget:
            self._highlight_widget.setStyleSheet("")
            self._highlight_widget = None

        # Find folder under cursor
        for w in self._get_all_icons():
            if w.is_dir and w.item_path and w.item_path != self._drag_path:
                if w.geometry().contains(pos):
                    self._highlight_widget = w
                    w.setStyleSheet("""
                        QWidget {
                            background-color: rgba(137, 180, 250, 0.2);
                            border-radius: 8px;
                        }
                    """)
                    break

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 6px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #313244;
            }
            QMenu::separator {
                height: 1px;
                background-color: #45475a;
                margin: 4px 8px;
            }
        """)

        refresh = menu.addAction("Refresh Desktop")
        refresh.triggered.connect(self.refresh_desktop)
        menu.addSeparator()

        new_folder = menu.addAction("New Folder")
        new_folder.triggered.connect(self._new_folder)

        new_file = menu.addAction("New File")
        new_file.triggered.connect(self._new_file)
        menu.addSeparator()

        terminal = menu.addAction("Open Terminal")
        terminal.triggered.connect(lambda: self.open_app.emit("terminal"))

        file_mgr = menu.addAction("Open File Manager")
        file_mgr.triggered.connect(lambda: self.open_app.emit("file_manager"))

        menu.addSeparator()

        sys_info = menu.addAction("System Information")
        sys_info.triggered.connect(self._show_sys_info)

        menu.exec(self.mapToGlobal(pos))

    def _new_folder(self):
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            path = self.desktop_path.rstrip("/") + "/" + name
            self.kernel.filesystem.mkdir(path)
            self.refresh_desktop()

    def _new_file(self):
        name, ok = QInputDialog.getText(self, "New File", "File name:")
        if ok and name:
            path = self.desktop_path.rstrip("/") + "/" + name
            self.kernel.filesystem.create_file(path)
            self.refresh_desktop()

    def _show_sys_info(self):
        info = self.kernel.get_system_info()
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("System Information")
        msg.setText("\n".join(f"{k}: {v}" for k, v in info.items()))
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 12px;
            }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
            }
        """)
        msg.exec()
