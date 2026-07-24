"""配置数据类 - 定义所有程序参数及默认值"""

from dataclasses import dataclass, field, asdict
import json


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
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    def to_json(self) -> str:
        """序列化为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "Settings":
        """从 JSON 字符串反序列化"""
        return cls.from_dict(json.loads(json_str))
