"""护眼程序 - 主入口

通过定时休息和眨眼提醒帮助用户保护眼睛，减少视觉疲劳。
基于 tkinter 事件循环架构，所有 GUI 操作在主线程执行。
"""

import sys
import os
import logging
from queue import Queue, Empty

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("EyeCare")

import tkinter as tk
from eye_care.config.manager import ConfigManager
from eye_care.config.settings import Settings
from eye_care.ui.overlay import Overlay
from eye_care.ui.settings_gui import SettingsGUI
from eye_care.ui.tray import TrayManager
from eye_care.system.autostart import AutoStart


class EyeCareApp:
    """护眼程序主类 - 基于 tkinter 事件循环"""

    def __init__(self):
        logger.info("护眼程序启动")

        # tkinter 主窗口（隐藏，仅用于事件循环）
        self._root = tk.Tk()
        self._root.withdraw()
        self._ui_actions = Queue()
        self._closing = False
        self._root.after(50, self._process_ui_actions)

        # 配置管理
        self.config_manager = ConfigManager()

        # 界面组件
        self.overlay = Overlay(on_skip=self._on_rest_skip)
        self.settings_gui = SettingsGUI(on_save=self._on_settings_save)
        self.tray = TrayManager(
            on_settings=lambda: self._post_ui_action(self._open_settings),
            on_exit=lambda: self._post_ui_action(self._exit_app)
        )

        # 定时器 ID
        self._rest_timer_id = None
        self._blink_timer_id = None
        self._blink_paused = False

        # 同步开机自启状态
        self._sync_autostart()

    def _post_ui_action(self, callback):
        """Queue work requested by a non-Tk thread for the Tk main thread."""
        self._ui_actions.put(callback)

    def _process_ui_actions(self):
        """Run queued tray actions from Tk's event loop."""
        try:
            while True:
                self._ui_actions.get_nowait()()
        except Empty:
            pass
        if not self._closing:
            self._root.after(50, self._process_ui_actions)

    def _sync_autostart(self):
        """同步配置中的开机自启状态到系统"""
        settings = self.config_manager.settings
        AutoStart.set_enabled(settings.autostart)

    def start(self):
        """启动程序"""
        settings = self.config_manager.settings

        # 启动定时器（如果未暂停）
        if not settings.paused:
            self._start_rest_timer()
            self._start_blink_timer()
        else:
            logger.info("程序启动时已暂停")

        # 启动系统托盘
        self.tray.start()

        logger.info("护眼程序已就绪 - 休息间隔: %d分钟, 眨眼间隔: %d秒, 暂停: %s",
                     settings.rest_interval, settings.blink_interval, settings.paused)

        # 进入 tkinter 事件循环
        self._root.mainloop()

    # ---- 定时器管理（基于 tkinter after）----

    def _start_rest_timer(self):
        """启动休息定时器"""
        if self._rest_timer_id:
            self._root.after_cancel(self._rest_timer_id)
        settings = self.config_manager.settings
        interval_ms = settings.rest_interval * 60 * 1000
        self._rest_timer_id = self._root.after(interval_ms, self._on_rest_trigger)

    def _start_blink_timer(self):
        """启动眨眼定时器"""
        if self._blink_timer_id:
            self._root.after_cancel(self._blink_timer_id)
        if self._blink_paused:
            return
        settings = self.config_manager.settings
        interval_ms = settings.blink_interval * 1000
        self._blink_timer_id = self._root.after(interval_ms, self._on_blink_trigger)

    def _stop_blink_timer(self):
        """停止眨眼定时器"""
        if self._blink_timer_id:
            self._root.after_cancel(self._blink_timer_id)
            self._blink_timer_id = None

    def _pause_blink(self):
        """暂停眨眼"""
        self._blink_paused = True
        self._stop_blink_timer()

    def _resume_blink(self):
        """恢复眨眼"""
        self._blink_paused = False
        self._start_blink_timer()

    # ---- 回调处理 ----

    def _on_rest_trigger(self):
        """休息定时器触发"""
        logger.info("休息时间到")
        settings = self.config_manager.settings
        self._pause_blink()
        self.overlay.show_rest(settings.rest_duration, settings.rest_opacity)

    def _on_blink_trigger(self):
        """眨眼定时器触发"""
        if self._blink_paused or self.overlay.is_showing:
            return
        settings = self.config_manager.settings
        self.overlay.show_blink(settings.blink_duration, settings.blink_opacity)
        # 重新启动下一次眨眼定时器
        self._start_blink_timer()

    def _on_rest_skip(self):
        """用户跳过休息"""
        self.overlay.hide()
        self._resume_blink()
        self._start_rest_timer()

    def _on_settings_save(self, settings_dict: dict):
        """设置保存回调"""
        new_settings = Settings.from_dict(settings_dict)
        self.config_manager.save(new_settings)

        # 更新开机自启
        AutoStart.set_enabled(new_settings.autostart)

        # 处理暂停状态
        if new_settings.paused:
            # 暂停：停止所有定时器，隐藏蒙版
            self._pause_blink()
            if self._rest_timer_id:
                self._root.after_cancel(self._rest_timer_id)
                self._rest_timer_id = None
            self.overlay.hide()
            logger.info("所有提醒已暂停")
        else:
            # 恢复：重启定时器
            self._start_rest_timer()
            self._resume_blink()
            logger.info("所有提醒已恢复")

        logger.info("设置已更新并生效")

    def _open_settings(self):
        """打开设置界面"""
        settings = self.config_manager.settings.to_dict()
        self.settings_gui.show(settings, master=self._root)

    def _exit_app(self):
        """退出程序"""
        logger.info("护眼程序退出")
        self._closing = True
        self.tray.stop()
        self.overlay.hide()
        self._root.quit()
        self._root.destroy()


def main():
    app = EyeCareApp()
    app.start()


if __name__ == "__main__":
    main()
