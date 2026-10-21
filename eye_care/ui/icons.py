"""图标加载 - 托盘与窗口共用的图标资源解析（带兜底绘制）"""

import logging
import os

from PIL import Image, ImageDraw

from ..paths import resource_path

logger = logging.getLogger(__name__)

ICO_PATH = resource_path("eye_care.ico")
PNG_PATH = resource_path("eye_care_icon.png")

_ICON_CACHE = None


def load_app_icon(size: int = 64) -> Image.Image:
    """加载应用图标；资源缺失时动态绘制兜底图标。"""
    global _ICON_CACHE
    if _ICON_CACHE is not None:
        if _ICON_CACHE.size == (size, size):
            return _ICON_CACHE
        return _ICON_CACHE.resize((size, size), Image.LANCZOS)

    for path in (PNG_PATH, ICO_PATH):
        if os.path.exists(path):
            try:
                with Image.open(path) as source:
                    _ICON_CACHE = source.convert("RGBA").copy()
                return _ICON_CACHE
            except OSError as exc:
                logger.warning("图标加载失败(%s): %s", path, exc)

    logger.info("未找到图标资源，使用内置绘制图标")
    _ICON_CACHE = _draw_fallback_icon()
    return _ICON_CACHE


def ico_path() -> str:
    """窗口 iconbitmap 用的 ico 路径（不存在时返回空串）。"""
    return ICO_PATH if os.path.exists(ICO_PATH) else ""


def _draw_fallback_icon() -> Image.Image:
    """兜底：动态生成眼睛图标"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 16, 56, 48], outline=(100, 200, 100, 255), width=3)
    draw.ellipse([22, 22, 42, 42], fill=(100, 200, 100, 255))
    draw.ellipse([28, 28, 36, 36], fill=(30, 80, 30, 255))
    draw.ellipse([30, 28, 33, 31], fill=(255, 255, 255, 200))
    return img
