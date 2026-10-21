"""提醒调度器 - 休息/眨眼定时器与状态机的纯逻辑层

设计要点：
- 不依赖 tkinter，只依赖注入的 ``TimerBackend``（after / after_cancel），
  因此可用假时钟做单元测试，覆盖"暂停后恢复""跳过休息""设置变更"等分支。
- 对外只暴露 start / stop / apply_settings / skip_rest，
  UI 通过构造参数注入回调，不在调度器内部直接操作窗口。
"""

import logging
from typing import Callable, Protocol

from ..config.settings import Settings

logger = logging.getLogger(__name__)


class TimerBackend(Protocol):
    """最小定时器接口，Tk 的根窗口即满足该协议。"""

    def after(self, ms: int, func: Callable) -> str: ...

    def after_cancel(self, timer_id: str) -> None: ...


class ReminderScheduler:
    """按 Settings 驱动休息与眨眼两类提醒"""

    def __init__(
        self,
        backend: TimerBackend,
        on_rest: Callable[[], None],
        on_blink: Callable[[], None],
        is_busy: Callable[[], bool] | None = None,
    ):
        """
        Args:
            backend: 定时器后端（通常是 tk.Tk 根窗口）
            on_rest: 休息时间到，由上层展示休息蒙版
            on_blink: 眨眼时间到，由上层展示眨眼蒙版
            is_busy: 返回 True 时跳过本次眨眼（蒙版正在显示等）
        """
        self._backend = backend
        self._on_rest = on_rest
        self._on_blink = on_blink
        self._is_busy = is_busy or (lambda: False)

        self._settings = Settings()
        self._rest_timer = None
        self._blink_timer = None
        self._running = False
        self._blink_paused = False
        self._in_rest = False

    # ---- 生命周期 ----

    def start(self, settings: Settings):
        """启动调度（settings.paused 为 True 时仅记录状态，不排定时器）"""
        self._settings = settings
        self._running = True
        if settings.paused:
            logger.info("程序已暂停，未启动提醒定时器")
            return
        self._schedule_rest()
        self._resume_blink()

    def stop(self):
        """停止全部定时器并复位状态"""
        self._running = False
        self._in_rest = False
        self._cancel_rest()
        self._stop_blink()

    def apply_settings(self, settings: Settings):
        """设置变更后重建定时器；避免在休息遮罩期间打断当前休息。"""
        self._settings = settings
        if not self._running:
            return

        if settings.paused:
            self._cancel_rest()
            self._stop_blink()
            self._in_rest = False
            logger.info("所有提醒已暂停")
            return

        logger.info("所有提醒已恢复")
        if not self._in_rest:
            self._schedule_rest()
            self._resume_blink()
        # 休息进行中：保持眨眼暂停，等 skip_rest 时统一恢复

    # ---- 休息 ----

    def skip_rest(self):
        """用户跳过（或休息自然结束）后，重新开始下一轮休息计时"""
        self._in_rest = False
        self._resume_blink()
        self._schedule_rest()

    @property
    def in_rest(self) -> bool:
        return self._in_rest

    def _schedule_rest(self):
        self._cancel_rest()
        if not self._running or self._settings.paused:
            return
        interval_ms = max(1, int(self._settings.rest_interval * 60 * 1000))
        self._rest_timer = self._backend.after(interval_ms, self._on_rest_trigger)

    def _cancel_rest(self):
        if self._rest_timer is not None:
            self._backend.after_cancel(self._rest_timer)
            self._rest_timer = None

    def _on_rest_trigger(self):
        self._rest_timer = None
        if not self._running or self._settings.paused:
            return
        logger.info("休息时间到")
        self._in_rest = True
        self._blink_paused = True
        # 取消已在排队的眨眼定时器，避免"欠下的"周期在休息结束后立即补发
        self._stop_blink()
        self._on_rest()

    # ---- 眨眼 ----

    def _schedule_blink(self):
        self._stop_blink()
        if not self._running or self._settings.paused or self._blink_paused:
            return
        interval_ms = max(1, int(self._settings.blink_interval * 1000))
        self._blink_timer = self._backend.after(interval_ms, self._on_blink_trigger)

    def _stop_blink(self):
        if self._blink_timer is not None:
            self._backend.after_cancel(self._blink_timer)
            self._blink_timer = None

    def _resume_blink(self):
        self._blink_paused = False
        self._schedule_blink()

    def _on_blink_trigger(self):
        self._blink_timer = None
        if self._is_busy():
            # 蒙版占用中（例如休息尚未结束），延后一个周期而不是直接丢弃节奏
            self._schedule_blink()
            return
        self._on_blink()
        self._schedule_blink()