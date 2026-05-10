"""Memory Monitor Window."""
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from gui.window import BaseWindow


class MemoryMonitorWindow(BaseWindow):
    """Memory monitor application window."""

    def __init__(self, kernel, parent=None):
        super().__init__("Memory Monitor", kernel, width=700, height=500)

        # Overall usage bar
        usage_frame = self._create_usage_frame()
        self.content_layout.addWidget(usage_frame)

        # Stats grid
        stats_frame = self._create_stats_frame()
        self.content_layout.addWidget(stats_frame)

        # Process memory table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["PID", "Process", "Memory (KB)", "% of Total"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: none;
                gridline-color: #313244;
                font-size: 12px;
                margin-top: 8px;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cdd6f4;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.content_layout.addWidget(self.table)

        # Auto refresh
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)

        self.refresh()

    def _create_usage_frame(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border-radius: 8px;
                padding: 12px;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 14px;
            }
            QLabel#usage_title {
                font-size: 16px;
                font-weight: bold;
                color: #89b4fa;
            }
            QProgressBar {
                background-color: #1e1e2e;
                border: none;
                border-radius: 6px;
                height: 24px;
                text-align: center;
                color: #cdd6f4;
                font-size: 12px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                border-radius: 6px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #a6e3a1, stop:0.5 #94e2d5, stop:1 #89b4fa);
            }
        """)
        layout = QVBoxLayout(frame)

        title = QLabel("Memory Usage")
        title.setObjectName("usage_title")
        layout.addWidget(title)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        return frame

    def _create_stats_frame(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                padding: 8px 0;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 13px;
            }
            QLabel#stat_value {
                color: #89b4fa;
                font-weight: bold;
                font-size: 18px;
            }
            QLabel#stat_label {
                color: #a6adc8;
                font-size: 11px;
            }
        """)
        layout = QHBoxLayout(frame)

        self.total_label = QLabel("0 MB", objectName="stat_value")
        self.used_label = QLabel("0 MB", objectName="stat_value")
        self.free_label = QLabel("0 MB", objectName="stat_value")
        self.percent_label = QLabel("0%", objectName="stat_value")

        for label, text in [
            (self.total_label, "Total"),
            (self.used_label, "Used"),
            (self.free_label, "Free"),
            (self.percent_label, "Usage"),
        ]:
            col = QVBoxLayout()
            value_label = label
            name_label = QLabel(text)
            name_label.setObjectName("stat_label")
            col.addWidget(value_label)
            col.addWidget(name_label)
            layout.addLayout(col)

        layout.addStretch()
        return frame

    def refresh(self):
        usage = self.kernel.memory_manager.get_usage()
        total_mb = usage["total"] // 1024
        used_mb = usage["used"] // 1024
        free_mb = usage["free"] // 1024
        percent = int(usage["usage_percent"])

        self.progress.setValue(percent)
        self.total_label.setText(f"{total_mb} MB")
        self.used_label.setText(f"{used_mb} MB")
        self.free_label.setText(f"{free_mb} MB")
        self.percent_label.setText(f"{percent}%")

        # Color based on usage
        if percent > 80:
            self.progress.setStyleSheet("""
                QProgressBar::chunk {
                    border-radius: 6px;
                    background: #f38ba8;
                }
            """)
        elif percent > 60:
            self.progress.setStyleSheet("""
                QProgressBar::chunk {
                    border-radius: 6px;
                    background: #fab387;
                }
            """)

        # Process memory table
        breakdown = self.kernel.memory_manager.get_process_breakdown()
        self.table.setRowCount(len(breakdown))
        for i, (pid, info) in enumerate(sorted(breakdown.items())):
            mem_pct = (info["total"] / usage["total"]) * 100
            self.table.setItem(i, 0, QTableWidgetItem(str(pid)))
            self.table.setItem(i, 1, QTableWidgetItem(info["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(str(info["total"])))
            self.table.setItem(i, 3, QTableWidgetItem(f"{mem_pct:.1f}%"))
