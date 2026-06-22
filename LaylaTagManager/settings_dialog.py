from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QIcon
from PySide6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QSpinBox, QLabel,
    QTableWidget, QTableWidgetItem, QDialogButtonBox, QKeySequenceEdit, QComboBox
)

from utils import get_resource_path

class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setWindowIcon(QIcon(get_resource_path("icons/logo.png")))
        self.config = config.copy()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # 界面选项卡
        tab_ui = QWidget()
        ui_layout = QVBoxLayout(tab_ui)
        ui_layout.addWidget(QLabel("默认字号:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 24)
        self.font_spin.setValue(self.config.get("font_size", 9))
        ui_layout.addWidget(self.font_spin)

        # 与上方字号控件留一点间距
        ui_layout.addSpacing(8)

        ui_layout.addWidget(QLabel("工具栏样式:"))
        self.style_combo = QComboBox()
        self.style_combo.addItem("图标", "icons")
        self.style_combo.addItem("文字", "text")
        current_style = self.config.get("toolbar_style", "icons")
        index = self.style_combo.findData(current_style)
        if index >= 0:
            self.style_combo.setCurrentIndex(index)
        ui_layout.addWidget(self.style_combo)

        # 将剩余空间推到下方（保证整体靠上）
        ui_layout.addStretch()
        tabs.addTab(tab_ui, "界面")

        # 快捷键选项卡
        tab_keys = QWidget()
        keys_layout = QVBoxLayout(tab_keys)
        self.key_table = QTableWidget(0, 2)
        self.key_table.setHorizontalHeaderLabels(["操作", "快捷键"])
        self.key_table.horizontalHeader().setStretchLastSection(True)
        self._populate_shortcuts()
        keys_layout.addWidget(self.key_table)
        tabs.addTab(tab_keys, "快捷键")

        layout.addWidget(tabs)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._apply_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_shortcuts(self):
        shortcuts = self.config.get("shortcuts", {})
        self.key_table.setRowCount(len(shortcuts))
        for i, (name, key) in enumerate(shortcuts.items()):
            item_name = QTableWidgetItem(name)
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.key_table.setItem(i, 0, item_name)
            editor = QKeySequenceEdit(QKeySequence(key))
            editor.editingFinished.connect(lambda e=editor, r=i: self._on_key_changed(r, e))
            self.key_table.setCellWidget(i, 1, editor)

    def _on_key_changed(self, row, editor):
        seq = editor.keySequence().toString()
        if not seq:
            return
        name = self.key_table.item(row, 0).text()
        self.config["shortcuts"][name] = seq

    def _apply_and_accept(self):
        self.config["font_size"] = self.font_spin.value()
        self.config["toolbar_style"] = self.style_combo.currentData()
        self.accept()