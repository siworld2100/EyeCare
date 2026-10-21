"""配置数据类 - 定义所有程序参数、默认值与边界校验规则"""

import json
import math
from dataclasses import asdict, dataclass
from typing import Any

# 字段 -> (最小值, 最大值, 是否浮点)
# 统一在此声明，供 from_dict / 数据类 / 界面共用同一套边界，
# 避免"界面限制一套、加载校验另一套"的双份真相。
NUMERIC_LIMITS: dict[str, tuple[float, float | None, bool]] = {
    "rest_interval": (1, None, False),
    "rest_duration": (5, None, False),
    "rest_opacity": (0, 100, False),
    "blink_interval": (10, None, False),
    "blink_duration": (0.5, None, True),
    "blink_opacity": (0, 100, False),
}

BOOLEAN_FIELDS = ("autostart", "paused")


def clamp_number(key: str, value: Any) -> int | float | None:
    """按字段规则校验并归一化数值，非法时返回 None。"""
    if key not in NUMERIC_LIMITS or isinstance(value, bool):
        return None
    if not isinstance(value, (int, float)):
        return None

    minimum, maximum, is_float = NUMERIC_LIMITS[key]
    number = float(value)
    if not math.isfinite(number) or number < minimum:
        return None
    if maximum is not None:
        number = min(number, maximum)
    return number if is_float else int(round(number))


@dataclass
class Settings:
    """程序配置数据类"""

    # 休息参数
    rest_interval: int = 20          # 休息间隔（分钟）
    rest_duration: int = 20          # 休息时长（秒）
    rest_opacity: int = 70           # 休息蒙版不透明度（0-100，100为完全不透明/黑色）

    # 眨眼参数
    blink_interval: int = 45         # 眨眼提醒间隔（秒）
    blink_duration: float = 2.0      # 眨眼蒙版显示时长（秒）
    blink_opacity: int = 100         # 眨眼蒙版不透明度（0-100）

    # 系统参数
    autostart: bool = True           # 开机自启动
    paused: bool = False             # 暂停所有提醒

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        """从字典创建配置对象，忽略未知字段并对越界值做裁剪。"""
        if not isinstance(data, dict):
            return cls()

        filtered: dict[str, Any] = {}
        for key in NUMERIC_LIMITS:
            value = clamp_number(key, data.get(key))
            if value is not None:
                filtered[key] = value

        for key in BOOLEAN_FIELDS:
            if isinstance(data.get(key), bool):
                filtered[key] = data[key]

        return cls(**filtered)

    def to_json(self) -> str:
        """序列化为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "Settings":
        """从 JSON 字符串反序列化"""
        return cls.from_dict(json.loads(json_str))
