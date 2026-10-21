"""显示器枚举 - 支持多屏时在每个屏幕上铺设遮罩

Windows 下通过 EnumDisplayMonitors 按物理像素坐标获取工作区；
其他平台与异常场景回退到 tkinter 的主屏尺寸。
"""

import ctypes
import logging
import sys
from typing import NamedTuple

logger = logging.getLogger(__name__)


class MonitorRect(NamedTuple):
    left: int
    top: int
    width: int
    height: int

    @property
    def geometry(self) -> str:
        """tkinter 的 geometry 字符串：宽x高+左+上"""
        return f"{self.width}x{self.height}+{self.left}+{self.top}"


def _enable_dpi_awareness() -> None:
    """声明进程 DPI 感知，避免 Windows 缩放 125%/150% 下坐标被系统二次换算。

    必须在创建 Tk 窗口之前调用；失败时静默忽略（老系统无此 API）。
    """
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_SYSTEM_DPI_AWARE
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            logger.debug("无法启用 DPI 感知，使用系统默认缩放")


def get_monitors(root) -> list[MonitorRect]:
    """返回所有显示器的物理像素矩形，按 X 坐标排序。

    Args:
        root: 任意已存在的 tkinter 窗口，用于取兜底尺寸；为空时返回空列表，
              由调用方决定降级策略。
    """
    if root is None:
        return []
    if sys.platform == "win32":
        monitors = _enum_windows_monitors()
        if monitors:
            # 多屏时必须铺满整块屏幕，否则主副屏之间会露出一条 1px 缝
            return sorted(monitors, key=lambda m: (m.left, m.top))
    return [MonitorRect(0, 0, root.winfo_screenwidth(), root.winfo_screenheight())]


def _enum_windows_monitors() -> list[MonitorRect]:
    try:
        from ctypes import wintypes
    except ImportError:  # pragma: no cover - 非 Windows
        return []

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", wintypes.DWORD),
            ("szDevice", wintypes.WCHAR * 32),
        ]

    monitors: list[MonitorRect] = []
    try:
        monitor_enum_proc = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(RECT),
            wintypes.LPARAM,
        )

        def _callback(hmonitor, hdc, lprect, lparam):
            info = MONITORINFOEXW()
            info.cbSize = ctypes.sizeof(MONITORINFOEXW)
            if ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
                # 使用 rcMonitor（整块屏幕）而非 rcWork，保证遮罩覆盖任务栏区域
                rect = info.rcMonitor
                monitors.append(
                    MonitorRect(
                        left=rect.left,
                        top=rect.top,
                        width=max(1, rect.right - rect.left),
                        height=max(1, rect.bottom - rect.top),
                    )
                )
            return True

        ctypes.windll.user32.EnumDisplayMonitors(
            None, None, monitor_enum_proc(_callback), 0
        )
    except (AttributeError, OSError) as exc:
        logger.warning("枚举显示器失败，回退为单屏: %s", exc)
        return []
    return monitors
