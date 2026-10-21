"""护眼程序 - 主入口 / 应用装配层

职责收敛为：装配组件、处理跨线程调度、编排"设置变更 -> 各子系统生效"。
提醒的定时与状态机在 ``eye_care.core.scheduler``，蒙版渲染在 ``eye_care.ui.overlay``。
"""

import logging
import os
import sys
from queue import Empty, Queue
from typing import Callable

import tkinter as tk

from eye_care.config.manager import ConfigManager
from eye_care.config.settings import Settings
from eye_care.core.scheduler import ReminderScheduler
from eye_care.system.autostart import AutoStart
from eye_care.system.monitors import _enable_dpi_awareness
from eye_care.system.single_instance import SingleInstanceGuard
from eye_care.ui.overlay import Overlay
from eye_care.ui.settings_gui import SettingsGUI
from eye_care.ui.tray import TrayManager

logger = logging.getLogger("EyeCare")

_UI_POLL_MS = 50


def _setup_logging() -> None:
    """配置日志：控制台 + 用户目录滚动日志文件（打包为无控制台时只写文件）。"""
    handlers: list[logging.Handler] = []
    log_dir = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "EyeCare"
    )
    try:
        from logging.handlers import RotatingFileHandler

        os.makedirs(log_dir, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                os.path.join(log_dir, "eyecare.log"),
                maxBytes=512 * 1024,
                backupCount=2,
                encoding="utf-8",
            )
        )
    except OSError:
        pass
    if sys.stderr is not None:  # pythonw / --noconsole 下为 None
        handlers.append(logging.StreamHandler(sys.stderr))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers or [logging.NullHandler()],
    )


class EyeCareApp:
    """护眼程序主类 - 基于 tkinter 事件循环"""

    def __init__(self):
        logger.info("护眼程序启动")
        _enable_dpi_awareness()

        # 隐藏的 tkinter 主窗口，仅承载事件循环与定时器
        self._root = tk.Tk()
        self._root.withdraw()
        self._closing = False
        self._ui_actions: Queue[Callable[[], None]] = Queue()

        self.config_manager = ConfigManager()
        settings = self.config_manager.settings

        self.overlay = Overlay(on_skip=self._on_rest_finished)
        self.settings_gui = SettingsGUI(on_save=self._on_settings_save)
        self.scheduler = ReminderScheduler(
            backend=self._root,
            on_rest=self._show_rest,
            on_blink=self._show_blink,
            is_busy=lambda: self.overlay.is_showing,
        )
        self.tray = TrayManager(
            on_settings=lambda: self._post(self._open_settings),
            on_exit=lambda: self._post(self._exit_app),
            on_toggle_pause=lambda: self._post(self._toggle_pause),
            is_paused=lambda: self.config_manager.settings.paused,
        )

        AutoStart.set_enabled(settings.autostart)
        self._root.after(_UI_POLL_MS, self._process_ui_actions)

        # 首次运行（无配置文件）弹出设置主页，让用户直接完成初始配置；
        # 之后照常静默运行在托盘。
        self._first_run = not os.path.exists(self.config_manager.config_path)
        if self._first_run:
            logger.info("首次运行：打开设置主页")
            self._root.after(200, self._open_settings)

    # ---- 跨线程调度 ----

    def _post(self, callback: Callable[[], None]) -> None:
        """把非 Tk 线程（托盘）的回调投递到主线程执行。"""
        if not self._closing:
            self._ui_actions.put(callback)

    def _process_ui_actions(self) -> None:
        try:
            while True:
                self._ui_actions.get_nowait()()
        except Empty:
            pass
        except Exception:  # 单个回调异常不应终止调度循环
            logger.exception("处理界面操作时出错")
        if not self._closing:
            self._root.after(_UI_POLL_MS, self._process_ui_actions)

    # ---- 主流程 ----

    def start(self) -> None:
        settings = self.config_manager.settings
        self.scheduler.start(settings)
        self.tray.start()
        logger.info(
            "护眼程序已就绪 - 休息间隔: %d分钟, 眨眼间隔: %d秒, 暂停: %s",
            settings.rest_interval,
            settings.blink_interval,
            settings.paused,
        )
        try:
            self._root.mainloop()
        finally:
            logger.info("事件循环已退出")

    def _show_rest(self) -> None:
        settings = self.config_manager.settings
        self.overlay.show_rest(settings.rest_duration, settings.rest_opacity)

    def _show_blink(self) -> None:
        settings = self.config_manager.settings
        self.overlay.show_blink(settings.blink_duration, settings.blink_opacity)

    # ---- 事件处理 ----

    def _on_rest_finished(self) -> None:
        """休息结束（倒计时归零或用户跳过）"""
        self.scheduler.skip_rest()

    def _on_settings_save(self, settings_dict: dict) -> bool:
        """设置保存回调，返回是否成功持久化。"""
        new_settings = Settings.from_dict(settings_dict)
        saved = self.config_manager.save(new_settings)
        if not saved:
            logger.warning("配置未落盘，但本次会话继续使用新设置")

        AutoStart.set_enabled(new_settings.autostart)
        self.scheduler.apply_settings(new_settings)
        if new_settings.paused:
            self.overlay.hide()
        self.tray.refresh_menu()
        logger.info("设置已更新并生效")
        return saved

    def _toggle_pause(self) -> None:
        """托盘菜单快速暂停/恢复（无需打开设置窗口）"""
        settings = self.config_manager.settings
        settings.paused = not settings.paused
        self.config_manager.save()
        self.scheduler.apply_settings(settings)
        if settings.paused:
            self.overlay.hide()
        self.tray.refresh_menu()
        logger.info("托盘切换暂停状态: %s", settings.paused)

    def _open_settings(self) -> None:
        self.settings_gui.show(self.config_manager.settings.to_dict(), master=self._root)

    def _exit_app(self) -> None:
        logger.info("护眼程序退出")
        self._closing = True
        self.scheduler.stop()
        self.tray.stop()
        self.overlay.hide()
        self._root.quit()
        self._root.destroy()


def main() -> None:
    _setup_logging()

    # 单实例锁：第二个实例直接退出（幂等，重复获取返回 True 不受影响）
    guard = SingleInstanceGuard("EyeCare")
    if not guard.acquire():
        logger.info("护眼程序已在运行，本次启动退出")
        return

    EyeCareApp().start()
    guard.release()


if __name__ == "__main__":
    main()
