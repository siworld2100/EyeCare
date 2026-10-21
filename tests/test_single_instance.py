"""SingleInstanceGuard 单元测试（Windows 互斥量语义）"""

import unittest

from eye_care.system.single_instance import SingleInstanceGuard


class SingleInstanceGuardTest(unittest.TestCase):
    def test_second_acquire_fails_windows(self):
        """同一进程内第二次 acquire 同名互斥量应失败（互斥量已存在）。"""
        first = SingleInstanceGuard("EyeCare_Test_Mutex_XYZ")
        second = SingleInstanceGuard("EyeCare_Test_Mutex_XYZ")
        try:
            self.assertTrue(first.acquire(), "首次获取应成功")
            self.assertFalse(second.acquire(), "同名第二次获取应失败")
        finally:
            first.release()

    def test_release_allows_reacquire(self):
        guard = SingleInstanceGuard("EyeCare_Test_Mutex_ABC")
        try:
            self.assertTrue(guard.acquire())
        finally:
            guard.release()

        again = SingleInstanceGuard("EyeCare_Test_Mutex_ABC")
        try:
            self.assertTrue(again.acquire(), "释放后应可重新获取")
        finally:
            again.release()

    def test_unique_names_both_succeed(self):
        a = SingleInstanceGuard("EyeCare_Test_Mutex_A")
        b = SingleInstanceGuard("EyeCare_Test_Mutex_B")
        try:
            self.assertTrue(a.acquire())
            self.assertTrue(b.acquire())
        finally:
            a.release()
            b.release()

    def test_acquire_is_idempotent(self):
        guard = SingleInstanceGuard("EyeCare_Test_Mutex_IDEM")
        try:
            self.assertTrue(guard.acquire())
            self.assertTrue(guard.acquire(), "同一对象重复 acquire 应幂等返回 True")
        finally:
            guard.release()


if __name__ == "__main__":
    unittest.main()
