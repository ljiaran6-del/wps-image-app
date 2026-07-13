import io
from typing import Optional
from PIL import Image, ImageFilter
from openai import OpenAI
import httpx


class AIService:
    """AI 服务：封装 OpenAI gpt-image-2 的图像编辑能力"""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = "gpt-image-2"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client: Optional[OpenAI] = None
        if api_key:
            self._build_client()

    def _build_client(self):
        """根据当前配置构建 OpenAI 客户端"""
        kwargs = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        self.client = OpenAI(**kwargs)

    def set_config(self, api_key: str = None, base_url: str = None, model: str = None):
        """设置或更新配置"""
        if api_key is not None:
            self.api_key = api_key
        if base_url is not None:
            self.base_url = base_url
        if model is not None:
            self.model = model
        if self.api_key:
            self._build_client()
        else:
            self.client = None

    def _validate(self):
        if not self.client:
            raise RuntimeError("未设置 OpenAI API Key，请在设置中配置")

    def _pil_to_file(self, image: Image.Image, format: str = "PNG", filename: str = "image.png"):
        """将 PIL Image 转为 OpenAI SDK 可识别的文件对象"""
        buffer = io.BytesIO()
        # 处理 mask：OpenAI 要求 mask 是 RGBA 透明 PNG
        if filename == "mask.png" and image.mode != "RGBA":
            image = image.convert("RGBA")
        # RGBA 不能保存为 JPEG
        if format == "JPEG" and image.mode == "RGBA":
            image = image.convert("RGB")
        image.save(buffer, format=format)
        buffer.name = filename
        buffer.seek(0)
        return buffer

    def erase(self, image: Image.Image, mask: Image.Image) -> Image.Image:
        """AI消除：根据 mask 消除选中区域并自然修复"""
        return self.edit_region(
            image,
            mask,
            prompt="Remove only the content inside the selected masked area and fill it naturally to match the surrounding content. "
                   "Keep everything outside the masked area completely unchanged. "
                   "Make the filled area seamless and consistent with the rest of the image.",
            blend_with_mask=True,
        )

    def remove_watermark(self, image: Image.Image, mask: Image.Image) -> Image.Image:
        """AI去水印：去除选中区域的水印"""
        return self.edit_region(
            image,
            mask,
            prompt="Remove the watermark from this area and fill it naturally. "
                   "The filled area should match the surrounding texture, color, and lighting.",
            blend_with_mask=True,
        )

    def _blend_with_mask(self, original: Image.Image, edited: Image.Image, mask: Image.Image) -> Image.Image:
        """把编辑结果按 mask 与原图混合：mask 内用编辑结果，mask 外用原图，边缘羽化过渡"""
        import numpy as np

        # 统一为 RGBA
        orig = original.convert("RGBA").resize(edited.size, Image.Resampling.LANCZOS)
        edit = edited.convert("RGBA")
        # 把 mask 缩放到编辑结果尺寸
        mask_resized = mask.resize(edited.size, Image.Resampling.NEAREST)
        # 羽化 mask 边缘，让接缝更自然（羽化半径按尺寸自适应，5~15 像素）
        feather = max(5, min(edited.width, edited.height) // 200)
        mask_blur = mask_resized.filter(ImageFilter.GaussianBlur(radius=feather))
        mask_array = np.array(mask_blur).astype(np.float32) / 255.0
        mask_4ch = np.stack([mask_array] * 4, axis=-1)

        orig_array = np.array(orig).astype(np.float32)
        edit_array = np.array(edit).astype(np.float32)
        blended = orig_array * (1 - mask_4ch) + edit_array * mask_4ch
        return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8))

    def edit_region(self, image: Image.Image, mask: Image.Image, prompt: str, blend_with_mask: bool = False) -> Image.Image:
        """AI局部改图：根据提示词修改 mask 区域"""
        self._validate()

        # 更新当前使用的模型
        self.model = self.model or "gpt-image-2"

        # 确保 mask 是单通道灰度图
        if mask.mode != "L":
            mask = mask.convert("L")

        # 确保 image 和 mask 尺寸一致（mask 用 NEAREST 保持硬边缘，避免编辑区域扩散）
        if image.size != mask.size:
            mask = mask.resize(image.size, Image.Resampling.NEAREST)

        # 记录原始尺寸，用于后续缩放回原始尺寸
        original_size = image.size

        # OpenAI image edit API 要求 image 和 mask 必须和 size 参数一致
        api_size = self._get_optimal_size(image.size)
        api_w, api_h = map(int, api_size.split("x"))

        # 缩放 image 和 mask 到 API 支持尺寸（mask 用 NEAREST 保持硬边缘）
        if image.size != (api_w, api_h):
            image_for_api = image.resize((api_w, api_h), Image.Resampling.LANCZOS)
            mask_for_api = mask.resize((api_w, api_h), Image.Resampling.NEAREST)
        else:
            image_for_api = image
            mask_for_api = mask

        # 调用 OpenAI image edit API
        try:
            response = self.client.images.edit(
                model=self.model,
                image=self._pil_to_file(image_for_api, "PNG", "image.png"),
                mask=self._pil_to_file(mask_for_api, "PNG", "mask.png"),
                prompt=prompt,
                n=1,
                size=api_size,
            )

            # 获取返回的图片（支持 url 或 b64_json）
            import base64
            image_data = response.data[0]
            if image_data.url:
                with httpx.Client(timeout=120) as client:
                    result_bytes = client.get(image_data.url).content
            elif image_data.b64_json:
                result_bytes = base64.b64decode(image_data.b64_json)
            else:
                raise RuntimeError("API 未返回图片数据")
            result_image = Image.open(io.BytesIO(result_bytes))

            if result_image.mode != "RGBA":
                result_image = result_image.convert("RGBA")

            # 如果原始尺寸不是 API 尺寸，缩放回原始尺寸
            if result_image.size != original_size:
                result_image = result_image.resize(original_size, Image.Resampling.LANCZOS)

            # 后处理：按 mask 把编辑结果与原图混合，防止模型扩散到 mask 外
            if blend_with_mask:
                result_image = self._blend_with_mask(image, result_image, mask)

            return result_image

        except Exception as e:
            raise RuntimeError(f"AI 编辑失败: {str(e)}")

    def outpaint(self, image: Image.Image, target_size: tuple, anchor: str = "center") -> Image.Image:
        """AI扩图：将图片扩展到目标尺寸"""
        self._validate()

        orig_w, orig_h = image.size
        target_w, target_h = target_size

        if target_w < orig_w or target_h < orig_h:
            raise ValueError("扩图目标尺寸必须大于原图尺寸")

        # 计算原图在新画布中的位置
        if anchor == "center":
            x, y = (target_w - orig_w) // 2, (target_h - orig_h) // 2
        elif anchor == "top":
            x, y = (target_w - orig_w) // 2, 0
        elif anchor == "bottom":
            x, y = (target_w - orig_w) // 2, target_h - orig_h
        elif anchor == "left":
            x, y = 0, (target_h - orig_h) // 2
        elif anchor == "right":
            x, y = target_w - orig_w, (target_h - orig_h) // 2
        else:
            x, y = (target_w - orig_w) // 2, (target_h - orig_h) // 2

        # 创建新画布（白色背景）
        new_image = Image.new("RGBA", target_size, (255, 255, 255, 255))
        new_image.paste(image, (x, y))

        # 创建 mask：原图区域为黑色（保留），扩展区域为白色（编辑）
        mask = Image.new("L", target_size, 255)
        mask.paste(Image.new("L", image.size, 0), (x, y))

        prompt = (
            "Extend this image naturally beyond its original boundaries. "
            "Preserve the original content in the center and seamlessly generate "
            "the surrounding area to match the style, lighting, and composition."
        )

        return self.edit_region(new_image, mask, prompt)

    def _get_optimal_size(self, size: tuple) -> str:
        """根据图片尺寸选择 OpenAI image edit API 支持的尺寸"""
        width, height = size
        # OpenAI image edit 支持的尺寸
        if width == height:
            return "1024x1024"
        elif width > height:
            return "1536x1024"
        else:
            return "1024x1536"
