"""资源定位 - 统一处理开发模式与 PyInstaller 打包后的资源路径

打包路径规则此前散落在 ui/tray.py 与 ui/settings_gui.py 各自实现，
此处作为唯一入口，避免新增资源时再改多处。
"""

import os
import sys

_DEV_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FROZEN_ROOT = getattr(sys, "_MEIPASS", None)


def resource_path(*parts: str) -> str:
    """返回资源文件的绝对路径。

    Args:
        *parts: 相对于项目根目录（或打包解压目录）的路径片段。
    """
    root = _FROZEN_ROOT or _DEV_ROOT
    return os.path.join(root, *parts)


def app_root() -> str:
    """返回程序根目录（打包后为 exe 所在目录）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return _DEV_ROOT
