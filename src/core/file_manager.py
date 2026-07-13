from pathlib import Path
from PIL import Image
from typing import Optional, List


class FileManager:
    """文件管理器：负责图片的打开、保存、文件夹遍历"""

    SUPPORTED_OPEN_FORMATS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")
    SUPPORTED_SAVE_FORMATS = ("PNG", "JPG", "JPEG", "WEBP", "BMP")

    def __init__(self):
        self.current_path: Optional[Path] = None
        self.current_image: Optional[Image.Image] = None
        self.folder_images: List[Path] = []
        self.current_index: int = -1

    def open(self, path: str) -> Optional[Image.Image]:
        """打开一张图片"""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        ext = file_path.suffix.lower()
        if ext not in self.SUPPORTED_OPEN_FORMATS:
            raise ValueError(f"不支持的文件格式: {ext}")

        # 打开图片并转换为 RGBA 模式（GIF 取第一帧）
        img = Image.open(file_path)
        if getattr(img, "is_animated", False):
            img.seek(0)

        # 统一转换为 RGBA，便于后续处理
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        elif img.mode == "RGB":
            img = img.convert("RGBA")

        self.current_path = file_path
        self.current_image = img.copy()

        # 更新文件夹图片列表
        self._refresh_folder_images()

        return self.current_image.copy()

    def _refresh_folder_images(self):
        """刷新当前文件夹中的图片列表"""
        if self.current_path is None:
            self.folder_images = []
            self.current_index = -1
            return

        folder = self.current_path.parent
        self.folder_images = sorted(
            [p for p in folder.iterdir() if p.suffix.lower() in self.SUPPORTED_OPEN_FORMATS]
        )
        try:
            self.current_index = self.folder_images.index(self.current_path)
        except ValueError:
            self.current_index = -1

    def next_image(self) -> Optional[Image.Image]:
        """下一张图片"""
        if not self.folder_images:
            return None
        self.current_index = (self.current_index + 1) % len(self.folder_images)
        return self.open(str(self.folder_images[self.current_index]))

    def prev_image(self) -> Optional[Image.Image]:
        """上一张图片"""
        if not self.folder_images:
            return None
        self.current_index = (self.current_index - 1) % len(self.folder_images)
        return self.open(str(self.folder_images[self.current_index]))

    def save(self, image: Image.Image, path: Optional[str] = None, format: Optional[str] = None) -> str:
        """
        保存图片
        :param image: 要保存的图片
        :param path: 保存路径，为 None 时覆盖原图
        :param format: 保存格式，为 None 时根据 path 推断
        :return: 实际保存的路径
        """
        if path is None:
            if self.current_path is None:
                raise ValueError("没有当前文件，无法覆盖保存")
            save_path = self.current_path
        else:
            save_path = Path(path)

        if format is None:
            format = save_path.suffix.lstrip(".").upper()
            if format == "JPG":
                format = "JPEG"

        if format not in self.SUPPORTED_SAVE_FORMATS:
            raise ValueError(f"不支持的保存格式: {format}")

        # 保存为 JPG 时不支持透明通道
        save_image = image
        if format in ("JPEG", "JPG") and image.mode == "RGBA":
            save_image = Image.new("RGB", image.size, (255, 255, 255))
            save_image.paste(image, mask=image.split()[3])

        save_image.save(save_path, format=format)

        # 如果是覆盖保存，更新当前路径和图片
        if path is None:
            self.current_path = save_path
            self.current_image = image.copy()

        return str(save_path)

    def get_file_info(self) -> dict:
        """获取当前文件信息"""
        if self.current_image is None:
            return {}
        return {
            "path": str(self.current_path) if self.current_path else "",
            "name": self.current_path.name if self.current_path else "",
            "width": self.current_image.width,
            "height": self.current_image.height,
            "mode": self.current_image.mode,
        }
