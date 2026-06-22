from collections import deque

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QIcon, QAction
from PySide6.QtWidgets import QStyledItemDelegate, QLineEdit, QDialog, QDialogButtonBox, QVBoxLayout, QLabel, \
    QAbstractItemView
from PySide6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem,
    QToolBar, QMessageBox, QHeaderView, QCompleter, QComboBox
)

from utils import get_resource_path
from widgets.tag_completer import CUSTOM_ROLE, MAX_COMPLETION_ITEMS, TagListModel


class CenterPanel(QWidget):
    tags_modified = Signal(str)
    translation_edited_from_center = Signal(str, str)
    find_requested = Signal(str)
    request_adjust_columns = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_image = None
        self.current_file = None
        self.undo_stack = deque(maxlen=20)
        self.completer = None
        self.completer_proxy = None
        self.get_translation_callback = None
        self._init_ui()

    def set_toolbar_style(self, style):
        """style: 'icons' 或 'text'"""
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
                # 如果是图标模式，保留 tooltip 显示原文字
                if style == "icons":
                    widget.setToolTip(action.text())
                else:
                    widget.setToolTip("")

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.toolbar = QToolBar()
        self.add_action = QAction(QIcon(get_resource_path("icons/plus.svg")), "添加标签", self)
        self.add_action.triggered.connect(self.add_tag)
        self.toolbar.addAction(self.add_action)

        self.del_action = QAction(QIcon(get_resource_path("icons/times.svg")), "删除标签", self)
        self.del_action.triggered.connect(self.delete_tags)
        self.toolbar.addAction(self.del_action)

        self.toolbar.addSeparator()

        self.undo_action = QAction(QIcon(get_resource_path("icons/undo.svg")), "撤销", self)
        self.undo_action.triggered.connect(self.undo)
        self.toolbar.addAction(self.undo_action)

        self.toolbar.addSeparator()

        self.find_action = QAction(QIcon(get_resource_path("icons/search.svg")), "查找标签", self)
        self.find_action.triggered.connect(self.find_tag)
        self.toolbar.addAction(self.find_action)

        layout.addWidget(self.toolbar)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["标签", "翻译"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # 初始宽度由 main.py 恢复或均分，这里不设固定值
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setWordWrap(True)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.table.keyPressEvent = self.table_key_press_event
        layout.addWidget(self.table)

        self.completer = QCompleter()
        self.completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)  # 不再实际起作用
        self.completer.setCompletionRole(CUSTOM_ROLE)  # 填入表格时只填纯 tag
        self.completer.setMaxVisibleItems(7)  # 弹出窗口最多显示7行
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # 标签列（第0列）的代理，双击编辑时自动带补全
        class TagDelegate(QStyledItemDelegate):
            def __init__(self, completer, filter_func, parent=None):
                super().__init__(parent)
                self.completer = completer
                self.filter_func = filter_func

            def createEditor(self, parent, option, index):
                editor = QLineEdit(parent)
                editor.setCompleter(self.completer)
                editor.setProperty("completing", False)

                def on_text_changed(text):
                    if editor.property("completing"):
                        editor.setProperty("completing", False)
                        return
                    self.filter_func(text)

                editor.textChanged.connect(on_text_changed)

                # 补全选中的槽（回车/点击）
                def on_activated(text):
                    editor.setProperty("completing", True)
                    self.commitData.emit(editor)
                    self.closeEditor.emit(editor, QStyledItemDelegate.NoHint)

                # 高亮导航的槽（上下键）
                def on_highlighted(text):
                    editor.setProperty("completing", True)

                self.completer.activated.connect(on_activated)
                self.completer.highlighted.connect(on_highlighted)

                # 编辑器销毁时，使用槽函数对象断开连接
                editor.destroyed.connect(
                    lambda: (
                        self.completer.activated.disconnect(on_activated),
                        self.completer.highlighted.disconnect(on_highlighted)
                    )
                )
                return editor

        self.table.setItemDelegateForColumn(0, TagDelegate(self.completer, self.filter_completer))

    def filter_completer(self, text):
        """根据输入文本，生成最多20个匹配项的模型，替换给 completer"""
        if not hasattr(self, 'all_tags') or self.all_tags is None:
            return
        text_lower = text.lower().strip()
        matched = []
        for tag in self.all_tags:
            if text_lower in tag.lower():
                matched.append(tag)
                if len(matched) >= MAX_COMPLETION_ITEMS:
                    break
        new_model = TagListModel(matched, self.get_translation_callback)
        self.completer.setModel(new_model)

    def set_current_image(self, filename, image_data):
        self.current_file = filename
        self.current_image = image_data
        self.undo_stack.clear()
        self.refresh_table()

    def refresh_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        if self.current_image is None:
            self.table.blockSignals(False)
            return
        for i, tag in enumerate(self.current_image.tags):
            self._add_row(i, tag)
        self.table.resizeRowsToContents()   # 自动调整行高以显示全部内容
        self.table.blockSignals(False)
        self.request_adjust_columns.emit()

    def clear_completer_cache(self):
        if hasattr(self, 'completer_source_model'):
            self.completer_source_model.clear_cache()

    def _add_row(self, row, tag):
        self.table.insertRow(row)
        item_tag = QTableWidgetItem(tag)
        item_tag.setFlags(item_tag.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, item_tag)

        translation = ""
        if self.get_translation_callback:
            translation = self.get_translation_callback(tag)
        item_trans = QTableWidgetItem(translation)
        self.table.setItem(row, 1, item_trans)

    def on_cell_changed(self, row, col):
        if col == 0:
            new_tag = self.table.item(row, col).text().strip()
            if not new_tag:
                return
            old_tags = list(self.current_image.tags)
            if row < len(old_tags):
                self._push_undo()
                old_tags[row] = new_tag
                self.current_image.tags = old_tags
                # 立即更新该行的翻译列
                trans = ""
                if self.get_translation_callback:
                    trans = self.get_translation_callback(new_tag)
                trans_item = self.table.item(row, 1)
                if trans_item:
                    self.table.blockSignals(True)
                    trans_item.setText(trans)
                    self.table.blockSignals(False)
                self.tags_modified.emit(self.current_file)
        elif col == 1:
            tag_item = self.table.item(row, 0)
            trans_item = self.table.item(row, 1)
            if tag_item and trans_item:
                tag = tag_item.text().strip()
                new_trans = trans_item.text().strip()
                self.translation_edited_from_center.emit(tag, new_trans)
        self.table.resizeRowToContents(row)

    def _push_undo(self):
        if self.current_image:
            self.undo_stack.append(list(self.current_image.tags))

    def undo(self):
        if not self.undo_stack:
            return
        tags = self.undo_stack.pop()
        self.current_image.tags = tags
        self.refresh_table()
        self.tags_modified.emit(self.current_file)

    def add_tag(self):
        if not self.current_image:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("添加标签")
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("选择添加位置："))
        pos_combo = QComboBox()
        pos_combo.addItems(["top (开头)", "next (选中之后)", "down (末尾)"])
        pos_combo.setCurrentIndex(1)
        layout.addWidget(pos_combo)

        layout.addWidget(QLabel("输入标签："))
        line_edit = QLineEdit()
        line_edit.setCompleter(self.completer)
        line_edit.setProperty("completing", False)

        def on_text(text):
            if line_edit.property("completing"):
                line_edit.setProperty("completing", False)
                return
            self.filter_completer(text)

        line_edit.textChanged.connect(on_text)

        def on_act(text):
            line_edit.setProperty("completing", True)

        def on_hl(text):
            line_edit.setProperty("completing", True)

        self.completer.activated.connect(on_act)
        self.completer.highlighted.connect(on_hl)

        # 对话框关闭时 line_edit 销毁，用槽函数断开连接
        line_edit.destroyed.connect(
            lambda: (
                self.completer.activated.disconnect(on_act),
                self.completer.highlighted.disconnect(on_hl)
            )
        )

        layout.addWidget(line_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.Accepted:
            return

        tag = line_edit.text().strip()
        # 获取用户选择的位置策略
        pos_str = pos_combo.currentText()

        self._push_undo()
        tags = self.current_image.tags

        if pos_str.startswith("top"):
            tags.insert(0, tag)
        elif pos_str.startswith("next"):
            selected = list(set(item.row() for item in self.table.selectedItems()))
            insert_at = min(selected) + 1 if selected else len(tags)
            if insert_at > len(tags):
                insert_at = len(tags)
            tags.insert(insert_at, tag)
        else:  # down
            tags.append(tag)

        self.refresh_table()
        self.tags_modified.emit(self.current_file)

    def delete_tags(self):
        if not self.current_image:
            return
        rows = sorted(set(item.row() for item in self.table.selectedItems()))
        if not rows:
            return
        # 记录第一个被删行的位置
        first_deleted = rows[0]
        self._push_undo()
        new_tags = [t for i, t in enumerate(self.current_image.tags) if i not in rows]
        self.current_image.tags = new_tags
        self.refresh_table()
        # 恢复选择：定位到 first_deleted 之后的行，若超出范围则选最后一行
        if new_tags:
            target_row = first_deleted
            if target_row >= len(new_tags):
                target_row = len(new_tags) - 1
            self.table.selectRow(target_row)

        self.tags_modified.emit(self.current_file)

    def move_tag_up(self):
        self._move_tag(-1)

    def move_tag_down(self):
        self._move_tag(1)

    def _move_tag(self, offset):
        rows = sorted(set(item.row() for item in self.table.selectedItems()))
        if not rows or not self.current_image:
            return
        tags = self.current_image.tags
        self._push_undo()
        for r in rows:
            new_pos = r + offset
            if 0 <= new_pos < len(tags):
                tags[r], tags[new_pos] = tags[new_pos], tags[r]
        self.current_image.tags = tags
        self.refresh_table()
        new_rows = [min(max(r + offset, 0), len(tags)-1) for r in rows]
        self.table.clearSelection()
        for r in new_rows:
            self.table.selectRow(r)
        self.tags_modified.emit(self.current_file)

    def find_tag(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中一个标签")
            return
        tag_item = self.table.item(row, 0)
        if tag_item:
            self.find_requested.emit(tag_item.text().strip())

    def build_completer(self, sorted_tags):
        self.all_tags = sorted_tags  # 保存起来，供过滤使用
        # 可选：初始化一个前20的模型，避免首次弹出空列表
        self.filter_completer('')

    def table_key_press_event(self, event):
        """处理表格的快捷键"""
        if event.key() == Qt.Key.Key_Delete:
            self.delete_tags()
        elif event.key() == Qt.Key.Key_Left and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            if self.table.hasFocus():
                self.move_tag_up()
                return
        elif event.key() == Qt.Key.Key_Right and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            if self.table.hasFocus():
                self.move_tag_down()
                return
        elif event.matches(QKeySequence.StandardKey.Undo):
            self.undo()
            return
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.table.state() == QAbstractItemView.State.EditingState:
                # 正在编辑中，交给默认处理（提交并关闭编辑器）
                super(QTableWidget, self.table).keyPressEvent(event)
                return
            if self.table.hasFocus() and self.table.currentItem() is not None:
                self.table.editItem(self.table.currentItem())
                return
        super(QTableWidget, self.table).keyPressEvent(event)

    # 设置翻译回调
    def set_translation_callback(self, cb):
        self.get_translation_callback = cb