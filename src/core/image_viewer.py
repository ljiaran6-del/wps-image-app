from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, QRect, QSize, Signal
from PySide6.QtGui import QPainter, QPixmap, QImage, QColor, QMouseEvent, QWheelEvent, QKeyEvent
from PIL import Image
import numpy as np

from tools.base_tool import BaseTool


class ImageViewer(QWidget):
    """图片查看器：显示、缩放、拖动、适应窗口"""

    # 信号
    scale_changed = Signal(float)
    mouse_moved = Signal(QPoint)
    image_loaded = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._pil_image: Image.Image | None = None
        self._pixmap: QPixmap | None = None
        self._scale: float = 1.0
        self._offset = QPoint(0, 0)
        self._min_scale = 0.05
        self._max_scale = 20.0

        # 拖动状态
        self._dragging = False
        self._last_mouse_pos = QPoint()

        # 背景色
        self.setStyleSheet("background-color: #2b2b2b;")
        self.setMouseTracking(True)

        self._tool: BaseTool | None = None

    def set_tool(self, tool: BaseTool | None):
        """设置当前工具"""
        self._tool = tool

    def get_tool(self) -> BaseTool | None:
        return self._tool

    def set_image(self, image: Image.Image):
        """设置显示的图片"""
        self._pil_image = image.copy()
        self._pixmap = self._pil_to_pixmap(self._pil_image)
        self._reset_view()
        self.image_loaded.emit()
        self.update()

    def get_image(self) -> Image.Image | None:
        """获取当前显示的图片"""
        if self._pil_image is None:
            return None
        return self._pil_image.copy()

    def update_image(self, image: Image.Image):
        """更新当前显示的图片（不重置视图）"""
        self._pil_image = image.copy()
        self._pixmap = self._pil_to_pixmap(self._pil_image)
        self.update()

    def _pil_to_pixmap(self, image: Image.Image) -> QPixmap:
        """PIL Image 转 QPixmap"""
        if image.mode == "RGBA":
            fmt = QImage.Format.Format_RGBA8888
        elif image.mode == "RGB":
            fmt = QImage.Format.Format_RGB888
        else:
            image = image.convert("RGBA")
            fmt = QImage.Format.Format_RGBA8888

        data = image.tobytes("raw", image.mode)
        qimage = QImage(data, image.width, image.height, fmt)
        return QPixmap.fromImage(qimage.copy())

    def _reset_view(self):
        """重置视图（适应窗口）"""
        if self._pixmap is None:
            return
        self.fit_to_window()

    def fit_to_window(self):
        """适应窗口大小"""
        if self._pixmap is None:
            return
        widget_size = self.size()
        img_size = self._pixmap.size()

        scale_x = widget_size.width() / img_size.width()
        scale_y = widget_size.height() / img_size.height()
        self._scale = min(scale_x, scale_y) * 0.95  # 留一点边距
        self._scale = max(self._min_scale, min(self._scale, self._max_scale))

        self._center_image()
        self.scale_changed.emit(self._scale)
        self.update()

    def actual_size(self):
        """实际大小（1:1）"""
        self._scale = 1.0
        self._center_image()
        self.scale_changed.emit(self._scale)
        self.update()

    def _center_image(self):
        """将图片居中"""
        if self._pixmap is None:
            return
        widget_size = self.size()
        img_size = self._pixmap.size() * self._scale
        self._offset = QPoint(
            int((widget_size.width() - img_size.width()) / 2),
            int((widget_size.height() - img_size.height()) / 2),
        )

    def zoom_in(self, factor: float = 1.25):
        """放大"""
        self.set_scale(self._scale * factor)

    def zoom_out(self, factor: float = 0.8):
        """缩小"""
        self.set_scale(self._scale * factor)

    def set_scale(self, scale: float, anchor: QPoint = None):
        """设置缩放比例，可指定锚点"""
        if self._pixmap is None:
            return

        old_scale = self._scale
        new_scale = max(self._min_scale, min(scale, self._max_scale))

        if anchor is None:
            # 以窗口中心为锚点
            anchor = QPoint(self.width() // 2, self.height() // 2)

        # 以锚点为中心缩放
        self._offset = anchor - (anchor - self._offset) * (new_scale / old_scale)
        self._scale = new_scale
        self.scale_changed.emit(self._scale)
        self.update()

    def get_scale(self) -> float:
        return self._scale

    def get_image_rect(self) -> QRect:
        """获取图片在窗口中的矩形区域"""
        if self._pixmap is None:
            return QRect()
        size = self._pixmap.size() * self._scale
        return QRect(self._offset.x(), self._offset.y(), int(size.width()), int(size.height()))

    def widget_to_image_pos(self, pos: QPoint) -> QPoint:
        """将窗口坐标转换为图片坐标"""
        img_rect = self.get_image_rect()
        if not img_rect.contains(pos):
            return QPoint(-1, -1)
        x = int((pos.x() - img_rect.x()) / self._scale)
        y = int((pos.y() - img_rect.y()) / self._scale)
        return QPoint(x, y)

    def image_to_widget_pos(self, pos: QPoint) -> QPoint:
        """将图片坐标转换为窗口坐标"""
        img_rect = self.get_image_rect()
        x = int(pos.x() * self._scale + img_rect.x())
        y = int(pos.y() * self._scale + img_rect.y())
        return QPoint(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 绘制背景
        painter.fillRect(self.rect(), QColor("#2b2b2b"))

        if self._pixmap is None:
            # 绘制提示文字
            painter.setPen(QColor("#888888"))
            text = "点击 文件 -> 打开 选择图片"
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)
            return

        # 绘制图片
        img_rect = self.get_image_rect()
        painter.drawPixmap(img_rect, self._pixmap)

        # 调用工具的绘制方法（选区、标注等）
        if self._tool:
            self._tool.on_paint(painter)

    def resizeEvent(self, event):
        if self._pixmap is not None:
            self._center_image()
            self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if self._tool and event.button() == Qt.MouseButton.LeftButton:
            self._tool.on_mouse_press(event)
        elif event.button() == Qt.MouseButton.MiddleButton:
            self._dragging = True
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.mouse_moved.emit(event.pos())
        if self._tool:
            self._tool.on_mouse_move(event)
        if self._dragging:
            delta = event.pos() - self._last_mouse_pos
            self._offset += delta
            self._last_mouse_pos = event.pos()
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._tool and event.button() == Qt.MouseButton.LeftButton:
            self._tool.on_mouse_release(event)
        if event.button() == Qt.MouseButton.MiddleButton:
            self._dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        if self._pixmap is None:
            return

        delta = event.angleDelta().y()
        if delta > 0:
            self.set_scale(self._scale * 1.1, event.position().toPoint())
        else:
            self.set_scale(self._scale * 0.9, event.position().toPoint())
        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().keyReleaseEvent(event)
