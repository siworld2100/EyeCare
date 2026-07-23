"""定时器管理 - 管理休息和眨眼的定时触发"""

import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)


class TimerManager:
    """定时器管理器，控制休息和眨眼提醒的定时触发"""

    def __init__(self):
        self._rest_timer: threading.Timer = None
        self._blink_timer: threading.Timer = None
        self._rest_callback: Callable = None
        self._blink_callback: Callable = None
        self._blink_paused = False
        self._rest_interval = 20 * 60   # 秒
        self._blink_interval = 45       # 秒

    def set_callbacks(self, rest_callback: Callable, blink_callback: Callable):
        """设置回调函数"""
        self._rest_callback = rest_callback
        self._blink_callback = blink_callback

    def update_intervals(self, rest_interval_minutes: int, blink_interval_seconds: int):
        """更新定时器间隔（不重启当前计时）"""
        self._rest_interval = rest_interval_minutes * 60
        self._blink_interval = blink_interval_seconds

    def start(self):
        """启动所有定时器"""
        self.start_rest_timer()
        self.start_blink_timer()
        logger.info("定时器已启动 - 休息间隔: %d分钟, 眨眼间隔: %d秒",
                     self._rest_interval // 60, self._blink_interval)

    def stop(self):
        """停止所有定时器"""
        self.cancel_rest_timer()
        self.cancel_blink_timer()
        logger.info("定时器已停止")

    # ---- 休息定时器 ----

    def start_rest_timer(self):
        """启动休息定时器"""
        self.cancel_rest_timer()
        if self._rest_callback:
            self._rest_timer = threading.Timer(self._rest_interval, self._on_rest)
            self._rest_timer.daemon = True
            self._rest_timer.start()

    def cancel_rest_timer(self):
        """取消休息定时器"""
        if self._rest_timer:
            self._rest_timer.cancel()
            self._rest_timer = None

    def _on_rest(self):
        """休息定时器触发"""
        logger.debug("休息定时器触发")
        if self._rest_callback:
            self._rest_callback()
        # 休息结束后重新启动眨眼定时器需要外部调用 restart_blink_after_rest

    # ---- 眨眼定时器 ----

    def start_blink_timer(self):
        """启动眨眼定时器"""
        self.cancel_blink_timer()
        if self._blink_callback and not self._blink_paused:
            self._blink_timer = threading.Timer(self._blink_interval, self._on_blink)
            self._blink_timer.daemon = True
            self._blink_timer.start()

    def cancel_blink_timer(self):
        """取消眨眼定时器"""
        if self._blink_timer:
            self._blink_timer.cancel()
            self._blink_timer = None

    def _on_blink(self):
        """眨眼定时器触发"""
        if self._blink_paused:
            return
        logger.debug("眨眼定时器触发")
        if self._blink_callback:
            self._blink_callback()
        # 重新启动下一次眨眼定时器
        if not self._blink_paused:
            self.start_blink_timer()

    # ---- 眨眼暂停/恢复（休息时使用）----

    def pause_blink(self):
        """暂停眨眼定时器"""
        self._blink_paused = True
        self.cancel_blink_timer()
        logger.debug("眨眼定时器已暂停")

    def resume_blink(self):
        """恢复眨眼定时器"""
        self._blink_paused = False
        self.start_blink_timer()
        logger.debug("眨眼定时器已恢复")
