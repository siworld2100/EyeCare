"""眨眼提醒逻辑 - 处理眨眼蒙版的触发和消失"""

import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)


class BlinkManager:
    """眨眼提醒逻辑管理器"""

    def __init__(self):
        self._overlay_callback: Callable = None
        self._duration = 1.5      # 蒙版显示时长（秒）
        self._opacity = 30        # 蒙版透明度
        self._is_showing = False
        self._hide_timer: threading.Timer = None

    @property
    def is_showing(self) -> bool:
        return self._is_showing

    def set_overlay_callback(self, callback: Callable):
        """设置蒙版显示/隐藏回调"""
        self._overlay_callback = callback

    def update_params(self, duration: float, opacity: int):
        """更新眨眼参数"""
        self._duration = duration
        self._opacity = opacity

    def trigger_blink(self):
        """触发眨眼提醒"""
        if self._is_showing:
            return
        self._is_showing = True
        logger.debug("显示眨眼蒙版，时长 %.1f 秒", self._duration)
        if self._overlay_callback:
            self._overlay_callback("show_blink", self._duration, self._opacity)
        # 定时自动隐藏
        self._hide_timer = threading.Timer(self._duration, self._hide)
        self._hide_timer.daemon = True
        self._hide_timer.start()

    def _hide(self):
        """隐藏眨眼蒙版"""
        self._is_showing = False
        if self._overlay_callback:
            self._overlay_callback("hide", 0, 0)
        logger.debug("眨眼蒙版已隐藏")
