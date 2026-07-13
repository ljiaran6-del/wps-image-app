from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QSlider, QHBoxLayout, QTextEdit, QButtonGroup
)
from PySide6.QtCore import Qt

from .selection_tool import SelectionTool


class AIEditTool(SelectionTool):
    """AI局部改图工具"""

    def __init__(self, viewer):
        super().__init__(viewer, name="ai_edit")
        self.process_callback = None
        self._build_property_widget()

    def _build_property_widget(self):
        self.property_widget = QWidget()
        layout = QVBoxLayout(self.property_widget)
        layout.setSpacing(10)

        layout.addWidget(QLabel("AI局部改图"))
        layout.addWidget(QLabel("框选要修改的区域，输入提示词，然后点击开始。"))

        # 提示词输入
        layout.addWidget(QLabel("提示词"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("例如：把这里换成蓝天白云")
        self.prompt_input.setMaximumHeight(80)
        layout.addWidget(self.prompt_input)

        # 模式选择
        layout.addWidget(QLabel("选区模式"))
        self.btn_rect = QPushButton("矩形选区")
        self.btn_brush = QPushButton("涂鸦蒙版")
        self.btn_rect.setCheckable(True)
        self.btn_brush.setCheckable(True)
        self.btn_rect.setChecked(True)
        self.btn_rect.setStyleSheet(self._mode_button_style())
        self.btn_brush.setStyleSheet(self._mode_button_style())

        self.mode_group = QButtonGroup(self.property_widget)
        self.mode_group.addButton(self.btn_rect)
        self.mode_group.addButton(self.btn_brush)
        self.mode_group.setExclusive(True)

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

        self.btn_clear = QPushButton("清除选区")
        self.btn_clear.clicked.connect(self.clear_selection)
        layout.addWidget(self.btn_clear)

        self.btn_process = QPushButton("开始改图")
        self.btn_process.setStyleSheet("background-color: #00a8ff; color: white; padding: 8px;")
        self.btn_process.clicked.connect(self._on_process)
        layout.addWidget(self.btn_process)

        layout.addStretch()

    def _mode_button_style(self) -> str:
        return """
            QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:checked {
                background-color: #00a8ff;
                border: 1px solid #00a8ff;
            }
        """

    def get_prompt(self) -> str:
        return self.prompt_input.toPlainText().strip()

    def set_process_callback(self, callback):
        """设置处理按钮点击回调"""
        self.process_callback = callback

    def _on_process(self):
        if self.process_callback:
            self.process_callback(self)
