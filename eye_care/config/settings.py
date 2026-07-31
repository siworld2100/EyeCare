"""配置数据类 - 定义所有程序参数及默认值"""

from dataclasses import dataclass, field, asdict
import json
import math


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
        """从字典创建配置对象，忽略未知字段"""
        if not isinstance(data, dict):
            return cls()

        integer_limits = {
            "rest_interval": (1, None),
            "rest_duration": (5, None),
            "rest_opacity": (0, 100),
            "blink_interval": (10, None),
            "blink_opacity": (0, 100),
        }
        filtered = {}
        for key, (minimum, maximum) in integer_limits.items():
            value = data.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                if value >= minimum and (maximum is None or value <= maximum):
                    filtered[key] = value

        duration = data.get("blink_duration")
        if isinstance(duration, (int, float)) and not isinstance(duration, bool):
            if math.isfinite(duration) and duration >= 0.5:
                filtered["blink_duration"] = float(duration)

        for key in ("autostart", "paused"):
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
