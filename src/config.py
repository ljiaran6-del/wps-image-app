import json
import os
from pathlib import Path


class Config:
    """应用配置管理"""

    DEFAULT_CONFIG = {
        "openai_api_key": "",
        "openai_base_url": "",
        "openai_model": "gpt-image-2",
        "default_save_format": "png",
        "default_save_path": "",
        "history_max_steps": 50,
        "default_brush_size": 20,
        "default_annotation_color": "#FF0000",
        "default_annotation_width": 3,
    }

    def __init__(self, config_path: str = None):
        if config_path is None:
            # 配置文件放在项目根目录
            self.config_path = Path(__file__).parent.parent / "config.json"
        else:
            self.config_path = Path(config_path)

        self._data = {}
        self.load()

    def load(self):
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._data = {**self.DEFAULT_CONFIG, **loaded}
            except Exception as e:
                print(f"加载配置文件失败: {e}，使用默认配置")
                self._data = self.DEFAULT_CONFIG.copy()
        else:
            self._data = self.DEFAULT_CONFIG.copy()
            self.save()

    def save(self):
        """保存配置文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    @property
    def openai_api_key(self) -> str:
        return self.get("openai_api_key", "")

    @openai_api_key.setter
    def openai_api_key(self, value: str):
        self.set("openai_api_key", value)

    @property
    def openai_base_url(self) -> str:
        return self.get("openai_base_url", "")

    @openai_base_url.setter
    def openai_base_url(self, value: str):
        self.set("openai_base_url", value)

    @property
    def openai_model(self) -> str:
        return self.get("openai_model", "gpt-image-2")

    @openai_model.setter
    def openai_model(self, value: str):
        self.set("openai_model", value)

    @property
    def history_max_steps(self) -> int:
        return self.get("history_max_steps", 50)

    @property
    def default_save_format(self) -> str:
        return self.get("default_save_format", "png")
