from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QMouseEvent, QPainter, QPen, QColor, QBrush, QPixmap, QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QPushButton, QHBoxLayout, QButtonGroup
from PySide6.QtCore import QSize
from PIL import Image, ImageDraw

from .base_tool import BaseTool


class SelectionTool(BaseTool):
    """选区/蒙版绘制工具基类：支持矩形选区和涂鸦蒙版"""

    MODE_RECT = "rect"
    MODE_BRUSH = "brush"

    def __init__(self, viewer, name: str = "selection"):
        super().__init__(viewer, name)
        self.mode = self.MODE_RECT
        self.brush_size = 20
        self.drawing = False
        self.start_pos = QPoint()
        self.current_pos = QPoint()
        self.mask_image: Image.Image | None = None
        self.selection_rect: QRect | None = None
        self._build_property_widget()

    def _build_property_widget(self):
        self.property_widget = QWidget()
        layout = QVBoxLayout(self.property_widget)

        # 模式选择
        layout.addWidget(QLabel("选区模式"))
        self.btn_rect = QPushButton("矩形选区")
        self.btn_brush = QPushButton("涂鸦蒙版")
        self.btn_rect.setCheckable(True)
        self.btn_brush.setCheckable(True)
        self.btn_rect.setChecked(True)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.btn_rect)
        mode_layout.addWidget(self.btn_brush)
        layout.addLayout(mode_layout)

        self.btn_rect.clicked.connect(lambda: self.set_mode(self.MODE_RECT))
        self.btn_brush.clicked.connect(lambda: self.set_mode(self.MODE_BRUSH))

        # 笔刷大小
        layout.addWidget(QLabel("笔刷大小"))
        self.slider_size = QSlider(Qt.Orientation.Horizontal)
        self.slider_size.setMinimum(5)
        self.slider_size.setMaximum(200)
        self.slider_size.setValue(self.brush_size)
        self.slider_size.valueChanged.connect(self.set_brush_size)
        layout.addWidget(self.slider_size)

        # 清除按钮
        self.btn_clear = QPushButton("清除选区")
        self.btn_clear.clicked.connect(self.clear_selection)
        layout.addWidget(self.btn_clear)

        layout.addStretch()

    def set_mode(self, mode: str):
        self.mode = mode
        self.btn_rect.setChecked(mode == self.MODE_RECT)
        self.btn_brush.setChecked(mode == self.MODE_BRUSH)
        self.viewer.update()

    def set_brush_size(self, size: int):
        self.brush_size = size

    def clear_selection(self):
        self.mask_image = None
        self.selection_rect = None
        self.viewer.update()

    def get_mask(self) -> Image.Image | None:
        """获取当前选区的 mask（白色为编辑区域，黑色为保留区域）"""
        image = self.viewer.get_image()
        if image is None:
            return None

        width, height = image.size
        mask = Image.new("L", (width, height), 0)

        if self.mode == self.MODE_RECT and self.selection_rect is not None:
            draw = ImageDraw.Draw(mask)
            x1, y1, w, h = self.selection_rect.getRect()
            x2, y2 = x1 + w, y1 + h
            draw.rectangle([x1, y1, x2, y2], fill=255)
        elif self.mode == self.MODE_BRUSH and self.mask_image is not None:
            mask = self.mask_image.copy()

        return mask

    def on_mouse_press(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        img_pos = self.viewer.widget_to_image_pos(event.pos())
        if img_pos.x() < 0:
            return

        self.drawing = True
        self.start_pos = img_pos
        self.current_pos = img_pos

        if self.mode == self.MODE_BRUSH:
            image = self.viewer.get_image()
            if image is None:
                return
            if self.mask_image is None:
                self.mask_image = Image.new("L", image.size, 0)
            self._draw_brush(img_pos)

        self.viewer.update()

    def on_mouse_move(self, event: QMouseEvent):
        if not self.drawing:
            return

        img_pos = self.viewer.widget_to_image_pos(event.pos())
        if img_pos.x() < 0:
            return
        self.current_pos = img_pos

        if self.mode == self.MODE_BRUSH:
            self._draw_brush(img_pos)

        self.viewer.update()

    def on_mouse_release(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        img_pos = self.viewer.widget_to_image_pos(event.pos())
        self.current_pos = img_pos

        if self.mode == self.MODE_RECT:
            x1 = min(self.start_pos.x(), self.current_pos.x())
            y1 = min(self.start_pos.y(), self.current_pos.y())
            x2 = max(self.start_pos.x(), self.current_pos.x())
            y2 = max(self.start_pos.y(), self.current_pos.y())
            if x2 - x1 > 5 and y2 - y1 > 5:
                self.selection_rect = QRect(x1, y1, x2 - x1, y2 - y1)

        self.drawing = False
        self.viewer.update()

    def _draw_brush(self, pos: QPoint):
        """在蒙版上绘制笔刷"""
        if self.mask_image is None:
            return
        draw = ImageDraw.Draw(self.mask_image)
        r = self.brush_size // 2
        draw.ellipse([pos.x() - r, pos.y() - r, pos.x() + r, pos.y() + r], fill=255)

    def on_paint(self, painter: QPainter):
        if self.mode == self.MODE_RECT:
            # 绘制矩形选区（预览或已完成）
            if self.drawing:
                x1 = min(self.start_pos.x(), self.current_pos.x())
                y1 = min(self.start_pos.y(), self.current_pos.y())
                x2 = max(self.start_pos.x(), self.current_pos.x())
                y2 = max(self.start_pos.y(), self.current_pos.y())
            elif self.selection_rect is not None:
                x1, y1, w, h = self.selection_rect.getRect()
                x2, y2 = x1 + w, y1 + h
            else:
                return

            p1 = self.viewer.image_to_widget_pos(QPoint(x1, y1))
            p2 = self.viewer.image_to_widget_pos(QPoint(x2, y2))

            pen = QPen(QColor("#00a8ff"))
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(0, 168, 255, 80)))
            painter.drawRect(QRect(p1, p2))

            # 绘制四个角点，增加可见性
            painter.setBrush(QBrush(QColor("#00a8ff")))
            handle_size = 8
            for hx, hy in [(p1.x(), p1.y()), (p2.x(), p1.y()), (p1.x(), p2.y()), (p2.x(), p2.y())]:
                painter.drawEllipse(hx - handle_size//2, hy - handle_size//2, handle_size, handle_size)

        elif self.mode == self.MODE_BRUSH:
            # 绘制蒙版预览（高亮红色覆盖）
            if self.mask_image is not None:
                from PySide6.QtGui import QImage
                import numpy as np
                mask_array = np.array(self.mask_image)
                preview = np.zeros((mask_array.shape[0], mask_array.shape[1], 4), dtype=np.uint8)
                # 已涂抹区域显示为亮红色，透明度较高
                preview[mask_array > 0] = [255, 30, 30, 200]
                qimage = QImage(preview.data, preview.shape[1], preview.shape[0], QImage.Format.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimage.copy())
                img_rect = self.viewer.get_image_rect()
                painter.drawPixmap(img_rect, pixmap)

            # 绘制画笔光标（跟随鼠标）
            if self.drawing:
                cursor_pos = self.viewer.image_to_widget_pos(self.current_pos)
                r = max(3, int(self.brush_size * self.viewer.get_scale() / 2))
                # 外圈白色，内圈红色
                painter.setPen(QPen(QColor("#ffffff"), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(cursor_pos.x() - r, cursor_pos.y() - r, r * 2, r * 2)
                painter.setPen(QPen(QColor("#ff0000"), 1))
                painter.drawEllipse(cursor_pos.x() - r, cursor_pos.y() - r, r * 2, r * 2)
