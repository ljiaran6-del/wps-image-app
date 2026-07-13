from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPoint
from PySide6.QtGui import QMouseEvent, QPaintEvent, QPainter
from abc import ABC, abstractmethod


class BaseTool(ABC):
    """工具基类"""

    def __init__(self, viewer, name: str = "tool"):
        self.viewer = viewer
        self.name = name
        self.property_widget: QWidget | None = None

    @abstractmethod
    def on_mouse_press(self, event: QMouseEvent):
        pass

    @abstractmethod
    def on_mouse_move(self, event: QMouseEvent):
        pass

    @abstractmethod
    def on_mouse_release(self, event: QMouseEvent):
        pass

    def on_paint(self, painter: QPainter):
        """在图片上绘制工具相关的内容（如选区框、蒙版预览）"""
        pass

    def get_property_widget(self) -> QWidget | None:
        """返回右侧面板中显示的属性控件"""
        return self.property_widget

    def activate(self):
        """工具被激活时调用"""
        pass

    def deactivate(self):
        """工具被取消激活时调用"""
        pass
