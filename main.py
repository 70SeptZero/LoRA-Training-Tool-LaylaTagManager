import json
import os
import sys

from PySide6.QtCore import Qt, QByteArray, QTimer
from PySide6.QtGui import QKeySequence, QIcon, QFontMetrics, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QSplitter,
    QMessageBox, QDialog
)

from settings_dialog import SettingsDialog
from utils import (
    scan_folder, load_tag_metadata, load_custom_tags, save_custom_tags,
    compute_tag_frequencies, generate_thumbnail, get_base_path, get_resource_path
)
from widgets.center_panel import CenterPanel
from widgets.left_panel import LeftPanel
from widgets.right_panel import RightPanel


class MainWindow(QMainWindow):
    CONFIG_FILE = "config.json"

    def __init__(self):
        super().__init__()
        self.CONFIG_FILE = os.path.join(get_base_path(), "config.json")
        # tags 文件夹位于 exe 同目录
        self.tags_dir = os.path.join(get_base_path(), "tags")
        os.makedirs(self.tags_dir, exist_ok=True)
        self.setWindowTitle("LaylaTagManager")
        self.setWindowIcon(QIcon(get_resource_path("icons/logo.png")))
        self.resize(1400, 800)
        self.config = self.load_config()
        self.last_opened_folder = self.config.get("last_folder", "")
        self.custom_tags = {}
        self.standard_tags_set = set()
        self.images = {}
        self.current_file = None
        self.folder_path = None

        font = QApplication.font()
        font.setPointSize(self.config.get("font_size", 9))
        QApplication.setFont(font)

        self._create_menu()
        self._create_panels()
        self._connect_signals()
        self._apply_shortcuts(self.config.get("shortcuts", {}))
        self.statusBar().showMessage("请选择数据集文件夹")
        self.apply_toolbar_style(self.config.get("toolbar_style", "icons"))

        # 初始化百分比列宽（如果配置中没有则用默认百分比）
        self.center_percentages = self.config.get("center_column_percentages", [0.5, 0.5])
        self.right_percentages = self.config.get("right_column_percentages", [0.4, 0.4, 0.2])

        # 延迟恢复列宽，确保面板已显示
        QTimer.singleShot(0, self.restore_column_widths)

    # ---------- 配置读写 ----------
    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_config(self):
        config = {
            "last_folder": self.last_opened_folder,
            "font_size": self.config.get("font_size", 9),
            "shortcuts": self.config.get("shortcuts", {
                "add_tag": "Ctrl+E",
                "delete_tag": "Delete",
                "undo": "Ctrl+Z",
                "find_tag": "Ctrl+F",
                "save": "Ctrl+S"
            }),
            "center_column_percentages": self.center_percentages,
            "right_column_percentages": self.right_percentages,
            "toolbar_style": self.config.get("toolbar_style", "icons"),
            "window_geometry": self.saveGeometry().toHex().data().decode()
        }
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    # ---------- 菜单与面板 ----------
    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        open_action = QAction("打开文件夹", self)
        open_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_action)

        self.save_action = QAction("保存 (Ctrl+S)", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_all)
        file_menu.addAction(self.save_action)

        file_menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menubar.addMenu("设置")
        settings_action = QAction("偏好设置...", self)
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(settings_action)

    def _create_panels(self):
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.left_panel = LeftPanel()
        self.center_panel = CenterPanel()
        self.right_panel = RightPanel()

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.center_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([400, 500, 500])
        self.setCentralWidget(self.splitter)

        self.right_panel.setup_completer(self.center_panel.completer,
                                         self.center_panel.filter_completer)

        # 监听分割条移动，重新分配列宽
        self.splitter.splitterMoved.connect(self.on_splitter_moved)

        # 监听列宽拖拽（用户手动拖拽表头分割线）
        self.center_panel.table.horizontalHeader().sectionResized.connect(
            lambda col, old, new: self.on_column_resized(
                self.center_panel.table, col, old, new, "center"
            )
        )
        self.right_panel.table.horizontalHeader().sectionResized.connect(
            lambda col, old, new: self.on_column_resized(
                self.right_panel.table, col, old, new, "right"
            )
        )

    def _connect_signals(self):
        self.left_panel.image_selected.connect(self.on_image_selected)
        self.center_panel.tags_modified.connect(self.on_current_tags_modified)
        self.center_panel.translation_edited_from_center.connect(self.on_translation_edited)
        self.center_panel.find_requested.connect(self.find_tag_in_right)
        self.right_panel.request_reload.connect(self.on_global_tags_changed)
        self.right_panel.filter_requested.connect(self.left_panel.set_filter)
        self.right_panel.clear_filter.connect(lambda: self.left_panel.set_filter(None))
        self.right_panel.translation_changed.connect(self.on_translation_edited)
        self.right_panel.add_to_current_callback = self.add_tag_to_current_image_from_right
        self.center_panel.set_translation_callback(
            lambda tag: self.metadata.get(tag, {}).get('translation', '')
                        or self.custom_tags.get(tag, '')
                        or self.standard_meta.get(tag, {}).get('translation', '')
        )
        # 列宽调整（延迟到布局更新后）
        self.right_panel.request_adjust_columns.connect(
            lambda: QTimer.singleShot(0, lambda:
            self.apply_percentage_to_table(self.right_panel.table, self.right_percentages))
        )
        self.center_panel.request_adjust_columns.connect(
            lambda: QTimer.singleShot(0, lambda:
            self.apply_percentage_to_table(self.center_panel.table, self.center_percentages))
        )

    # ---------- 列宽百分比管理 ----------
    def on_splitter_moved(self, pos, index):
        """分割条移动后，重新按百分比应用列宽"""
        self.apply_percentage_to_table(self.center_panel.table, self.center_percentages)
        self.apply_percentage_to_table(self.right_panel.table, self.right_percentages)

    def on_column_resized(self, table, col, old_size, new_size, panel):
        """用户拖拽列宽，实时计算当前百分比并保存，同时调整相邻列保持总宽不变"""
        header = table.horizontalHeader()
        num_cols = header.count()
        viewport_w = table.viewport().width()
        if viewport_w <= 0:
            return

        # 获取当前所有列宽（此时col列可能已被调整为new_size）
        current_widths = [header.sectionSize(i) for i in range(num_cols)]

        # 强制本次变化的列不小于最小宽度
        min_w = self._get_min_col_width(table, col)
        if new_size < min_w:
            header.resizeSection(col, min_w)
            current_widths[col] = min_w
            new_size = min_w

        # 计算总宽度与视口宽度的差值
        total = sum(current_widths)
        diff = total - viewport_w

        if diff != 0:
            # 选择相邻列进行补偿（优先右侧，若为最后一列则左侧）
            if col < num_cols - 1:
                neighbor = col + 1
            else:
                neighbor = col - 1

            neighbor_min = self._get_min_col_width(table, neighbor)
            neighbor_old = current_widths[neighbor]

            # ---------- 新增部分 ----------
            # 当拖动导致总宽超出（diff > 0），且邻居列无法完全补偿时，限制当前列的最大宽度
            if diff > 0:
                neighbor_can_shrink = neighbor_old - neighbor_min
                if diff > neighbor_can_shrink:
                    # 除 col 和 neighbor 之外其他列的总宽度
                    other_cols_sum = total - new_size - neighbor_old
                    max_w = viewport_w - other_cols_sum - neighbor_min
                    if new_size > max_w:
                        new_size = max_w
                        if new_size < min_w:
                            new_size = min_w
                        header.resizeSection(col, new_size)
                        current_widths[col] = new_size
                        # 重新计算 total 和 diff，后续补偿会自然成功
                        total = sum(current_widths)
                        diff = total - viewport_w
            # --------------------------------

            # 计算邻居新宽度并应用
            neighbor_new = neighbor_old - diff
            if neighbor_new < neighbor_min:
                neighbor_new = neighbor_min
            header.resizeSection(neighbor, neighbor_new)
            current_widths[neighbor] = neighbor_new
            total = sum(current_widths)

            # 仍有误差时微调最后一列（通常不会进入了）
            diff = total - viewport_w
            if diff != 0:
                last = num_cols - 1
                last_old = current_widths[last]
                last_new = last_old - diff
                if last_new >= self._get_min_col_width(table, last):
                    header.resizeSection(last, last_new)
                    current_widths[last] = last_new

        # 重新计算百分比并保存
        final_widths = [header.sectionSize(i) for i in range(num_cols)]
        total_final = sum(final_widths)
        if total_final > 0:
            percents = [w / total_final for w in final_widths]
            if panel == "center":
                self.center_percentages = percents
            else:
                self.right_percentages = percents
            self.save_config()
        table.resizeRowsToContents()

    def apply_percentage_to_table(self, table, percentages):
        """根据百分比设置列宽，使总宽度刚好填满视口，无滚动条"""
        header = table.horizontalHeader()
        num_cols = header.count()
        if num_cols == 0 or not percentages or len(percentages) != num_cols:
            return
        viewport_w = table.viewport().width()
        if viewport_w <= 0:
            return

        # 计算每列宽度（注意最后一列用剩余像素，避免精度丢失造成总宽超出）
        widths = []
        allocated = 0
        for i in range(num_cols - 1):
            w = int(viewport_w * percentages[i])
            min_w = self._get_min_col_width(table, i)
            if w < min_w:
                w = min_w
            widths.append(w)
            allocated += w
        # 最后一列占满剩余宽度
        last = viewport_w - allocated
        min_last = self._get_min_col_width(table, num_cols - 1)
        if last < min_last:
            last = min_last
        widths.append(last)

        # 如果有列被最小宽度限制了，可能需要重新从其他列压缩，这里简单处理：如果总宽超出，按比例缩减其他列
        total = sum(widths)
        if total != viewport_w:
            # 微调：将最后一列设为 viewport_w - sum(widths[:-1])
            widths[-1] = viewport_w - sum(widths[:-1])
            if widths[-1] < min_last:
                widths[-1] = min_last

        overflow = sum(widths) - viewport_w
        if overflow > 0:
            # 尝试从最后一列向前压缩，直到消除溢出
            for i in range(num_cols - 1, -1, -1):
                min_w = self._get_min_col_width(table, i)
                if widths[i] - min_w > 0:
                    shrink = min(overflow, widths[i] - min_w)
                    widths[i] -= shrink
                    overflow -= shrink
                if overflow <= 0:
                    break

        for i, w in enumerate(widths):
            header.resizeSection(i, w)
        table.resizeRowsToContents()

    def _get_min_col_width(self, table, col):
        header_item = table.horizontalHeaderItem(col)
        text = header_item.text() if header_item else ""
        fm = QFontMetrics(table.horizontalHeader().font())
        char_width = fm.averageCharWidth() if hasattr(fm, 'averageCharWidth') else fm.horizontalAdvance('x')
        return fm.horizontalAdvance(text) + 2 * char_width

    def restore_column_widths(self):
        """启动时根据保存的百分比恢复列宽"""
        self.apply_percentage_to_table(self.center_panel.table, self.center_percentages)
        self.apply_percentage_to_table(self.right_panel.table, self.right_percentages)

    # 主窗口缩放时重新分配
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_percentage_to_table(self.center_panel.table, self.center_percentages)
        self.apply_percentage_to_table(self.right_panel.table, self.right_percentages)

    # ---------- 其他功能（不变） ----------
    def _apply_shortcuts(self, shortcuts):
        action_map = {
            "add_tag": self.center_panel.add_action,
            "delete_tag": self.center_panel.del_action,
            "undo": self.center_panel.undo_action,
            "find_tag": self.center_panel.find_action,
            "save": self.save_action,
        }
        for name, key in shortcuts.items():
            if name in action_map:
                action_map[name].setShortcut(QKeySequence(key))

    def open_settings(self):
        dlg = SettingsDialog(self.config)
        if dlg.exec() == QDialog.Accepted:
            new_config = dlg.config
            self.config = new_config
            self.save_config()
            font = QApplication.font()
            font.setPointSize(self.config.get("font_size", 9))
            QApplication.setFont(font)
            self._apply_shortcuts(self.config.get("shortcuts", {}))
            self.apply_toolbar_style(self.config.get("toolbar_style", "icons"))

    def apply_toolbar_style(self, style):
        self.center_panel.set_toolbar_style(style)
        self.right_panel.set_toolbar_style(style)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择数据集文件夹", self.last_opened_folder)
        if not folder:
            return
        self.folder_path = folder
        self.last_opened_folder = folder
        self.save_config()

        try:
            self.statusBar().showMessage("正在加载图片...")
            self.images = scan_folder(folder)
            if not self.images:
                QMessageBox.information(self, "提示", "该文件夹没有找到支持的图片")
                return

            for img in self.images.values():
                img.thumbnail = generate_thumbnail(img.path, (80, 60))

            standard_csv = os.path.join(self.tags_dir, "tags.csv")
            standard_meta = load_tag_metadata(standard_csv)
            self.standard_tags_set = set(standard_meta.keys())
            self.standard_meta = standard_meta

            custom_csv = os.path.join(self.tags_dir, "custom_tags.csv")
            self.custom_tags = load_custom_tags(custom_csv)

            # 先统计图片中出现的标签及频率
            freq = compute_tag_frequencies(self.images)

            # 构建 metadata，只包含在图片中出现的标签
            self.metadata = {}
            for tag, count in freq.items():
                # 翻译优先取自自定义，其次标准库，都没有则为空
                trans = self.custom_tags.get(tag)
                if trans is None:
                    trans = standard_meta.get(tag, {}).get('translation', '')
                self.metadata[tag] = {
                    'category': standard_meta.get(tag, {}).get('category', ''),
                    'frequency': count,
                    'translation': trans
                }

            self.left_panel.load_images(self.images)
            self.right_panel.set_images_reference(self.images)
            self.right_panel.load_metadata(self.metadata)

            # 构建补全标签列表
            custom_sorted = sorted(self.custom_tags.keys(), key=str.lower)
            standard_list = [tag for tag in standard_meta if tag not in self.custom_tags]
            all_tags_ordered = custom_sorted + standard_list

            self.center_panel.build_completer(all_tags_ordered)

            self.statusBar().showMessage(f"已加载 {len(self.images)} 张图片")
            self.center_panel.clear_completer_cache()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败: {str(e)}")

    def on_image_selected(self, filename):
        self.current_file = filename
        img = self.images[filename]
        self.center_panel.set_current_image(filename, img)

    def on_current_tags_modified(self, filename):
        self._update_frequencies()
        self.right_panel.metadata = self.metadata
        self.right_panel.refresh_table()
        if self.left_panel.filter_tag:
            self.left_panel.set_filter(self.left_panel.filter_tag)

    def on_global_tags_changed(self):
        self._update_frequencies()
        self.right_panel.metadata = self.metadata
        self.right_panel.refresh_table()
        if self.left_panel.filter_tag:
            self.left_panel.set_filter(self.left_panel.filter_tag)
        if self.current_file and self.current_file in self.images:
            self.center_panel.set_current_image(self.current_file, self.images[self.current_file])
        self.statusBar().showMessage("已修改，请按 Ctrl+S 保存", 3000)

    def _update_frequencies(self):
        freq = compute_tag_frequencies(self.images)
        new_metadata = {}
        for tag, count in freq.items():
            # 保留已有的翻译，新标签从自定义库或标准库获取翻译
            trans = self.metadata.get(tag, {}).get('translation', '')
            if not trans:
                trans = self.custom_tags.get(tag, '')
            if not trans:  # 增加标准库回退
                trans = self.standard_meta.get(tag, {}).get('translation', '')
            new_metadata[tag] = {
                'category': self.metadata.get(tag, {}).get('category', ''),
                'frequency': count,
                'translation': trans
            }
        self.metadata = new_metadata

    def on_translation_edited(self, tag, new_trans):
        if tag in self.metadata:
            self.metadata[tag]['translation'] = new_trans
        else:
            self.metadata[tag] = {'category': '', 'frequency': 0, 'translation': new_trans}
        self.custom_tags[tag] = new_trans
        self._save_custom_tags_now()
        self.right_panel.refresh_table()
        self.center_panel.refresh_table()
        self.center_panel.clear_completer_cache()

    def _save_custom_tags_now(self):
        if self.folder_path:  # 只要有数据集文件夹打开过，就允许保存（否则可能没有翻译过）
            custom_csv = os.path.join(self.tags_dir, "custom_tags.csv")
            save_custom_tags(custom_csv, self.custom_tags)

    def add_tag_to_current_image_from_right(self, tag):
        if not self.current_file:
            QMessageBox.warning(self, "提示", "没有选中任何图片")
            return
        img = self.images[self.current_file]
        img.tags.append(tag)
        self.center_panel._push_undo()
        self.center_panel.refresh_table()
        self.on_current_tags_modified(self.current_file)

    def find_tag_in_right(self, text):
        found = self.right_panel.find_and_select(text)
        if not found:
            QMessageBox.information(self, "未找到", f"标签 '{text}' 不存在")

    def save_all(self):
        if not self.images:
            return
        try:
            for img in self.images.values():
                if img.is_modified():
                    tags_str = ', '.join(img.tags)
                    with open(img.txt_path, 'w', encoding='utf-8') as f:
                        f.write(tags_str)
                    img.original_tags = list(img.tags)
            self._save_custom_tags_now()
            self.statusBar().showMessage("保存成功")
            self.center_panel.undo_stack.clear()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def closeEvent(self, event):
        modified = any(img.is_modified() for img in self.images.values()) if self.images else False
        if modified:
            # 创建自定义消息框
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Question)
            msgBox.setWindowTitle("未保存的修改")
            msgBox.setText("有未保存的修改，是否保存？")

            # 添加中文按钮，并指定角色（决定点击后的行为和返回值）
            saveBtn = msgBox.addButton("保存", QMessageBox.AcceptRole)
            discardBtn = msgBox.addButton("不保存", QMessageBox.DestructiveRole)
            cancelBtn = msgBox.addButton("取消", QMessageBox.RejectRole)

            # 设置默认按钮（按 Enter 键时触发）
            msgBox.setDefaultButton(saveBtn)

            msgBox.exec()  # 显示对话框

            # 判断用户点击了哪个按钮
            if msgBox.clickedButton() == saveBtn:
                self.save_all()
                event.accept()
            elif msgBox.clickedButton() == discardBtn:
                event.accept()
            else:  # 取消
                event.ignore()
        else:
            event.accept()
        self.save_config()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    geom = window.config.get("window_geometry")
    if geom:
        window.restoreGeometry(QByteArray.fromHex(geom.encode()))
    window.show()
    sys.exit(app.exec())