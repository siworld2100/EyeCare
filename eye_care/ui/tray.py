"""系统托盘 - 最小化到托盘，提供设置和退出菜单

托盘运行在独立线程，菜单回调必须回到 Tk 主线程执行，
因此这里只负责把回调原样转交给上层（上层已做线程调度）。
"""

import logging
import threading
from typing import Callable

import pystray

from .icons import load_app_icon

logger = logging.getLogger(__name__)


class TrayManager:
    """系统托盘管理器"""

    def __init__(
        self,
        on_settings: Callable[[], None] | None = None,
        on_exit: Callable[[], None] | None = None,
        on_toggle_pause: Callable[[], None] | None = None,
        is_paused: Callable[[], bool] | None = None,
    ):
        """
        Args:
            on_settings: 打开设置界面的回调
            on_exit: 退出程序的回调
            on_toggle_pause: 暂停/恢复切换回调
            is_paused: 返回当前是否暂停，用于菜单勾选状态
        """
        self._on_settings = on_settings
        self._on_exit = on_exit
        self._on_toggle_pause = on_toggle_pause
        self._is_paused = is_paused or (lambda: False)
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None

    def start(self):
        """启动系统托盘（在后台守护线程中运行）"""
        menu = pystray.Menu(
            pystray.MenuItem("打开设置", self._menu_settings, default=True),
            pystray.MenuItem(
                "暂停提醒",
                self._menu_toggle_pause,
                checked=lambda _item: self._is_paused(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._menu_exit),
        )
        self._icon = pystray.Icon(
            "EyeCare", load_app_icon(64), "护眼程序", menu
        )
        self._thread = threading.Thread(
            target=self._icon.run, name="EyeCareTray", daemon=True
        )
        self._thread.start()
        logger.info("系统托盘已启动")

    def stop(self):
        """停止系统托盘"""
        icon, self._icon = self._icon, None
        if icon is not None:
            try:
                icon.stop()
            except Exception as exc:  # pystray 在线程未就绪时可能抛任意异常
                logger.debug("停止托盘失败: %s", exc)
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        logger.info("系统托盘已停止")

    def refresh_menu(self):
        """状态变化后刷新菜单勾选态"""
        if self._icon is not None:
            try:
                self._icon.update_menu()
            except Exception as exc:
                logger.debug("刷新托盘菜单失败: %s", exc)

    # ---- 菜单回调（托盘线程） ----

    def _menu_settings(self, _icon, _item):
        logger.debug("托盘菜单: 打开设置")
        if self._on_settings:
            self._on_settings()

    def _menu_toggle_pause(self, _icon, _item):
        logger.debug("托盘菜单: 切换暂停")
        if self._on_toggle_pause:
            self._on_toggle_pause()

    def _menu_exit(self, _icon, _item):
        logger.debug("托盘菜单: 退出程序")
        if self._on_exit:
            self._on_exit()
