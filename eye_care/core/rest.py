"""休息逻辑 - 处理休息触发和结束"""

import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class RestManager:
    """休息逻辑管理器"""

    def __init__(self):
        self._overlay_callback: Callable = None
        self._duration = 20       # 休息时长（秒）
        self._opacity = 70        # 蒙版透明度
        self._is_resting = False
        self._countdown_timer: threading.Timer = None

    @property
    def is_resting(self) -> bool:
        return self._is_resting

    def set_overlay_callback(self, callback: Callable):
        """设置蒙版显示/隐藏回调"""
        self._overlay_callback = callback

    def update_params(self, duration: int, opacity: int):
        """更新休息参数"""
        self._duration = duration
        self._opacity = opacity

    def trigger_rest(self):
        """触发休息"""
        if self._is_resting:
            return
        self._is_resting = True
        logger.info("开始休息，时长 %d 秒", self._duration)
        if self._overlay_callback:
            self._overlay_callback("show_rest", self._duration, self._opacity)
        # 启动倒计时自动结束
        self._countdown_timer = threading.Timer(self._duration, self._auto_end_rest)
        self._countdown_timer.daemon = True
        self._countdown_timer.start()

    def skip_rest(self):
        """跳过休息"""
        if not self._is_resting:
            return
        self._end_rest()

    def _auto_end_rest(self):
        """倒计时结束，自动结束休息"""
        self._end_rest()

    def _end_rest(self):
        """结束休息"""
        if self._countdown_timer:
            self._countdown_timer.cancel()
            self._countdown_timer = None
        self._is_resting = False
        logger.info("休息结束")
        if self._overlay_callback:
            self._overlay_callback("hide", 0, 0)
