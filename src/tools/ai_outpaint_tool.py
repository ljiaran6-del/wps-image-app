from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QFormLayout, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt
from PIL import Image

from .base_tool import BaseTool


class AIOutpaintTool(BaseTool):
    """AI扩图工具"""

    PRESET_RATIOS = {
        "1:1 (正方形)": (1, 1),
        "16:9 (宽屏)": (16, 9),
        "9:16 (竖屏)": (9, 16),
        "4:3 (标准)": (4, 3),
        "3:4 (竖版)": (3, 4),
    }

    ANCHORS = {
        "居中": "center",
        "顶部": "top",
        "底部": "bottom",
        "左侧": "left",
        "右侧": "right",
    }

    def __init__(self, viewer):
        super().__init__(viewer, name="ai_outpaint")
        self.process_callback = None
        self._build_property_widget()

    def _build_property_widget(self):
        self.property_widget = QWidget()
        layout = QVBoxLayout(self.property_widget)

        layout.addWidget(QLabel("AI扩图"))
        layout.addWidget(QLabel("选择目标比例和锚点，AI 会自动扩展图片。"))

        # 比例选择
        layout.addWidget(QLabel("目标比例"))
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(list(self.PRESET_RATIOS.keys()))
        self.ratio_combo.currentIndexChanged.connect(self._on_ratio_changed)
        layout.addWidget(self.ratio_combo)

        # 缩放倍数
        layout.addWidget(QLabel("基于短边的放大倍数"))
        self.scale_spin = QSpinBox()
        self.scale_spin.setMinimum(1)
        self.scale_spin.setMaximum(5)
        self.scale_spin.setValue(2)
        self.scale_spin.valueChanged.connect(self._update_target_size)
        layout.addWidget(self.scale_spin)

        # 锚点选择
        layout.addWidget(QLabel("原图位置"))
        self.anchor_combo = QComboBox()
        self.anchor_combo.addItems(list(self.ANCHORS.keys()))
        layout.addWidget(self.anchor_combo)

        # 目标尺寸显示
        self.size_label = QLabel("目标尺寸: -")
        layout.addWidget(self.size_label)

        # 自定义目标尺寸
        self.check_custom_size = QCheckBox("使用自定义尺寸")
        self.check_custom_size.stateChanged.connect(self._on_custom_size_changed)
        layout.addWidget(self.check_custom_size)

        form = QFormLayout()
        self.spin_target_w = QSpinBox()
        self.spin_target_w.setRange(1, 8192)
        self.spin_target_w.setEnabled(False)
        self.spin_target_w.valueChanged.connect(self._on_manual_size_changed)
        form.addRow("宽度", self.spin_target_w)

        self.spin_target_h = QSpinBox()
        self.spin_target_h.setRange(1, 8192)
        self.spin_target_h.setEnabled(False)
        self.spin_target_h.valueChanged.connect(self._on_manual_size_changed)
        form.addRow("高度", self.spin_target_h)
        layout.addLayout(form)

        self.btn_process = QPushButton("开始扩图")
        self.btn_process.setStyleSheet("background-color: #00a8ff; color: white; padding: 8px;")
        self.btn_process.clicked.connect(self._on_process)
        layout.addWidget(self.btn_process)

        layout.addStretch()

    def _on_ratio_changed(self):
        self._update_target_size()

    def _update_target_size(self):
        image = self.viewer.get_image()
        if image is None:
            self.size_label.setText("目标尺寸: -")
            return

        ratio_name = self.ratio_combo.currentText()
        rw, rh = self.PRESET_RATIOS[ratio_name]
        scale = self.scale_spin.value()

        orig_w, orig_h = image.size
        short_side = min(orig_w, orig_h)
        new_short = short_side * scale

        if rw >= rh:
            target_w = new_short
            target_h = int(new_short * rh / rw)
        else:
            target_h = new_short
            target_w = int(new_short * rw / rh)

        # 确保不小于原图
        target_w = max(target_w, orig_w)
        target_h = max(target_h, orig_h)

        self._target_size = (target_w, target_h)
        self.size_label.setText(f"目标尺寸: {target_w} x {target_h}")

        # 如果未勾选自定义尺寸，同步更新自定义输入框的默认值
        if not self.check_custom_size.isChecked():
            self.spin_target_w.blockSignals(True)
            self.spin_target_h.blockSignals(True)
            self.spin_target_w.setValue(target_w)
            self.spin_target_h.setValue(target_h)
            self.spin_target_w.blockSignals(False)
            self.spin_target_h.blockSignals(False)

    def _on_custom_size_changed(self, state):
        checked = state == Qt.CheckState.Checked.value
        self.spin_target_w.setEnabled(checked)
        self.spin_target_h.setEnabled(checked)
        if checked:
            # 勾选时，把当前自动计算值填入自定义框
            self._update_target_size()

    def _on_manual_size_changed(self):
        if self.check_custom_size.isChecked():
            target_w = self.spin_target_w.value()
            target_h = self.spin_target_h.value()
            self._target_size = (target_w, target_h)
            self.size_label.setText(f"目标尺寸: {target_w} x {target_h} (自定义)")

    def get_target_size(self) -> tuple:
        if self.check_custom_size.isChecked():
            return (self.spin_target_w.value(), self.spin_target_h.value())
        self._update_target_size()
        return getattr(self, "_target_size", None)

    def get_anchor(self) -> str:
        anchor_name = self.anchor_combo.currentText()
        return self.ANCHORS.get(anchor_name, "center")

    def set_process_callback(self, callback):
        self.process_callback = callback

    def _on_process(self):
        if self.process_callback:
            self.process_callback(self)

    def on_mouse_press(self, event):
        pass

    def on_mouse_move(self, event):
        pass

    def on_mouse_release(self, event):
        pass
