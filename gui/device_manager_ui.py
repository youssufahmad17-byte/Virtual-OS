"""Device Manager Window."""
from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QSplitter, QTextEdit, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from gui.window import BaseWindow


class DeviceManagerWindow(BaseWindow):
    """Device manager application window."""

    def __init__(self, kernel, parent=None):
        super().__init__("Device Manager", kernel, width=800, height=550)

        # Stats bar
        stats_bar = self._create_stats_bar()
        self.content_layout.addWidget(stats_bar)

        # Main content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Device tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Device", "Status"])
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: none;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #313244;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cdd6f4;
                padding: 6px;
                border: none;
            }
        """)
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tree.currentItemChanged.connect(self._on_device_selected)
        splitter.addWidget(self.tree)

        # Device details panel
        details_panel = self._create_details_panel()
        splitter.addWidget(details_panel)

        splitter.setSizes([450, 350])
        self.content_layout.addWidget(splitter)

        # Action buttons
        btn_bar = self._create_action_bar()
        self.content_layout.addWidget(btn_bar)

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
        """)
        bar_layout = QHBoxLayout(bar)

        self.total_label = QLabel("")
        self.online_label = QLabel("")

        bar_layout.addWidget(self.total_label)
        bar_layout.addWidget(self.online_label)
        bar_layout.addStretch()

        return bar

    def _create_details_panel(self):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #181825;
                border-left: 1px solid #313244;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 13px;
                padding: 4px;
            }
            QLabel#title {
                color: #89b4fa;
                font-size: 16px;
                font-weight: bold;
                padding: 8px;
            }
            QLabel#label {
                color: #a6adc8;
                font-weight: bold;
            }
            QLabel#value {
                color: #cdd6f4;
            }
        """)
        layout = QVBoxLayout(panel)

        self.title_label = QLabel("Device Details")
        self.title_label.setObjectName("title")
        layout.addWidget(self.title_label)

        self.details_layout = QVBoxLayout()
        layout.addLayout(self.details_layout)
        layout.addStretch()

        self.detail_labels = {}
        return panel

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
            QPushButton#enableBtn {
                background-color: #a6e3a1;
                color: #1e1e2e;
            }
            QPushButton#disableBtn {
                background-color: #f38ba8;
                color: #1e1e2e;
            }
        """)
        bar_layout = QHBoxLayout(bar)

        self.enable_btn = QPushButton("Enable Device")
        self.enable_btn.setObjectName("enableBtn")
        self.enable_btn.clicked.connect(self._enable_device)

        self.disable_btn = QPushButton("Disable Device")
        self.disable_btn.setObjectName("disableBtn")
        self.disable_btn.clicked.connect(self._disable_device)

        bar_layout.addWidget(self.enable_btn)
        bar_layout.addWidget(self.disable_btn)
        bar_layout.addStretch()

        return bar

    def refresh(self):
        self.tree.clear()
        categories = self.kernel.device_manager.get_categories()
        online = 0

        for cat_name, devices in sorted(categories.items()):
            cat_item = QTreeWidgetItem(self.tree)
            cat_item.setText(0, cat_name)
            cat_item.setExpanded(True)

            for dev in devices:
                dev_item = QTreeWidgetItem(cat_item)
                dev_item.setText(0, dev.name)
                status_icon = {"Online": "●", "Disabled": "○", "Error": "✕", "Offline": "○"}
                status = dev.state if dev.enabled else "Disabled"
                dev_item.setText(1, f"{status_icon.get(status, '●')} {status}")

                if status == "Online":
                    dev_item.setForeground(1, QColor("#a6e3a1"))
                    online += 1
                elif status == "Disabled":
                    dev_item.setForeground(1, QColor("#f38ba8"))
                elif status == "Error":
                    dev_item.setForeground(1, QColor("#fab387"))

                dev_item.setData(0, Qt.ItemDataRole.UserRole, dev)

        self.total_label.setText(f"Total Devices: {self.kernel.device_manager.get_device_count()}")
        self.online_label.setText(f"Online: {online}")

    def _on_device_selected(self, current, previous):
        if not current:
            return
        dev = current.data(0, Qt.ItemDataRole.UserRole)
        if not dev:
            return

        self.title_label.setText(dev.name)

        # Clear old details
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        details = [
            ("Category:", dev.category),
            ("Driver:", dev.driver),
            ("Status:", dev.state),
            ("Enabled:", "Yes" if dev.enabled else "No"),
            ("Vendor:", dev.vendor),
            ("Bus:", dev.bus),
        ]

        for key, value in details:
            label = QLabel(f"{key}  {value}")
            label.setObjectName("value" if not key.endswith(":") else "label")
            self.details_layout.addWidget(label)

        if dev.properties:
            props_label = QLabel("\nProperties:")
            props_label.setObjectName("label")
            self.details_layout.addWidget(props_label)
            for k, v in dev.properties.items():
                label = QLabel(f"  {k}:  {v}")
                label.setObjectName("value")
                self.details_layout.addWidget(label)

    def _enable_device(self):
        items = self.tree.selectedItems()
        if items:
            dev = items[0].data(0, Qt.ItemDataRole.UserRole)
            if dev:
                self.kernel.device_manager.enable_device(dev.name)
                self.refresh()

    def _disable_device(self):
        items = self.tree.selectedItems()
        if items:
            dev = items[0].data(0, Qt.ItemDataRole.UserRole)
            if dev:
                self.kernel.device_manager.disable_device(dev.name)
                self.refresh()
