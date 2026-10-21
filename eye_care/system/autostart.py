"""开机自启管理 - Windows 注册表操作；非 Windows 平台安全空转"""

import logging
import os
import sys

from ..paths import app_root

logger = logging.getLogger(__name__)

AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "EyeCare"

SUPPORTED = sys.platform == "win32"


def _command_line() -> str:
    """当前可执行入口的命令行（打包后为自身 exe，开发模式为 python main.py）。"""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    main_path = os.path.join(app_root(), "main.py")
    return f'"{sys.executable}" "{main_path}"'


class AutoStart:
    """开机自启动管理"""

    @staticmethod
    def is_enabled() -> bool:
        if not SUPPORTED:
            return False
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_READ
            ) as key:
                winreg.QueryValueEx(key, APP_NAME)
                return True
        except FileNotFoundError:
            return False
        except OSError as exc:
            logger.warning("检查开机自启状态失败: %s", exc)
            return False

    @staticmethod
    def enable() -> bool:
        if not SUPPORTED:
            return False
        try:
            import winreg

            command = _command_line()
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
            logger.info("已启用开机自启: %s", command)
            return True
        except OSError as exc:
            logger.error("启用开机自启失败: %s", exc)
            return False

    @staticmethod
    def disable() -> bool:
        if not SUPPORTED:
            return False
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    logger.info("已禁用开机自启")
                except FileNotFoundError:
                    pass
            return True
        except OSError as exc:
            logger.error("禁用开机自启失败: %s", exc)
            return False

    @staticmethod
    def set_enabled(enabled: bool) -> bool:
        """同步开机自启状态；已处于目标状态时不重复写注册表。"""
        if AutoStart.is_enabled() == bool(enabled):
            return True
        return AutoStart.enable() if enabled else AutoStart.disable()
