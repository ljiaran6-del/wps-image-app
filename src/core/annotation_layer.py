from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math


@dataclass
class Annotation(ABC):
    """标注元素基类"""
    color: str = "#FF0000"
    width: int = 3
    alpha: int = 255

    @abstractmethod
    def draw(self, painter: QPainter, scale: float = 1.0):
        pass

    @abstractmethod
    def draw_pil(self, draw: ImageDraw.ImageDraw, image_size: tuple):
        """在 PIL ImageDraw 上绘制，用于保存时合并"""
        pass

    @abstractmethod
    def bbox(self) -> QRect:
        """返回包围盒，用于选中判断"""
        pass

    def _qt_color(self) -> QColor:
        c = QColor(self.color)
        c.setAlpha(self.alpha)
        return c


@dataclass
class BrushAnnotation(Annotation):
    points: List[QPoint] = field(default_factory=list)

    def draw(self, painter: QPainter, scale: float = 1.0):
        if len(self.points) < 2:
            return
        pen = QPen(self._qt_color())
        pen.setWidth(int(self.width * scale))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        for i in range(1, len(self.points)):
            p1 = self.points[i - 1] * scale
            p2 = self.points[i] * scale
            painter.drawLine(p1, p2)

    def draw_pil(self, draw: ImageDraw.ImageDraw, image_size: tuple):
        if len(self.points) < 2:
            return
        color = self._pil_color()
        r = self.width // 2
        for i in range(1, len(self.points)):
            draw.line([self.points[i-1].x(), self.points[i-1].y(),
                       self.points[i].x(), self.points[i].y()],
                      fill=color, width=self.width)
            draw.ellipse([self.points[i].x()-r, self.points[i].y()-r,
                          self.points[i].x()+r, self.points[i].y()+r], fill=color)

    def bbox(self) -> QRect:
        if not self.points:
            return QRect()
        xs = [p.x() for p in self.points]
        ys = [p.y() for p in self.points]
        return QRect(min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys))

    def _pil_color(self):
        c = QColor(self.color)
        return (c.red(), c.green(), c.blue(), self.alpha)


@dataclass
class ArrowAnnotation(Annotation):
    start: QPoint = field(default_factory=QPoint)
    end: QPoint = field(default_factory=QPoint)

    def draw(self, painter: QPainter, scale: float = 1.0):
        s = self.start * scale
        e = self.end * scale
        pen = QPen(self._qt_color())
        pen.setWidth(int(self.width * scale))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(s, e)

        # 箭头
        angle = math.atan2(e.y() - s.y(), e.x() - s.x())
        arrow_len = 15 * scale
        arrow_angle = math.pi / 6
        p1 = QPoint(
            int(e.x() - arrow_len * math.cos(angle - arrow_angle)),
            int(e.y() - arrow_len * math.sin(angle - arrow_angle))
        )
        p2 = QPoint(
            int(e.x() - arrow_len * math.cos(angle + arrow_angle)),
            int(e.y() - arrow_len * math.sin(angle + arrow_angle))
        )
        painter.drawLine(e, p1)
        painter.drawLine(e, p2)

    def draw_pil(self, draw: ImageDraw.ImageDraw, image_size: tuple):
        color = self._pil_color()
        draw.line([self.start.x(), self.start.y(), self.end.x(), self.end.y()],
                  fill=color, width=self.width)
        angle = math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x())
        arrow_len = 15
        arrow_angle = math.pi / 6
        p1 = (int(self.end.x() - arrow_len * math.cos(angle - arrow_angle)),
              int(self.end.y() - arrow_len * math.sin(angle - arrow_angle)))
        p2 = (int(self.end.x() - arrow_len * math.cos(angle + arrow_angle)),
              int(self.end.y() - arrow_len * math.sin(angle + arrow_angle)))
        draw.line([self.end.x(), self.end.y(), p1[0], p1[1]], fill=color, width=self.width)
        draw.line([self.end.x(), self.end.y(), p2[0], p2[1]], fill=color, width=self.width)

    def bbox(self) -> QRect:
        x1, y1 = self.start.x(), self.start.y()
        x2, y2 = self.end.x(), self.end.y()
        return QRect(min(x1, x2), min(y1, y2), abs(x2-x1), abs(y2-y1))

    def _pil_color(self):
        c = QColor(self.color)
        return (c.red(), c.green(), c.blue(), self.alpha)


