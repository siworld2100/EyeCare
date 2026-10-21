"""配置管理器 - 负责配置文件的读写（原子写入 + 宽容降级）"""

import json
import logging
import os
import sys
import tempfile

from .settings import Settings

logger = logging.getLogger(__name__)

APP_NAME = "EyeCare"


def _get_config_dir() -> str:
    """获取配置文件目录（保存到用户 AppData）"""
    if sys.platform == "win32":
        # Windows: %LOCALAPPDATA%\EyeCare
        return os.path.join(os.environ.get("LOCALAPPDATA", ""), APP_NAME)
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/EyeCare
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    # Linux: ~/.config/EyeCare
    return os.path.join(os.path.expanduser("~"), ".config", APP_NAME)


class ConfigManager:
    """配置文件读写管理"""

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = os.path.join(_get_config_dir(), "config.json")
        self.config_path = config_path
        self._settings: Settings | None = None
        logger.info("配置文件路径: %s", self.config_path)

    @property
    def settings(self) -> Settings:
        """获取当前配置（首次访问时懒加载）"""
        if self._settings is None:
            self._settings = self.load()
        return self._settings

    def load(self) -> Settings:
        """从文件加载配置；文件缺失或损坏时返回默认配置。"""
        if not os.path.exists(self.config_path):
            logger.info("配置文件不存在，使用默认配置")
            return Settings()
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("配置文件加载成功: %s", self.config_path)
            return Settings.from_dict(data)
        except (OSError, ValueError) as exc:
            logger.warning("配置文件读取失败，使用默认配置: %s", exc)
            return Settings()

    def save(self, settings: Settings | None = None) -> bool:
        """原子保存配置到文件。

        先写临时文件再 os.replace，避免写入中途崩溃导致配置文件被截断。
        返回 False 表示写入失败（不抛异常，保证调用方界面流程不中断）。
        """
        if settings is not None:
            self._settings = settings
        if self._settings is None:
            return False

        directory = os.path.dirname(self.config_path) or "."
        tmp_path = None
        try:
            os.makedirs(directory, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(
                dir=directory, prefix=".config-", suffix=".tmp"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._settings.to_dict(), f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.config_path)
            logger.info("配置已保存: %s", self.config_path)
            return True
        except OSError as exc:
            logger.error("配置保存失败: %s", exc)
            return False
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def update(self, **kwargs) -> Settings:
        """更新配置项并保存（未知字段记日志后忽略）"""
        settings = self.settings
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
            else:
                logger.warning("未知配置项: %s", key)
        self.save()
        return settings
