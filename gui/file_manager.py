"""File Manager Window with file editing, rename, and modern styling."""
from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QListView, QSplitter, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFrame, QHeaderView, QAbstractItemView,
    QInputDialog, QMenu, QWidget, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor
from gui.window import BaseWindow
from core.filesystem import FileEntry
from gui.icons import IconFactory, Colors


class FileTreeWidget(QTreeWidget):
    """Tree view for directory navigation."""

    def __init__(self, vfs):
        super().__init__()
        self.vfs = vfs
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #181825;
                color: #cdd6f4;
                border: none;
                font-size: 13px;
                padding: 4px;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #313244;
                color: #cdd6f4;
            }
        """)
        self.setHeaderHidden(True)
        self.setAnimated(True)
        self.setIndentation(16)
        self.setColumnCount(1)
        self.refresh()

    def refresh(self):
        self.clear()
        self._build_tree(self.vfs.root, None)

    def _build_tree(self, entry, parent_item):
        if not entry.is_dir or not entry.children:
            return
        dirs = [c for c in entry.children.values() if c.is_dir]
        for child in sorted(dirs, key=lambda x: x.name):
            item = QTreeWidgetItem([child.name])
            item.setData(0, Qt.ItemDataRole.UserRole, child)
            if parent_item is None:
                self.addTopLevelItem(item)
            else:
                parent_item.addChild(item)
            self._build_tree(child, item)

    def get_selected_path(self):
        items = self.selectedItems()
        if items:
            entry = items[0].data(0, Qt.ItemDataRole.UserRole)
            if entry:
                return entry.path if entry.path else "/"
        return None


class FileListWidget(QListWidget):
    """List view for files and directories."""

    file_opened = pyqtSignal(str)  # emits file path
    folder_navigated = pyqtSignal(str)  # emits folder path

    def __init__(self, vfs):
        super().__init__()
        self.vfs = vfs
        self.current_path = "/home/user"
        self.setStyleSheet("""
            QListWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: none;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #313244;
            }
            QListWidget::item:selected {
                background-color: #313244;
                color: #cdd6f4;
            }
        """)
        self.setViewMode(QListView.ViewMode.ListMode)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.itemDoubleClicked.connect(self._on_double_click)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.refresh()

    def refresh(self, path=None):
        if path:
            self.current_path = path
        self.clear()
        entry = self.vfs._resolve_path(self.current_path)
        if entry and entry.is_dir and entry.children:
            items = sorted(entry.children.values(), key=lambda x: (not x.is_dir, x.name))
            for item in items:
                label = f"  {item.name}"
                list_item = QListWidgetItem(label)
                list_item.setData(Qt.ItemDataRole.UserRole, item)
                if item.is_dir:
                    list_item.setForeground(QColor(Colors.BLUE))
                else:
                    list_item.setForeground(QColor(Colors.SUBTEXT0))
                self.addItem(list_item)

    def _on_double_click(self, item):
        entry = item.data(Qt.ItemDataRole.UserRole)
        if not entry:
            return
        if entry.is_dir:
            new_path = self.current_path.rstrip("/") + "/" + entry.name
            self.refresh(new_path)
            self.folder_navigated.emit(new_path)
        else:
            file_path = self.current_path.rstrip("/") + "/" + entry.name
            self.file_opened.emit(file_path)

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
                padding: 6px 20px;
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

        new_folder = QAction("New Folder", self)
        new_file = QAction("New File", self)
        rename = QAction("Rename", self)
        delete = QAction("Delete", self)
        edit_file = QAction("Edit", self)

        new_folder.triggered.connect(self._new_folder)
        new_file.triggered.connect(self._new_file)
        rename.triggered.connect(self._rename_item)
        delete.triggered.connect(self._delete_item)
        edit_file.triggered.connect(self._edit_selected)

        menu.addAction(new_folder)
        menu.addAction(new_file)
        menu.addSeparator()
        menu.addAction(edit_file)
        menu.addAction(rename)
        menu.addAction(delete)
        menu.exec(pos)

    def _get_selected_entry(self):
        items = self.selectedItems()
        if items:
            return items[0].data(Qt.ItemDataRole.UserRole)
        return None

    def _new_folder(self):
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            path = self.current_path.rstrip("/") + "/" + name
            self.vfs.mkdir(path)
            self.refresh()

    def _new_file(self):
        name, ok = QInputDialog.getText(self, "New File", "File name:")
        if ok and name:
            path = self.current_path.rstrip("/") + "/" + name
            self.vfs.create_file(path)
            self.refresh()

    def _rename_item(self):
        entry = self._get_selected_entry()
        if not entry:
            return
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=entry.name)
        if ok and new_name and new_name != entry.name:
            old_path = self.current_path.rstrip("/") + "/" + entry.name
            new_path = self.current_path.rstrip("/") + "/" + new_name
            self.vfs.mv(old_path, new_path)
            self.refresh()

    def _delete_item(self):
        entry = self._get_selected_entry()
        if entry:
            path = self.current_path.rstrip("/") + "/" + entry.name
            self.vfs.rm(path, recursive=True)
            self.refresh()

    def _edit_selected(self):
        entry = self._get_selected_entry()
        if entry and not entry.is_dir:
            file_path = self.current_path.rstrip("/") + "/" + entry.name
            self.file_opened.emit(file_path)


class FileManagerWindow(BaseWindow):
    """File manager application window."""

    open_file = pyqtSignal(str)

    def __init__(self, kernel, parent=None):
        super().__init__("File Manager", kernel, width=900, height=600)

        # Navigation bar
        nav_bar = self._create_nav_bar()
        self.content_layout.addWidget(nav_bar)

        # Splitter with tree and list
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.tree_widget = FileTreeWidget(kernel.filesystem)
        self.tree_widget.clicked.connect(self._on_tree_clicked)
        splitter.addWidget(self.tree_widget)

        self.list_widget = FileListWidget(kernel.filesystem)
        self.list_widget.folder_navigated.connect(self._on_folder_navigated)
        self.list_widget.file_opened.connect(self._on_file_opened)
        splitter.addWidget(self.list_widget)

        splitter.setSizes([220, 680])
        self.content_layout.addWidget(splitter)

        # Status bar
        status = self._create_status_bar()
        self.content_layout.addWidget(status)

    def _create_nav_bar(self):
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border-bottom: 1px solid #45475a;
                padding: 6px;
            }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QLineEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }
        """)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setSpacing(6)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self._go_back)
        bar_layout.addWidget(back_btn)

        home_btn = QPushButton("Home")
        home_btn.clicked.connect(self._go_home)
        bar_layout.addWidget(home_btn)

        desktop_btn = QPushButton("Desktop")
        desktop_btn.clicked.connect(self._go_desktop)
        bar_layout.addWidget(desktop_btn)

        self.path_edit = QLineEdit()
        self.path_edit.setText("/home/user")
        self.path_edit.returnPressed.connect(self._navigate_to_path)
        bar_layout.addWidget(self.path_edit, 1)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh)
        bar_layout.addWidget(refresh_btn)

        return bar

    def _create_status_bar(self):
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border-top: 1px solid #45475a;
                padding: 4px;
            }
            QLabel {
                color: #a6adc8;
                font-size: 11px;
            }
        """)
        bar_layout = QHBoxLayout(bar)
        self.status_label = QLabel("Ready")
        bar_layout.addWidget(self.status_label)
        bar_layout.addStretch()
        return bar

    def _navigate_to_path(self):
        path = self.path_edit.text()
        self.list_widget.refresh(path)
        self._update_status(path)

    def _go_back(self):
        path = self.list_widget.current_path
        parent = path.rsplit("/", 1)[0] or "/"
        self.list_widget.refresh(parent)
        self.path_edit.setText(parent)
        self._update_status(parent)

    def _go_home(self):
        self.list_widget.refresh("/home/user")
        self.path_edit.setText("/home/user")
        self._update_status("/home/user")

    def _go_desktop(self):
        self.list_widget.refresh("/home/user/Desktop")
        self.path_edit.setText("/home/user/Desktop")
        self._update_status("/home/user/Desktop")

    def _refresh(self):
        self.list_widget.refresh()
        self.tree_widget.refresh()
        self._update_status(self.list_widget.current_path)

    def _on_tree_clicked(self, index):
        path = self.tree_widget.get_selected_path()
        if path:
            self.list_widget.refresh(path)
            self.path_edit.setText(path)
            self._update_status(path)

    def _on_folder_navigated(self, path):
        self.path_edit.setText(path)
        self._update_status(path)

    def _on_file_opened(self, file_path):
        self.open_file.emit(file_path)

    def _update_status(self, path):
        entry = self.kernel.filesystem._resolve_path(path)
        if entry:
            count = len(entry.children) if entry.is_dir and entry.children else 0
            self.status_label.setText(f"{path}  --  {count} items")
