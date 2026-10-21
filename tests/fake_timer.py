"""假定时器后端 - 用可控时钟替代 tkinter.after，便于对调度器做确定性测试"""

from typing import Callable


class FakeTimerBackend:
    """记录所有已排定的回调，由测试显式推进时钟。"""

    def __init__(self):
        self.now = 0
        self._timers: dict[int, tuple[int, Callable[[], None]]] = {}
        self._next_id = 1
        self.cancelled: list[int] = []

    def after(self, ms: int, func: Callable[[], None]) -> int:
        timer_id = self._next_id
        self._next_id += 1
        self._timers[timer_id] = (self.now + max(0, int(ms)), func)
        return timer_id

    def after_cancel(self, timer_id: int) -> None:
        if self._timers.pop(timer_id, None) is not None:
            self.cancelled.append(timer_id)

    # ---- 测试辅助 ----

    @property
    def pending(self) -> int:
        return len(self._timers)

    def advance(self, ms: int) -> None:
        """推进时钟并执行到期的回调（按到期时间顺序，支持回调内重新排程）。"""
        target = self.now + ms
        while True:
            due = [(t, tid) for tid, (t, _) in self._timers.items() if t <= target]
            if not due:
                break
            due_time, timer_id = min(due)
            entry = self._timers.pop(timer_id)
            self.now = due_time
            entry[1]()
        self.now = target
