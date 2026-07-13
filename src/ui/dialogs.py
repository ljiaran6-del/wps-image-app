from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QLabel, QWidget
)
from PySide6.QtCore import Qt


class APISettingsDialog(QDialog):
    """API 设置对话框：支持设置 BASE_URL、API_KEY、MODEL"""

    def __init__(self, parent=None, api_key: str = "", base_url: str = "", model: str = "gpt-image-2"):
        super().__init__(parent)
        self.setWindowTitle("API 设置")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # 说明文字
        desc = QLabel("配置 OpenAI 兼容 API，支持自定义 BASE_URL、API_KEY 和模型名称。\n"
                      "留空 BASE_URL 则使用 OpenAI 官方地址。")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #333333; font-size: 12px;")
        layout.addWidget(desc)

        # 表单
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.base_url_edit = QLineEdit(base_url)
        self.base_url_edit.setPlaceholderText("例如：https://api.openai.com/v1")
        form.addRow("BASE_URL:", self.base_url_edit)

        self.api_key_edit = QLineEdit(api_key)
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("请输入 API Key")
        form.addRow("API_KEY:", self.api_key_edit)

        self.model_edit = QLineEdit(model)
        self.model_edit.setPlaceholderText("例如：gpt-image-2")
        form.addRow("MODEL:", self.model_edit)

        layout.addLayout(form)

        # 按钮
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        # 给对话框内所有 QLabel 设置深色样式，避免被全局白字样式覆盖
        self.setStyleSheet("""
            APISettingsDialog {
                background-color: #f5f5f5;
            }
            APISettingsDialog QLabel {
                color: #333333;
            }
            APISettingsDialog QLineEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 6px;
                border-radius: 4px;
            }
            APISettingsDialog QPushButton {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #aaaaaa;
                padding: 6px 16px;
                min-width: 60px;
            }
        """)

    def get_values(self) -> dict:
        return {
            "base_url": self.base_url_edit.text().strip(),
            "api_key": self.api_key_edit.text().strip(),
            "model": self.model_edit.text().strip() or "gpt-image-2",
        }
