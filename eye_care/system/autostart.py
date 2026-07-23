"""开机自启管理 - Windows 注册表操作"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

# 注册表路径
AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "EyeCare"


class AutoStart:
    """开机自启动管理"""

    @staticmethod
    def is_enabled() -> bool:
        """检查是否已设置开机自启"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, APP_NAME)
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            logger.warning("检查开机自启状态失败: %s", e)
            return False

    @staticmethod
    def enable():
        """启用开机自启"""
        try:
            import winreg
            # 获取程序路径
            if getattr(sys, 'frozen', False):
                # 打包后的 exe
                exe_path = sys.executable
            else:
                # 开发模式
                exe_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'

            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            logger.info("已启用开机自启: %s", exe_path)
            return True
        except Exception as e:
            logger.error("启用开机自启失败: %s", e)
            return False

    @staticmethod
    def disable():
        """禁用开机自启"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE)
            try:
                winreg.DeleteValue(key, APP_NAME)
                logger.info("已禁用开机自启")
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
            return True
        except Exception as e:
            logger.error("禁用开机自启失败: %s", e)
            return False

    @staticmethod
    def set_enabled(enabled: bool):
        """设置开机自启状态"""
        if enabled:
            return AutoStart.enable()
        else:
            return AutoStart.disable()
