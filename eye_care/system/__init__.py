"""系统平台相关能力（开机自启、显示器枚举、单实例锁）"""

from .autostart import AutoStart
from .monitors import MonitorRect, get_monitors
from .single_instance import SingleInstanceGuard

__all__ = ["AutoStart", "MonitorRect", "SingleInstanceGuard", "get_monitors"]
