from PySide6 import QtCore
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QSlider, QSplitter, QHBoxLayout, QSizePolicy
)

from utils import generate_thumbnail


class LeftPanel(QWidget):
    image_selected = Signal(str)  # 文件名

    def __init__(self, parent=None):
        super().__init__(parent)
        self.images = {}  # {filename: ImageData}
        self.current_file = None
        self.filter_tag = None  # 当前筛选标签
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        self.splitter = QSplitter(Qt.Orientation.Vertical)  # 保存为实例变量

        # 上半部分：当前图片预览
        self.preview_label = QLabel("当前图片预览")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid gray;")
        self.preview_label.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Ignored
        )
        self.splitter.addWidget(self.preview_label)

        # 下半部分：文件列表 + 滑块
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QtCore.QSize(80, 60))  # 默认图标大小
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.currentItemChanged.connect(self.on_item_changed)
        bottom_layout.addWidget(self.list_widget)

        # 行高滑块 + 图片数量 同一行
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("缩略图大小:"))
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(30, 120)
        self.size_slider.setValue(60)
        self.size_slider.valueChanged.connect(self.on_slider_changed)
        slider_row.addWidget(self.size_slider)
        self.count_label = QLabel("图片总数: 0")
        slider_row.addWidget(self.count_label)
        bottom_layout.addLayout(slider_row)

        self.splitter.addWidget(bottom_widget)
        main_layout.addWidget(self.splitter)

        # 分隔条移动时自动更新预览图
        self.splitter.splitterMoved.connect(self._update_preview)

    def _update_preview(self):
        """根据 preview_label 当前大小重新缩放并显示预览图"""
        if self.current_file and self.current_file in self.images:
            img = self.images[self.current_file]
            pix = QPixmap(img.path)
            if not pix.isNull():
                scaled_pix = pix.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pix)
            else:
                self.preview_label.setText("无法加载图片")

    def load_images(self, images_dict):
        self.images = images_dict
        self.refresh_list()
        # 如果有图片，自动选中第一个
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def refresh_list(self):
        """根据筛选条件刷新文件列表"""
        self.list_widget.clear()
        filtered = {}
        if self.filter_tag:
            # 筛选包含特定标签的图片
            for fname, img in self.images.items():
                if self.filter_tag in img.tags:
                    filtered[fname] = img
        else:
            filtered = self.images

        for fname, img in filtered.items():
            # 生成或获取缩略图
            thumb = img.thumbnail
            if thumb is None:
                thumb = generate_thumbnail(img.path, (80, 60))
                img.thumbnail = thumb
            icon = QIcon(thumb)
            item = QListWidgetItem(icon, f"{fname}\n{img.width}x{img.height}")
            item.setData(Qt.ItemDataRole.UserRole, fname)  # 存储文件名
            self.list_widget.addItem(item)
        self.count_label.setText(f"图片数量: {self.list_widget.count()}")

    def on_item_changed(self, current, previous):
        if current is None:
            return
        fname = current.data(Qt.ItemDataRole.UserRole)
        self.current_file = fname
        # 先显示预览图，_update_preview 会负责缩放
        self._update_preview()
        self.image_selected.emit(fname)

    def on_slider_changed(self, value):
        """调整缩略图大小（改变行高和图标大小）"""
        self.list_widget.setIconSize(QtCore.QSize(value, int(value * 0.75)))
        # 重新设置每个项目的图标为适当大小的缩略图
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            fname = item.data(Qt.ItemDataRole.UserRole)
            img = self.images.get(fname)
            if img:
                thumb = generate_thumbnail(img.path, (value, int(value * 0.75)))
                item.setIcon(QIcon(thumb))
                img.thumbnail = thumb  # 更新缓存

    def set_filter(self, tag):
        """设置筛选标签，None为取消筛选"""
        self.filter_tag = tag
        self.refresh_list()
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def get_current_file(self):
        return self.current_file

    def resizeEvent(self, event):
        """窗口大小改变时更新预览图"""
        super().resizeEvent(event)
        self._update_preview()