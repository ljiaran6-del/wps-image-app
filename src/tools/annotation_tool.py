from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QSlider,
    QColorDialog, QHBoxLayout, QComboBox, QSpinBox, QFormLayout
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent

from .base_tool import BaseTool
from core.annotation_layer import (
    AnnotationLayer, BrushAnnotation, ArrowAnnotation,
    RectAnnotation, CircleAnnotation, TextAnnotation,
    MosaicAnnotation, BlurAnnotation
)


class AnnotationTool(BaseTool):
    """标注工具：支持画笔、箭头、矩形、圆、文字、马赛克、模糊"""

    TOOL_BRUSH = "画笔"
    TOOL_ARROW = "箭头"
    TOOL_RECT = "矩形"
    TOOL_CIRCLE = "圆形"
    TOOL_TEXT = "文字"
    TOOL_MOSAIC = "马赛克"
    TOOL_BLUR = "模糊"

    def __init__(self, viewer):
        super().__init__(viewer, name="annotation")
        self.layer = AnnotationLayer()
        self.current_tool = self.TOOL_BRUSH
        self.color = "#FF0000"
        self.width = 3
        self.alpha = 255
        self.font_size = 20
        self.drawing = False
        self.start_pos = QPoint()
        self.current_pos = QPoint()
        self.current_brush_points = []
        self._build_property_widget()

    def _build_property_widget(self):
        self.property_widget = QWidget()
        layout = QVBoxLayout(self.property_widget)

        layout.addWidget(QLabel("标注工具"))

        # 工具类型选择
        layout.addWidget(QLabel("工具类型"))
        self.tool_combo = QComboBox()
        self.tool_combo.addItems([
            self.TOOL_BRUSH, self.TOOL_ARROW, self.TOOL_RECT,
            self.TOOL_CIRCLE, self.TOOL_TEXT, self.TOOL_MOSAIC, self.TOOL_BLUR
        ])
        self.tool_combo.currentTextChanged.connect(self.set_tool_type)
        layout.addWidget(self.tool_combo)

        # 颜色选择
        self.btn_color = QPushButton("选择颜色")
        self.btn_color.clicked.connect(self._choose_color)
        layout.addWidget(self.btn_color)

        # 粗细
        form = QFormLayout()
        self.slider_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_width.setMinimum(1)
        self.slider_width.setMaximum(50)
        self.slider_width.setValue(self.width)
        self.slider_width.valueChanged.connect(self._on_width_changed)
        form.addRow("粗细", self.slider_width)

        # 透明度
        self.slider_alpha = QSlider(Qt.Orientation.Horizontal)
        self.slider_alpha.setMinimum(0)
        self.slider_alpha.setMaximum(255)
        self.slider_alpha.setValue(self.alpha)
        self.slider_alpha.valueChanged.connect(self._on_alpha_changed)
        form.addRow("透明度", self.slider_alpha)

        # 字号
        self.spin_font = QSpinBox()
        self.spin_font.setMinimum(8)
        self.spin_font.setMaximum(200)
        self.spin_font.setValue(self.font_size)
        self.spin_font.valueChanged.connect(self._on_font_changed)
        form.addRow("字号", self.spin_font)

        layout.addLayout(form)

        # 删除选中
        self.btn_delete = QPushButton("删除选中标注")
        self.btn_delete.clicked.connect(self.layer.remove_selected)
        self.btn_delete.clicked.connect(self.viewer.update)
        layout.addWidget(self.btn_delete)

        # 清空
        self.btn_clear = QPushButton("清空所有标注")
        self.btn_clear.clicked.connect(self.layer.clear)
        self.btn_clear.clicked.connect(self.viewer.update)
        layout.addWidget(self.btn_clear)

        layout.addStretch()

    def set_tool_type(self, tool_type: str):
        self.current_tool = tool_type

    def _choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = color.name()

    def _on_width_changed(self, value: int):
        self.width = value

    def _on_alpha_changed(self, value: int):
        self.alpha = value

    def _on_font_changed(self, value: int):
        self.font_size = value

    def on_mouse_press(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        img_pos = self.viewer.widget_to_image_pos(event.pos())
        if img_pos.x() < 0:
            # 点击空白处，取消选中
            hit = self.layer.hit_test(img_pos)
            self.layer.selected_index = hit
            self.viewer.update()
            return

        self.drawing = True
        self.start_pos = img_pos
        self.current_pos = img_pos

        if self.current_tool == self.TOOL_BRUSH:
            self.current_brush_points = [img_pos]

    def on_mouse_move(self, event: QMouseEvent):
        if not self.drawing:
            return

        img_pos = self.viewer.widget_to_image_pos(event.pos())
        if img_pos.x() < 0:
            return
        self.current_pos = img_pos

        if self.current_tool == self.TOOL_BRUSH:
            self.current_brush_points.append(img_pos)

        self.viewer.update()

    def on_mouse_release(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        img_pos = self.viewer.widget_to_image_pos(event.pos())
        self.current_pos = img_pos

        if not self.drawing:
            return

        self.drawing = False

        # 创建标注
        annotation = self._create_annotation()
        if annotation:
            self.layer.add(annotation)

        self.current_brush_points = []
        self.viewer.update()

    def _create_annotation(self):
        tl = QPoint(min(self.start_pos.x(), self.current_pos.x()),
                    min(self.start_pos.y(), self.current_pos.y()))
        br = QPoint(max(self.start_pos.x(), self.current_pos.x()),
                    max(self.start_pos.y(), self.current_pos.y()))

        if self.current_tool == self.TOOL_BRUSH:
            if len(self.current_brush_points) < 2:
                return None
            return BrushAnnotation(
                points=self.current_brush_points.copy(),
                color=self.color, width=self.width, alpha=self.alpha
            )

        elif self.current_tool == self.TOOL_ARROW:
            return ArrowAnnotation(
                start=self.start_pos, end=self.current_pos,
                color=self.color, width=self.width, alpha=self.alpha
            )

        elif self.current_tool == self.TOOL_RECT:
            return RectAnnotation(
                top_left=tl, bottom_right=br,
                color=self.color, width=self.width, alpha=self.alpha
            )

        elif self.current_tool == self.TOOL_CIRCLE:
            return CircleAnnotation(
                top_left=tl, bottom_right=br,
                color=self.color, width=self.width, alpha=self.alpha
            )

        elif self.current_tool == self.TOOL_TEXT:
            # 弹出输入框获取文字
            from PySide6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(self.viewer, "输入文字", "标注文字:")
            if ok and text:
                return TextAnnotation(
                    position=self.start_pos, text=text,
                    color=self.color, font_size=self.font_size, alpha=self.alpha
                )
            return None

        elif self.current_tool == self.TOOL_MOSAIC:
            return MosaicAnnotation(
                top_left=tl, bottom_right=br,
                color=self.color, width=self.width, alpha=self.alpha
            )

        elif self.current_tool == self.TOOL_BLUR:
            return BlurAnnotation(
                top_left=tl, bottom_right=br,
                color=self.color, width=self.width, alpha=self.alpha
            )

        return None

    def on_paint(self, painter):
        # 绘制已有标注（传入图片在 widget 中的偏移，让 image 坐标能正确映射到 widget 坐标）
        self.layer.draw(painter, self.viewer.get_scale(), self.viewer.get_image_rect().topLeft())

        # 绘制当前正在创建的预览
        if self.drawing:
            scale = self.viewer.get_scale()
            tl = QPoint(min(self.start_pos.x(), self.current_pos.x()),
                        min(self.start_pos.y(), self.current_pos.y()))
            br = QPoint(max(self.start_pos.x(), self.current_pos.x()),
                        max(self.start_pos.y(), self.current_pos.y()))
            w_tl = self.viewer.image_to_widget_pos(tl)
            w_br = self.viewer.image_to_widget_pos(br)

            from PySide6.QtGui import QPen, QColor
            pen = QPen(QColor(self.color))
            pen.setWidth(int(self.width * scale))
            painter.setPen(pen)

            if self.current_tool in (self.TOOL_RECT, self.TOOL_MOSAIC, self.TOOL_BLUR):
                from PySide6.QtCore import QRect
                painter.drawRect(QRect(w_tl, w_br))
            elif self.current_tool == self.TOOL_CIRCLE:
                from PySide6.QtCore import QRect
                painter.drawEllipse(QRect(w_tl, w_br))
            elif self.current_tool == self.TOOL_ARROW:
                painter.drawLine(w_tl, w_br)

        if self.current_tool == self.TOOL_BRUSH and self.drawing:
            # 画笔实时预览
            if len(self.current_brush_points) >= 2:
                from PySide6.QtGui import QPen, QColor
                scale = self.viewer.get_scale()
                pen = QPen(QColor(self.color))
                pen.setWidth(int(self.width * scale))
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                for i in range(1, len(self.current_brush_points)):
                    p1 = self.viewer.image_to_widget_pos(self.current_brush_points[i-1])
                    p2 = self.viewer.image_to_widget_pos(self.current_brush_points[i])
                    painter.drawLine(p1, p2)