@dataclass
class RectAnnotation(Annotation):
    top_left: QPoint = field(default_factory=QPoint)
    bottom_right: QPoint = field(default_factory=QPoint)
    filled: bool = False

    def draw(self, painter: QPainter, scale: float = 1.0):
        tl = self.top_left * scale
        br = self.bottom_right * scale
        rect = QRect(tl, br)
        pen = QPen(self._qt_color())
        pen.setWidth(int(self.width * scale))
        painter.setPen(pen)
        if self.filled:
            painter.setBrush(QBrush(self._qt_color()))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

    def draw_pil(self, draw: ImageDraw.ImageDraw, image_size: tuple):
        color = self._pil_color()
        coords = [self.top_left.x(), self.top_left.y(),
                  self.bottom_right.x(), self.bottom_right.y()]
        if self.filled:
            draw.rectangle(coords, fill=color)
        else:
            draw.rectangle(coords, outline=color, width=self.width)

    def bbox(self) -> QRect:
        return QRect(self.top_left, self.bottom_right)

    def _pil_color(self):
        c = QColor(self.color)
        return (c.red(), c.green(), c.blue(), self.alpha)


@dataclass
class CircleAnnotation(Annotation):
    top_left: QPoint = field(default_factory=QPoint)
    bottom_right: QPoint = field(default_factory=QPoint)
    filled: bool = False

    def draw(self, painter: QPainter, scale: float = 1.0):
        tl = self.top_left * scale
        br = self.bottom_right * scale
        rect = QRect(tl, br)
        pen = QPen(self._qt_color())
        pen.setWidth(int(self.width * scale))
        painter.setPen(pen)
        if self.filled:
            painter.setBrush(QBrush(self._qt_color()))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect)

    def draw_pil(self, draw: ImageDraw.ImageDraw, image_size: tuple):
        color = self._pil_color()
        coords = [self.top_left.x(), self.top_left.y(),
                  self.bottom_right.x(), self.bottom_right.y()]
        if self.filled:
            draw.ellipse(coords, fill=color)
        else:
            draw.ellipse(coords, outline=color, width=self.width)

    def bbox(self) -> QRect:
        return QRect(self.top_left, self.bottom_right)

    def _pil_color(self):
        c = QColor(self.color)
        return (c.red(), c.green(), c.blue(), self.alpha)


@dataclass
class TextAnnotation(Annotation):
    position: QPoint = field(default_factory=QPoint)
    text: str = ""
    font_size: int = 20

    def draw(self, painter: QPainter, scale: float = 1.0):
        pos = self.position * scale
        font = QFont("Microsoft YaHei", int(self.font_size * scale))
        painter.setFont(font)
        painter.setPen(self._qt_color())
        painter.drawText(pos, self.text)

    def draw_pil(self, draw: ImageDraw.ImageDraw, image_size: tuple):
        color = self._pil_color()
        try:
            font = ImageFont.truetype("msyh.ttc", self.font_size)
        except Exception:
            font = ImageFont.load_default()
        draw.text((self.position.x(), self.position.y()), self.text, fill=color, font=font)

    def bbox(self) -> QRect:
        # 简单估计
        w = len(self.text) * self.font_size
        h = self.font_size
        return QRect(self.position.x(), self.position.y(), w, h)

    def _pil_color(self):
        c = QColor(self.color)
        return (c.red(), c.green(), c.blue(), self.alpha)


@dataclass
class MosaicAnnotation(Annotation):
    top_left: QPoint = field(default_factory=QPoint)
    bottom_right: QPoint = field(default_factory=QPoint)
    block_size: int = 10

    def draw(self, painter: QPainter, scale: float = 1.0):
        tl = self.top_left * scale
        br = self.bottom_right * scale
        rect = QRect(tl, br)
        # 截取当前区域并绘制马赛克效果（简化：用背景色填充 + 网格）
        color = self._qt_color()
        painter.fillRect(rect, QColor(100, 100, 100, 200))
        pen = QPen(QColor(80, 80, 80, 200))
        pen.setWidth(1)
        painter.setPen(pen)
        block = int(self.block_size * scale)
        for x in range(tl.x(), br.x(), block):
            painter.drawLine(x, tl.y(), x, br.y())
        for y in range(tl.y(), br.y(), block):
            painter.drawLine(tl.x(), y, br.x(), y)

    def draw_pil(self, draw: ImageDraw.ImageDraw, image_size: tuple):
        # 马赛克在合并时需要在原图上处理，这里只做占位
        pass

    def bbox(self) -> QRect:
        return QRect(self.top_left, self.bottom_right)

    def _pil_color(self):
        c = QColor(self.color)
        return (c.red(), c.green(), c.blue(), self.alpha)


