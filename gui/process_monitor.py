"""Process Monitor Window - Task Manager."""
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QHeaderView, QFrame, QWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from gui.window import BaseWindow


class ProcessMonitorWindow(BaseWindow):
    """Process monitor / task manager window."""

    def __init__(self, kernel, parent=None):
        super().__init__("Process Monitor", kernel, width=800, height=500)

        # Stats bar
        stats_bar = self._create_stats_bar()
        self.content_layout.addWidget(stats_bar)

        # Process table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["PID", "PPID", "User", "State", "Memory (KB)", "CPU Time", "Threads", "Command"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: none;
                gridline-color: #313244;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cdd6f4;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #45475a;
                font-weight: bold;
            }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.content_layout.addWidget(self.table)

        # Action buttons
        btn_bar = self._create_action_bar()
        self.content_layout.addWidget(btn_bar)

        # Auto refresh
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)

        self.refresh()

    def _create_stats_bar(self):
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border-bottom: 1px solid #45475a;
                padding: 6px;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 13px;
                padding: 2px 8px;
            }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
        """)
        bar_layout = QHBoxLayout(bar)

        self.total_label = QLabel("Total: 0")
        self.running_label = QLabel("Running: 0")
        self.sleeping_label = QLabel("Sleeping: 0")
        self.cpu_label = QLabel("CPU: 0%")
        self.mem_label = QLabel("Memory: 0 MB")

        bar_layout.addWidget(self.total_label)
        bar_layout.addWidget(self.running_label)
        bar_layout.addWidget(self.sleeping_label)
        bar_layout.addStretch()
        bar_layout.addWidget(self.cpu_label)
        bar_layout.addWidget(self.mem_label)

        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.clicked.connect(self.refresh)
        bar_layout.addWidget(refresh_btn)

        return bar

    def _create_action_bar(self):
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border-top: 1px solid #45475a;
                padding: 6px;
            }
            QPushButton {
                padding: 6px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#killBtn {
                background-color: #f38ba8;
                color: #1e1e2e;
            }
            QPushButton#killBtn:hover {
                background-color: #eba0ac;
            }
            QPushButton#stopBtn {
                background-color: #fab387;
                color: #1e1e2e;
            }
            QPushButton#stopBtn:hover {
                background-color: #f9e2af;
            }
            QPushButton#resumeBtn {
                background-color: #a6e3a1;
                color: #1e1e2e;
            }
            QPushButton#resumeBtn:hover {
                background-color: #94e2d5;
            }
        """)
        bar_layout = QHBoxLayout(bar)

        kill_btn = QPushButton("Kill Process")
        kill_btn.setObjectName("killBtn")
        kill_btn.clicked.connect(self._kill_selected)

        stop_btn = QPushButton("Stop Process")
        stop_btn.setObjectName("stopBtn")
        stop_btn.clicked.connect(self._stop_selected)

        resume_btn = QPushButton("Resume Process")
        resume_btn.setObjectName("resumeBtn")
        resume_btn.clicked.connect(self._resume_selected)

        bar_layout.addWidget(kill_btn)
        bar_layout.addWidget(stop_btn)
        bar_layout.addWidget(resume_btn)
        bar_layout.addStretch()

        return bar

    def refresh(self):
        self.kernel.update()
        procs = self.kernel.process_manager.get_all_processes()
        self.table.setRowCount(len(procs))

        total = len(procs)
        running = sum(1 for p in procs if p.state == "Running")
        sleeping = sum(1 for p in procs if p.state == "Sleeping")
        total_mem = self.kernel.process_manager.get_total_memory() // 1024

        self.total_label.setText(f"Total: {total}")
        self.running_label.setText(f"Running: {running}")
        self.sleeping_label.setText(f"Sleeping: {sleeping}")
        self.cpu_label.setText(f"CPU: {min(100, int(self.kernel.process_manager.get_total_cpu()))}%")
        self.mem_label.setText(f"Memory: {total_mem} MB")

        for i, proc in enumerate(procs):
            state_color = {
                "Running": "#a6e3a1",
                "Sleeping": "#89b4fa",
                "Stopped": "#fab387",
                "Zombie": "#f38ba8",
            }
            items = [
                str(proc.pid),
                str(proc.ppid),
                proc.user,
                proc.state,
                str(proc.memory),
                f"{proc.cpu_time:.2f}s",
                str(proc.threads),
                proc.command,
            ]
            for j, text in enumerate(items):
                item = QTableWidgetItem(text)
                if j == 3:  # State column
                    item.setForeground(QColor(state_color.get(proc.state, "#cdd6f4")))
                self.table.setItem(i, j, item)

    def _get_selected_pid(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            pid_item = self.table.item(row, 0)
            if pid_item:
                return int(pid_item.text())
        return None

    def _kill_selected(self):
        pid = self._get_selected_pid()
        if pid:
            success, error = self.kernel.process_manager.kill_process(pid)
            if success:
                self.kernel.memory_manager.free(pid)
                self.refresh()

    def _stop_selected(self):
        pid = self._get_selected_pid()
        if pid:
            success, error = self.kernel.process_manager.stop_process(pid)
            if not success:
                pass  # Silently fail
            self.refresh()

    def _resume_selected(self):
        pid = self._get_selected_pid()
        if pid:
            success, error = self.kernel.process_manager.resume_process(pid)
            if not success:
                pass
            self.refresh()
