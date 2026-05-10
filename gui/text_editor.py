"""Text Editor Window for viewing and editing files."""
from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from gui.window import BaseWindow


class TextEditorWindow(BaseWindow):
    """Simple text editor for viewing and editing files."""

    def __init__(self, kernel, file_path="", content="", parent=None):
        title = f"Text Editor - {file_path.split('/')[-1] if file_path else 'Untitled'}"
        super().__init__(title, kernel, width=700, height=500)

        self.file_path = file_path
        self.original_content = content

        # Toolbar
        toolbar = self._create_toolbar()
        self.content_layout.addWidget(toolbar)

        # Text area
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: none;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                padding: 8px;
                selection-background-color: #45475a;
            }
        """)
        font = QFont("Consolas", 13)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_edit.setFont(font)
        self.text_edit.setPlainText(content)
        self.content_layout.addWidget(self.text_edit)

        # Status bar
        status = QFrame()
        status.setStyleSheet("""
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
        status_layout = QHBoxLayout(status)
        self.status_label = QLabel(f"Lines: 0  |  Characters: 0")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        self.path_label = QLabel(file_path or "Untitled")
        self.path_label.setStyleSheet("color: #89b4fa;")
        status_layout.addWidget(self.path_label)
        self.content_layout.addWidget(status)

        self._update_status()
        self.text_edit.textChanged.connect(self._update_status)

    def _create_toolbar(self):
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border-bottom: 1px solid #45475a;
                padding: 4px;
            }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 6px 14px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QPushButton#saveBtn {
                background-color: #a6e3a1;
                color: #1e1e2e;
            }
            QPushButton#saveBtn:hover {
                background-color: #94e2d5;
            }
        """)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setSpacing(6)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self.save_file)
        bar_layout.addWidget(save_btn)

        save_as_btn = QPushButton("Save As")
        save_as_btn.clicked.connect(self.save_as_file)
        bar_layout.addWidget(save_as_btn)

        bar_layout.addStretch()

        self.content_label = QLabel(self.file_path or "New File")
        self.content_label.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        bar_layout.addWidget(self.content_label)

        return bar

    def _update_status(self):
        text = self.text_edit.toPlainText()
        lines = text.count('\n') + 1
        chars = len(text)
        self.status_label.setText(f"Lines: {lines}  |  Characters: {chars}")

    def save_file(self):
        if not self.file_path:
            self.save_as_file()
            return

        content = self.text_edit.toPlainText()
        success, error = self.kernel.filesystem.write_file(self.file_path, content)
        if success:
            self.original_content = content
            self.status_label.setText(f"Saved: {self.file_path}")
        else:
            QMessageBox.warning(self, "Error", f"Failed to save: {error}")

    def save_as_file(self):
        from PyQt6.QtWidgets import QInputDialog
        path, ok = QInputDialog.getText(
            self, "Save As", "File path:",
            text=self.file_path or "/home/user/Documents/untitled.txt"
        )
        if ok and path:
            content = self.text_edit.toPlainText()
            success, error = self.kernel.filesystem.write_file(path, content)
            if success:
                self.file_path = path
                self.content_label.setText(path)
                self.path_label.setText(path)
                self.setWindowTitle(f"Text Editor - {path.split('/')[-1]}")
                self.original_content = content
                self.status_label.setText(f"Saved: {path}")
            else:
                QMessageBox.warning(self, "Error", f"Failed to save: {error}")