@dataclass
class BlurAnnotation(Annotation):
    top_left: QPoint = field(default_factory=QPoint)
    bottom_right: QPoint = field(default_factory=QPoint)
    radius: int = 10

    def draw(self, painter: QPainter, scale: float = 1.0):
        tl = self.top_left * scale
        br = self.bottom_right * scale
        rect = QRect(tl, br)
        # 简化：用半透明灰色填充表示模糊区域
        painter.fillRect(rect, QColor(128, 128, 128, 100))

    def draw_pil(self, draw: ImageDraw.ImageDraw, image_size: tuple):
        # 模糊在合并时需要在原图上处理，这里只做占位
        pass

    def bbox(self) -> QRect:
        return QRect(self.top_left, self.bottom_right)

    def _pil_color(self):
        c = QColor(self.color)
        return (c.red(), c.green(), c.blue(), self.alpha)


class AnnotationLayer:
    """标注层：管理所有标注元素"""

    def __init__(self):
        self.annotations: List[Annotation] = []
        self.selected_index: int = -1

    def add(self, annotation: Annotation):
        self.annotations.append(annotation)
        self.selected_index = len(self.annotations) - 1

    def remove(self, index: int):
        if 0 <= index < len(self.annotations):
            self.annotations.pop(index)
            if self.selected_index >= len(self.annotations):
                self.selected_index = len(self.annotations) - 1

    def remove_selected(self):
        if self.selected_index >= 0:
            self.remove(self.selected_index)

    def clear(self):
        self.annotations.clear()
        self.selected_index = -1

    def draw(self, painter: QPainter, scale: float = 1.0, offset: QPoint = None):
        # 如果有偏移，把坐标系原点移到图片在 widget 中的左上角
        if offset is not None:
            painter.save()
            painter.translate(offset)

        for i, annotation in enumerate(self.annotations):
            annotation.draw(painter, scale)
            if i == self.selected_index:
                # 绘制选中框
                bbox = annotation.bbox()
                if bbox.isValid():
                    pen = QPen(QColor("#00a8ff"))
                    pen.setWidth(2)
                    pen.setStyle(Qt.PenStyle.DashLine)
                    painter.setPen(pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    scaled_bbox = QRect(
                        int(bbox.x() * scale), int(bbox.y() * scale),
                        int(bbox.width() * scale), int(bbox.height() * scale)
                    )
                    painter.drawRect(scaled_bbox)

        if offset is not None:
            painter.restore()

    def hit_test(self, pos: QPoint) -> int:
        """命中测试，返回命中的标注索引，-1 表示未命中"""
        for i in range(len(self.annotations) - 1, -1, -1):
            if self.annotations[i].bbox().contains(pos):
                return i
        return -1

    def merge_to_image(self, image: Image.Image) -> Image.Image:
        """将标注合并到图片上"""
        result = image.copy().convert("RGBA")
        # 处理马赛克和模糊（需要读取原图内容）
        for annotation in self.annotations:
            if isinstance(annotation, MosaicAnnotation):
                bbox = annotation.bbox()
                region = result.crop((bbox.x(), bbox.y(), bbox.x()+bbox.width(), bbox.y()+bbox.height()))
                small = region.resize((max(1, bbox.width()//annotation.block_size), max(1, bbox.height()//annotation.block_size)), Image.Resampling.NEAREST)
                mosaic = small.resize((bbox.width(), bbox.height()), Image.Resampling.NEAREST)
                result.paste(mosaic, (bbox.x(), bbox.y()))
            elif isinstance(annotation, BlurAnnotation):
                bbox = annotation.bbox()
                region = result.crop((bbox.x(), bbox.y(), bbox.x()+bbox.width(), bbox.y()+bbox.height()))
                blurred = region.filter(ImageFilter.GaussianBlur(radius=annotation.radius))
                result.paste(blurred, (bbox.x(), bbox.y()))

        # 绘制其他标注
        overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for annotation in self.annotations:
            if not isinstance(annotation, (MosaicAnnotation, BlurAnnotation)):
                annotation.draw_pil(draw, result.size)

        result = Image.alpha_composite(result, overlay)
        return result
