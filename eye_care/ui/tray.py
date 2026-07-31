"""系统托盘 - 最小化到托盘，提供设置和退出菜单"""

import os
import sys
import logging
import threading
from typing import Callable
import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


def _get_base_path():
    """获取基础路径（兼容打包后）"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


_ICON_PATH = os.path.join(_get_base_path(), "eye_care.ico")
_PNG_ICON_PATH = os.path.join(_get_base_path(), "eye_care_icon.png")


def _load_icon_image() -> Image.Image:
    """加载托盘图标"""
    # 优先使用 png 图标
    if os.path.exists(_PNG_ICON_PATH):
        return Image.open(_PNG_ICON_PATH)
    # 使用 ico 图标
    if os.path.exists(_ICON_PATH):
        return Image.open(_ICON_PATH)
    # 兜底：动态生成
    return _create_fallback_icon()


def _create_fallback_icon() -> Image.Image:
    """兜底：动态生成图标"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 眼睛轮廓 - 外层
    draw.ellipse([8, 16, 56, 48], outline=(100, 200, 100, 255), width=3)
    # 眼球
    draw.ellipse([22, 22, 42, 42], fill=(100, 200, 100, 255))
    # 瞳孔
    draw.ellipse([28, 28, 36, 36], fill=(30, 80, 30, 255))
    # 高光
    draw.ellipse([30, 28, 33, 31], fill=(255, 255, 255, 200))

    return img


class TrayManager:
    """系统托盘管理器"""

    def __init__(self, on_settings: Callable = None, on_exit: Callable = None):
        """
        初始化托盘管理器
        Args:
            on_settings: 打开设置界面的回调
            on_exit: 退出程序的回调
        """
        self._on_settings = on_settings
        self._on_exit = on_exit
        self._tray_icon: pystray.Icon = None
        self._thread: threading.Thread = None

    def start(self):
        """启动系统托盘（在后台线程中运行）"""
        icon_image = _load_icon_image()

        menu = pystray.Menu(
            pystray.MenuItem("设置", self._menu_settings, default=True),
            pystray.MenuItem("退出", self._menu_exit),
        )

        self._tray_icon = pystray.Icon(
            "EyeCare",
            icon_image,
            "护眼程序",
            menu
        )

        self._thread = threading.Thread(target=self._tray_icon.run, daemon=True)
        self._thread.start()
        logger.info("系统托盘已启动")

    def stop(self):
        """停止系统托盘"""
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None
        logger.info("系统托盘已停止")

    def _menu_settings(self, icon, item):
        """菜单 - 设置"""
        logger.debug("托盘菜单: 打开设置")
        if self._on_settings:
            self._on_settings()

    def _menu_exit(self, icon, item):
        """菜单 - 退出"""
        logger.debug("托盘菜单: 退出程序")
        if self._on_exit:
            self._on_exit()
