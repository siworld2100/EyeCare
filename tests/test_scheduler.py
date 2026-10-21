"""ReminderScheduler 单元测试：覆盖启动、休息/眨眼触发、跳过、暂停与设置变更"""

import unittest

from eye_care.config.settings import Settings
from eye_care.core.scheduler import ReminderScheduler

from .fake_timer import FakeTimerBackend


class SchedulerTest(unittest.TestCase):
    def setUp(self):
        self.backend = FakeTimerBackend()
        self.rest_count = 0
        self.blink_count = 0
        self.busy = False
        self.scheduler = ReminderScheduler(
            backend=self.backend,
            on_rest=self._on_rest,
            on_blink=self._on_blink,
            is_busy=lambda: self.busy,
        )

    def _on_rest(self):
        self.rest_count += 1

    def _on_blink(self):
        self.blink_count += 1

    def _settings(self, **kwargs) -> Settings:
        base = dict(rest_interval=20, blink_interval=10, paused=False)
        base.update(kwargs)
        return Settings(**base)

    # ---- 启动 ----

    def test_start_schedules_both_timers(self):
        self.scheduler.start(self._settings())
        self.assertEqual(self.backend.pending, 2)

    def test_start_when_paused_schedules_nothing(self):
        self.scheduler.start(self._settings(paused=True))
        self.assertEqual(self.backend.pending, 0)

    # ---- 眨眼 ----

    def test_blink_fires_repeatedly(self):
        self.scheduler.start(self._settings())
        self.backend.advance(10_000)
        self.assertEqual(self.blink_count, 1)
        self.backend.advance(20_000)
        self.assertEqual(self.blink_count, 3)

    def test_blink_skipped_while_busy_but_rhythm_kept(self):
        self.scheduler.start(self._settings())
        self.busy = True
        self.backend.advance(10_000)
        self.assertEqual(self.blink_count, 0)
        self.busy = False
        self.backend.advance(10_000)
        self.assertEqual(self.blink_count, 1)

    # ---- 休息 ----

    def test_rest_pauses_blink_until_skip(self):
        self.scheduler.start(self._settings(rest_interval=1, blink_interval=10))
        self.backend.advance(60_000)
        self.assertEqual(self.rest_count, 1)
        self.assertTrue(self.scheduler.in_rest)
        blinks_before_rest = self.blink_count  # 休息前 50s 内正常触发的 5 次

        self.backend.advance(60_000)
        self.assertEqual(self.blink_count, blinks_before_rest, "休息期间不应弹出眨眼提醒")
        self.assertEqual(self.rest_count, 1)

        self.scheduler.skip_rest()
        self.assertFalse(self.scheduler.in_rest)
        self.backend.advance(10_000)
        self.assertEqual(self.blink_count, blinks_before_rest + 1)

    def test_blink_timer_resets_after_rest(self):
        """休息结束（跳过）后，眨眼应从完整周期重新起算，而不是立刻补发。"""
        self.scheduler.start(self._settings(rest_interval=1, blink_interval=45))
        self.backend.advance(60_000)
        self.assertTrue(self.scheduler.in_rest)
        self.scheduler.skip_rest()
        self.backend.advance(5_000)
        self.assertEqual(self.blink_count, 1)
        self.backend.advance(40_000)
        self.assertEqual(self.blink_count, 2)

    def test_skip_rest_reschedules_next_rest(self):
        self.scheduler.start(self._settings(rest_interval=1))
        self.backend.advance(60_000)
        self.scheduler.skip_rest()
        self.backend.advance(60_000)
        self.assertEqual(self.rest_count, 2)

    def test_rest_interval_change_applies_to_next_round(self):
        self.scheduler.start(self._settings(rest_interval=20))
        self.scheduler.apply_settings(self._settings(rest_interval=1))
        self.backend.advance(60_000)
        self.assertEqual(self.rest_count, 1)

    # ---- 暂停 / 恢复 ----

    def test_pause_cancels_everything_and_resume_restarts(self):
        self.scheduler.start(self._settings(rest_interval=1, blink_interval=10))
        self.scheduler.apply_settings(self._settings(paused=True))
        self.assertEqual(self.backend.pending, 0)

        self.backend.advance(120_000)
        self.assertEqual((self.rest_count, self.blink_count), (0, 0))

        self.scheduler.apply_settings(self._settings(rest_interval=1, blink_interval=10))
        self.backend.advance(60_000)
        self.assertEqual(self.rest_count, 1)

    def test_settings_change_during_rest_keeps_current_rest(self):
        self.scheduler.start(self._settings(rest_interval=1, blink_interval=10))
        self.backend.advance(60_000)
        self.assertTrue(self.scheduler.in_rest)
        blinks_before_rest = self.blink_count
        self.scheduler.apply_settings(self._settings(rest_interval=1, blink_interval=10))
        self.assertTrue(self.scheduler.in_rest, "保存设置不应打断正在进行的休息")
        self.backend.advance(30_000)
        self.assertEqual(self.blink_count, blinks_before_rest)

    def test_stop_clears_state(self):
        self.scheduler.start(self._settings(rest_interval=1))
        self.backend.advance(60_000)
        self.scheduler.stop()
        self.assertFalse(self.scheduler.in_rest)
        self.assertEqual(self.backend.pending, 0)
        self.backend.advance(600_000)
        self.assertEqual(self.rest_count, 1)


if __name__ == "__main__":
    unittest.main()
