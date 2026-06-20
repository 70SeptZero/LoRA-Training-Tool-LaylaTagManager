from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QToolBar, QHeaderView, QMenu, QMessageBox, QDialogButtonBox, QDialog, QLabel, QLineEdit, QComboBox,
    QHBoxLayout, QSpinBox
)

from utils import get_resource_path


class RightPanel(QWidget):
    request_reload = Signal()
    filter_requested = Signal(str)
    clear_filter = Signal()
    translation_changed = Signal(str, str)
    request_adjust_columns = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.metadata = {}
        self.current_sort = 'frequency_desc'
        self.all_images = {}
        self._init_ui()
        self.completer = None
        self.filter_completer_func = None

    def setup_completer(self, completer, filter_func):
        """设置补全器和过滤回调（由主窗口调用）"""
        self.completer = completer
        self.filter_completer_func = filter_func

    def set_toolbar_style(self, style):
        if style == "icons":
            button_style = Qt.ToolButtonStyle.ToolButtonIconOnly
        else:
            button_style = Qt.ToolButtonStyle.ToolButtonTextOnly

        for action in self.toolbar.actions():
            if action.isSeparator():
                continue
            widget = self.toolbar.widgetForAction(action)
            if widget:
                widget.setToolButtonStyle(button_style)
                if style == "icons":
                    widget.setToolTip(action.text())
                else:
                    widget.setToolTip("")

        # 处理排序按钮（是 QToolButton，不是 QAction）
        if hasattr(self, 'sort_btn'):
            self.sort_btn.setToolButtonStyle(button_style)
            if style == "icons":
                self.sort_btn.setToolTip("排序方式")
            else:
                self.sort_btn.setToolTip("")

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.toolbar = QToolBar()
        self.add_all_action = QAction(QIcon(get_resource_path("icons/plus.svg")), "为所有图片添加标签", self)
        self.add_all_action.triggered.connect(self.add_tag_to_all)
        self.toolbar.addAction(self.add_all_action)
        self.del_all_action = QAction(QIcon(get_resource_path("icons/times.svg")), "删除该标签", self)
        self.del_all_action.triggered.connect(self.delete_tag_from_all)
        self.toolbar.addAction(self.del_all_action)
        self.replace_action = QAction(QIcon(get_resource_path("icons/switch.svg")), "替换该标签", self)
        self.replace_action.triggered.connect(self.replace_tag)

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.replace_action)
        self.filter_action = QAction(QIcon(get_resource_path("icons/search.svg")), "筛选拥有该标签的图片", self)
        self.filter_action.triggered.connect(self.filter_by_tag)
        self.toolbar.addAction(self.filter_action)
        self.exit_filter_action = QAction(QIcon(get_resource_path("icons/search-minus.svg")), "退出筛选模式", self)
        self.exit_filter_action.triggered.connect(self.exit_filter)
        self.toolbar.addAction(self.exit_filter_action)

        self.toolbar.addSeparator()

        self.sort_menu = QMenu("排序方式")
        sort_actions = [
            ("频率↓", "frequency_desc"),
            ("频率↑", "frequency_asc"),
            ("字母↑", "alpha_asc"),
            ("字母↓", "alpha_desc"),
        ]
        for text, key in sort_actions:
            act = QAction(text, self)
            act.triggered.connect(lambda checked, k=key: self.set_sort(k))
            self.sort_menu.addAction(act)
        self.toolbar.addAction(self.sort_menu.menuAction())
        layout.addWidget(self.toolbar)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["标签", "翻译", "频率"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.setWordWrap(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.table.doubleClicked.connect(self.on_double_clicked)
        layout.addWidget(self.table)

    def load_metadata(self, metadata):
        self.metadata = metadata
        self.refresh_table()

    def set_images_reference(self, images_dict):
        self.all_images = images_dict

    def refresh_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        items = list(self.metadata.items())
        if self.current_sort == 'frequency_desc':
            items.sort(key=lambda x: (-x[1]['frequency'], x[0].lower()))
        elif self.current_sort == 'frequency_asc':
            items.sort(key=lambda x: (x[1]['frequency'], x[0].lower()))
        elif self.current_sort == 'alpha_desc':
            items.sort(key=lambda x: x[0].lower(), reverse=True)
        elif self.current_sort == 'alpha_asc':
            items.sort(key=lambda x: x[0].lower())

        for row, (tag, info) in enumerate(items):
            self.table.insertRow(row)
            item_tag = QTableWidgetItem(tag)
            item_tag.setFlags(item_tag.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, item_tag)
            item_trans = QTableWidgetItem(info.get('translation', ''))
            self.table.setItem(row, 1, item_trans)
            item_freq = QTableWidgetItem(str(info.get('frequency', 0)))
            item_freq.setFlags(item_freq.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, item_freq)
        self.table.resizeRowsToContents()   # 自动行高
        self.table.blockSignals(False)
        self.request_adjust_columns.emit()

    def on_cell_changed(self, row, col):
        if col != 1:
            return
        tag_item = self.table.item(row, 0)
        trans_item = self.table.item(row, 1)
        if tag_item and trans_item:
            tag = tag_item.text().strip()
            new_trans = trans_item.text().strip()
            if tag in self.metadata:
                self.metadata[tag]['translation'] = new_trans
                self.translation_changed.emit(tag, new_trans)
        self.table.resizeRowToContents(row)

    def on_double_clicked(self, index):
        if index.column() == 0:
            tag = self.table.item(index.row(), 0).text()
            if hasattr(self, 'add_to_current_callback'):
                self.add_to_current_callback(tag)

    def add_tag_to_all(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("给所有图片添加标签")
        layout = QVBoxLayout(dlg)

        layout.addWidget(QLabel("选择添加位置："))
        pos_combo = QComboBox()
        pos_combo.addItems(["top (开头)", "down (末尾)", "custom (自定义位置)"])
        pos_combo.setCurrentIndex(1)
        layout.addWidget(pos_combo)

        idx_widget = QWidget()
        idx_layout = QHBoxLayout(idx_widget)
        idx_layout.setContentsMargins(0, 0, 0, 0)
        idx_layout.addWidget(QLabel("插入索引 (1=开头)："))
        idx_spin = QSpinBox()
        idx_spin.setRange(1, 10000)
        idx_spin.setValue(1)
        idx_layout.addWidget(idx_spin)
        idx_widget.setVisible(False)
        layout.addWidget(idx_widget)

        layout.addWidget(QLabel("输入标签："))
        tag_edit = QLineEdit()

        # ----- 补全逻辑（与 add_tag 对话框一致）-----
        if self.completer is not None:
            tag_edit.setCompleter(self.completer)
            tag_edit.setProperty("completing", False)

            def on_text(text):
                if tag_edit.property("completing"):
                    tag_edit.setProperty("completing", False)
                    return
                if self.filter_completer_func:
                    self.filter_completer_func(text)

            tag_edit.textChanged.connect(on_text)

            def on_act(text):
                tag_edit.setProperty("completing", True)

            def on_hl(text):
                tag_edit.setProperty("completing", True)

            self.completer.activated.connect(on_act)
            self.completer.highlighted.connect(on_hl)

            tag_edit.destroyed.connect(
                lambda: (
                    self.completer.activated.disconnect(on_act),
                    self.completer.highlighted.disconnect(on_hl)
                )
            )
        # --------------------------------------------

        layout.addWidget(tag_edit)

        def on_pos_changed(text):
            idx_widget.setVisible(text.startswith("custom"))

        pos_combo.currentTextChanged.connect(on_pos_changed)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.Accepted:
            return

        tag = tag_edit.text().strip()
        if not tag:
            return

        pos_str = pos_combo.currentText()
        idx = idx_spin.value() - 1

        for img in self.all_images.values():
            if pos_str.startswith("top"):
                img.tags.insert(0, tag)
            elif pos_str.startswith("down"):
                img.tags.append(tag)
            else:
                ins = min(idx, len(img.tags))
                img.tags.insert(ins, tag)

        self.request_reload.emit()

    def delete_tag_from_all(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一个标签")
            return
        tag = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认", f"确定从所有图片删除标签'{tag}'吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for img in self.all_images.values():
                img.tags = [t for t in img.tags if t != tag]
            self.request_reload.emit()

    def replace_tag(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一个标签")
            return
        old_tag = self.table.item(row, 0).text().strip()

        dlg = QDialog(self)
        dlg.setWindowTitle("替换标签")
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel(f"将 '{old_tag}' 替换为:"))
        new_edit = QLineEdit()

        # ----- 补全逻辑 -----
        if self.completer is not None:
            new_edit.setCompleter(self.completer)
            new_edit.setProperty("completing", False)

            def on_text(text):
                if new_edit.property("completing"):
                    new_edit.setProperty("completing", False)
                    return
                if self.filter_completer_func:
                    self.filter_completer_func(text)

            new_edit.textChanged.connect(on_text)

            def on_act(text):
                new_edit.setProperty("completing", True)

            def on_hl(text):
                new_edit.setProperty("completing", True)

            self.completer.activated.connect(on_act)
            self.completer.highlighted.connect(on_hl)

            new_edit.destroyed.connect(
                lambda: (
                    self.completer.activated.disconnect(on_act),
                    self.completer.highlighted.disconnect(on_hl)
                )
            )
        # --------------------

        layout.addWidget(new_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.Accepted:
            return

        new_tag = new_edit.text().strip()
        if not new_tag:
            return
        for img in self.all_images.values():
            img.tags = [new_tag if t == old_tag else t for t in img.tags]
        self.request_reload.emit()

    def filter_by_tag(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一个标签")
            return
        tag = self.table.item(row, 0).text()
        self.filter_requested.emit(tag)

    def exit_filter(self):
        self.clear_filter.emit()

    def set_sort(self, sort_key):
        self.current_sort = sort_key
        self.refresh_table()

    def find_and_select(self, search_text):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text().lower() == search_text.lower():
                self.table.selectRow(row)
                self.table.scrollToItem(item)
                return True
        return False