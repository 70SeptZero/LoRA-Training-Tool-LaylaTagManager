from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QWheelEvent, QPixmap
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem

class ImagePreview(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)

        # 交互设置
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        # 注意：不全局设置 setResizeAnchor，因为 fitInView 需要视图中心作为锚点
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("border: none; background-color: #f0f0f0;")

        self._min_scale = 1.0
        self._pending_fit = False

    def set_image(self, pixmap: QPixmap):
        self._pixmap_item.setPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))

        vp = self.viewport()
        if self.isVisible() and vp.width() > 0 and vp.height() > 0:
            self.fit_to_view()
        else:
            self._pending_fit = True

    def showEvent(self, event):
        super().showEvent(event)
        if self._pending_fit and self.viewport().width() > 0:
            self._pending_fit = False
            self.fit_to_view()

    def fit_to_view(self):
        """图片适应视图，保持居中"""
        old_anchor = self.resizeAnchor()
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.setResizeAnchor(old_anchor)

        self._min_scale = self.transform().m11()

    # ---------- 缩放（滚轮）----------
    def wheelEvent(self, event: QWheelEvent):
        factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        current_scale = self.transform().m11()
        new_scale = current_scale * factor
        if new_scale < self._min_scale:
            factor = self._min_scale / current_scale
        self.scale(factor, factor)
        self._enforce_center_constraints()

    # ---------- 平移限制 ----------
    def scrollContentsBy(self, dx: int, dy: int):
        super().scrollContentsBy(dx, dy)
        self._enforce_center_constraints()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._scene.sceneRect().isValid():
            self._min_scale = self._calc_fit_scale()
            current_scale = self.transform().m11()
            if current_scale < self._min_scale:
                self.fit_to_view()
            else:
                self._enforce_center_constraints()

    # ---------- 内部辅助 ----------
    def _calc_fit_scale(self):
        view_rect = self.viewport().rect()
        scene_rect = self._scene.sceneRect()
        if scene_rect.isEmpty():
            return 1.0
        scale_x = view_rect.width() / scene_rect.width()
        scale_y = view_rect.height() / scene_rect.height()
        return min(scale_x, scale_y)

    def _enforce_center_constraints(self):
        viewport_rect = self.viewport().rect()
        scene_rect = self._scene.sceneRect()
        transform = self.transform()
        mapped_rect = transform.mapRect(scene_rect)

        dx, dy = 0, 0

        # 水平
        if mapped_rect.width() < viewport_rect.width():
            dx = (viewport_rect.width() - mapped_rect.width()) / 2 - mapped_rect.left()
        else:
            if mapped_rect.left() > 0:
                dx = -mapped_rect.left()
            elif mapped_rect.right() < viewport_rect.width():
                dx = viewport_rect.width() - mapped_rect.right()

        # 垂直
        if mapped_rect.height() < viewport_rect.height():
            dy = (viewport_rect.height() - mapped_rect.height()) / 2 - mapped_rect.top()
        else:
            if mapped_rect.top() > 0:
                dy = -mapped_rect.top()
            elif mapped_rect.bottom() < viewport_rect.height():
                dy = viewport_rect.height() - mapped_rect.bottom()

        if dx != 0 or dy != 0:
            scale = transform.m11()
            transform.translate(dx / scale, dy / scale)
            self.setTransform(transform)