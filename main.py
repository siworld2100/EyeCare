"""护眼程序 - 主入口

通过定时休息和眨眼提醒帮助用户保护眼睛，减少视觉疲劳。
"""

import sys
import logging
import threading
import tkinter as tk
from tkinter import messagebox

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("EyeCare")

from eye_care.config.manager import ConfigManager
from eye_care.core.timer import TimerManager
from eye_care.core.rest import RestManager
from eye_care.core.blink import BlinkManager
from eye_care.ui.overlay import Overlay
from eye_care.ui.settings_gui import SettingsGUI
from eye_care.ui.tray import TrayManager
from eye_care.system.autostart import AutoStart


class EyeCareApp:
    """护眼程序主类"""

    def __init__(self):
        logger.info("护眼程序启动")

        # 配置管理
        self.config_manager = ConfigManager()

        # 核心逻辑
        self.timer_manager = TimerManager()
        self.rest_manager = RestManager()
        self.blink_manager = BlinkManager()

        # 界面
        self.overlay = Overlay(on_skip=self._on_rest_skip)
        self.settings_gui = SettingsGUI(on_save=self._on_settings_save)
        self.tray = TrayManager(
            on_settings=self._open_settings,
            on_exit=self._exit_app
        )

        # 同步开机自启状态
        self._sync_autostart()

    def _sync_autostart(self):
        """同步配置中的开机自启状态到系统"""
        settings = self.config_manager.settings
        AutoStart.set_enabled(settings.autostart)

    def start(self):
        """启动程序"""
        settings = self.config_manager.settings

        # 设置回调
        self.timer_manager.set_callbacks(
            rest_callback=self._on_rest_trigger,
            blink_callback=self._on_blink_trigger
        )
        self.timer_manager.update_intervals(
            settings.rest_interval,
            settings.blink_interval
        )

        # 设置休息和眨眼的蒙版回调
        self.rest_manager.set_overlay_callback(self._handle_overlay)
        self.rest_manager.update_params(settings.rest_duration, settings.rest_opacity)
        self.blink_manager.set_overlay_callback(self._handle_overlay)
        self.blink_manager.update_params(settings.blink_duration, settings.blink_opacity)

        # 启动定时器
        self.timer_manager.start()

        # 启动系统托盘
        self.tray.start()

        logger.info("护眼程序已就绪 - 休息间隔: %d分钟, 眨眼间隔: %d秒",
                     settings.rest_interval, settings.blink_interval)

    def _handle_overlay(self, action: str, duration: int, opacity: int):
        """统一处理蒙版显示/隐藏（在主线程中执行）"""
        if action == "show_rest":
            # 休息触发时暂停眨眼
            self.timer_manager.pause_blink()
            # 在新线程中显示蒙版（避免阻塞）
            threading.Thread(
                target=self.overlay.show_rest,
                args=(duration, opacity),
                daemon=True
            ).start()
        elif action == "show_blink":
            threading.Thread(
                target=self.overlay.show_blink,
                args=(duration, opacity),
                daemon=True
            ).start()
        elif action == "hide":
            self.overlay.hide()
            # 休息结束，恢复眨眼
            if self.rest_manager.is_resting is False:
                self.timer_manager.resume_blink()

    def _on_rest_trigger(self):
        """休息定时器触发回调"""
        logger.info("休息时间到")
        settings = self.config_manager.settings
        self.rest_manager.update_params(settings.rest_duration, settings.rest_opacity)
        self.rest_manager.trigger_rest()

    def _on_blink_trigger(self):
        """眨眼定时器触发回调"""
        settings = self.config_manager.settings
        self.blink_manager.update_params(settings.blink_duration, settings.blink_opacity)
        self.blink_manager.trigger_blink()

    def _on_rest_skip(self):
        """用户跳过休息"""
        self.rest_manager.skip_rest()
        # 恢复眨眼定时器
        self.timer_manager.resume_blink()

    def _on_settings_save(self, settings_dict: dict):
        """设置保存回调"""
        from eye_care.config.settings import Settings
        new_settings = Settings.from_dict(settings_dict)
        self.config_manager.save(new_settings)

        # 更新所有模块的参数
        self.timer_manager.update_intervals(
            new_settings.rest_interval,
            new_settings.blink_interval
        )
        self.rest_manager.update_params(new_settings.rest_duration, new_settings.rest_opacity)
        self.blink_manager.update_params(new_settings.blink_duration, new_settings.blink_opacity)

        # 更新开机自启
        AutoStart.set_enabled(new_settings.autostart)

        # 重启定时器以应用新间隔
        self.timer_manager.stop()
        self.timer_manager.start()

        logger.info("设置已更新并生效")

    def _open_settings(self):
        """打开设置界面"""
        settings = self.config_manager.settings.to_dict()
        # 在主线程中打开设置界面
        threading.Thread(
            target=self.settings_gui.show,
            args=(settings,),
            daemon=True
        ).start()

    def _exit_app(self):
        """退出程序"""
        logger.info("护眼程序退出")
        self.timer_manager.stop()
        self.tray.stop()
        self.overlay.hide()
        sys.exit(0)


def main():
    app = EyeCareApp()
    app.start()

    # 保持主线程运行（托盘图标在后台线程）
    try:
        while True:
            # 使用事件循环保持程序运行
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        app._exit_app()


if __name__ == "__main__":
    main()
