"""Terminal Emulator Window."""
from PyQt6.QtWidgets import QTextEdit, QLineEdit, QVBoxLayout, QHBoxLayout, QWidget, QScrollBar, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QColor, QKeyEvent
from gui.window import BaseWindow
from apps.shell_commands import ShellCommands
import sys


class TerminalWidget(QTextEdit):
    """Terminal text display area."""

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Cascadia Code', 'Fira Code', 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                border: none;
                padding: 4px;
            }
            QScrollBar:vertical {
                background: #313244;
                width: 8px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #585b70;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        font = QFont("Consolas" if sys.platform == "win32" else "Monaco", 13)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

    def append_colored(self, text, color="#cdd6f4"):
        self.setTextColor(QColor(color))
        self.append(text)
        self.setTextColor(QColor("#cdd6f4"))


class TerminalWindow(BaseWindow):
    """Terminal application window."""

    def __init__(self, kernel, parent=None):
        super().__init__("Terminal", kernel, width=750, height=500)
        self.shell = ShellCommands(kernel)
        self.command_history = []
        self.history_index = -1

        self.content.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
            }
        """)

        self.output = TerminalWidget()

        # Input bar: prompt label + text input
        input_frame = QWidget()
        input_frame.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                border-top: 1px solid #313244;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(6, 4, 4, 4)
        input_layout.setSpacing(0)

        self.prompt_label = QLabel()
        self.prompt_label.setStyleSheet("""
            QLabel {
                color: #a6e3a1;
                font-family: 'Cascadia Code', 'Fira Code', 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                font-weight: bold;
                padding-right: 4px;
            }
        """)
        font_prompt = QFont("Consolas" if sys.platform == "win32" else "Monaco", 13)
        font_prompt.setStyleHint(QFont.StyleHint.Monospace)
        font_prompt.setBold(True)
        self.prompt_label.setFont(font_prompt)

        self.input_line = QLineEdit()
        self.input_line.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                color: #cdd6f4;
                border: none;
                font-family: 'Cascadia Code', 'Fira Code', 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                padding: 4px;
            }
        """)
        font = QFont("Consolas" if sys.platform == "win32" else "Monaco", 13)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.input_line.setFont(font)
        self.input_line.setPlaceholderText("Enter command...")
        self.input_line.returnPressed.connect(self.execute_command)
        self.input_line.installEventFilter(self)

        input_layout.addWidget(self.prompt_label)
        input_layout.addWidget(self.input_line, 1)

        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addWidget(self.output)
        self.content_layout.addWidget(input_frame)

        # Focus input
        self.input_line.setFocus()

        # Print welcome
        self.print_welcome()
        self.update_prompt()

    def print_welcome(self):
        self.output.append("Welcome to VirtualOS Terminal v1.0")
        self.output.append("Type 'help' for available commands.\n")

    def update_prompt(self):
        cwd = self.shell.fs.get_cwd()
        user = self.shell.env.get("USER", "user")
        hostname = self.shell.env.get("HOSTNAME", "virtual-os")
        self.prompt_label.setText(f"{user}@{hostname}:{cwd}$ ")
        self.input_line.clear()

    def eventFilter(self, obj, event):
        if obj == self.input_line and event.type() == QKeyEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                if self.command_history and self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.input_line.setText(self.command_history[-(self.history_index + 1)])
                return True
            elif event.key() == Qt.Key.Key_Down:
                if self.history_index > 0:
                    self.history_index -= 1
                    self.input_line.setText(self.command_history[-(self.history_index + 1)])
                else:
                    self.history_index = -1
                    self.input_line.setText("")
                return True
            elif event.key() == Qt.Key.Key_Tab:
                self.tab_complete()
                return True
        return super().eventFilter(obj, event)

    def tab_complete(self):
        text = self.input_line.text()
        parts = text.split()
        if not parts:
            return
        partial = parts[-1]
        if partial.startswith("/"):
            dir_path = partial.rsplit("/", 1)[0] or "/"
            prefix = partial.rsplit("/", 1)[-1]
            success, items, _ = self.shell.fs.ls(dir_path)
            if success:
                matches = [i for i in items if i.startswith(prefix)]
                if len(matches) == 1:
                    parts[-1] = dir_path.rstrip("/") + "/" + matches[0]
                    self.input_line.setText(" ".join(parts))
                elif len(matches) > 1:
                    self.output.append(f"{'  '.join(sorted(matches))}")
        else:
            # Command completion
            commands = list(self.shell._aliases.keys()) + [
                "ls", "cd", "pwd", "cat", "touch", "mkdir", "rm", "cp", "mv",
                "echo", "find", "tree", "ps", "kill", "uname", "whoami",
                "uptime", "df", "free", "env", "export", "grep", "wc",
                "head", "tail", "sort", "uniq", "ping", "ifconfig", "clear",
                "help", "history", "date", "cal", "chmod", "hostname", "id",
                "who", "top", "du", "man", "neofetch", "cowsay",
            ]
            matches = [c for c in commands if c.startswith(partial)]
            if len(matches) == 1:
                parts[-1] = matches[0]
                self.input_line.setText(" ".join(parts))
            elif len(matches) > 1:
                self.output.append(f"{'  '.join(sorted(matches))}")

    def execute_command(self):
        cmd = self.input_line.text().strip()
        if not cmd:
            self.update_prompt()
            return

        self.command_history.append(cmd)
        self.history_index = -1

        # Show command
        self.output.append(f"{self.prompt_label.text()}{cmd}")

        # Execute
        output, exit_code = self.shell.execute(cmd)

        if output == "__CLEAR__":
            self.output.clear()
        elif output:
            self.output.append(output)

        self.update_prompt()
