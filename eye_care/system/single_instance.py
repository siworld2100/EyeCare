"""单实例锁 - 防止程序重复启动

Windows 用命名互斥量实现：第一个实例持有锁，后续实例检测到锁已存在即退出。
非 Windows 平台回退为端口绑定探测（开发环境够用）。

用法：
    guard = SingleInstanceGuard("EyeCare")
    if not guard.acquire():
        logger.info("已有实例在运行，退出")
        sys.exit(0)
"""

import logging
import sys

logger = logging.getLogger(__name__)


class SingleInstanceGuard:
    """跨平台单实例保护"""

    def __init__(self, app_name: str = "EyeCare"):
        self._app_name = app_name
        self._handle = None  # Windows 互斥量句柄，需持有引用防止被 GC 释放
        self._acquired = False

    def acquire(self) -> bool:
        """尝试获取单实例锁，返回是否成功。"""
        if self._acquired:
            return True
        if sys.platform == "win32":
            self._acquired = self._acquire_windows()
        else:
            self._acquired = self._acquire_fallback()
        return self._acquired

    def release(self):
        """释放锁（进程退出时也会自动释放，这里用于显式清理）。"""
        if self._handle is not None:
            try:
                import ctypes

                ctypes.windll.kernel32.CloseHandle(self._handle)
            except OSError:
                pass
            self._handle = None
        self._acquired = False

    # ---- Windows ----

    def _acquire_windows(self) -> bool:
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            ERROR_ALREADY_EXISTS = 183
            mutex_name = f"Global\\{self._app_name}_SingleInstance"
            # 请求初始拥有权；若互斥量已存在则立即返回句柄并置 last error
            handle = kernel32.CreateMutexW(None, True, mutex_name)
            if not handle:
                logger.warning("创建互斥量失败，允许继续运行（降级为不锁）")
                return True  # 锁失效时宁可双开也不能阻止程序启动
            if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
                kernel32.CloseHandle(handle)
                logger.info("检测到已有实例在运行")
                return False
            self._handle = handle
            return True
        except OSError as exc:
            logger.warning("单实例锁异常: %s（降级为不锁）", exc)
            return True

    # ---- 非 Windows 兜底 ----

    def _acquire_fallback(self) -> bool:
        try:
            import socket

            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.bind(("127.0.0.1", 0))  # 占用一个本地端口作为标记
            self._sock.listen(1)
            return True
        except OSError as exc:
            logger.warning("单实例锁(端口)获取失败: %s", exc)
            return False
