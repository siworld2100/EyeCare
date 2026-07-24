"""配置管理器 - 负责配置文件的读写"""

import os
import sys
import json
import logging
from .settings import Settings

logger = logging.getLogger(__name__)

APP_NAME = "EyeCare"


def _get_config_dir():
    """获取配置文件目录（保存到用户 AppData）"""
    if sys.platform == "win32":
        # Windows: %LOCALAPPDATA%\EyeCare
        return os.path.join(os.environ.get("LOCALAPPDATA", ""), APP_NAME)
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/EyeCare
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    else:
        # Linux: ~/.config/EyeCare
        return os.path.join(os.path.expanduser("~"), ".config", APP_NAME)


class ConfigManager:
    """配置文件读写管理"""

    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        Args:
            config_path: 配置文件路径，默认为用户目录下的 config.json
        """
        if config_path is None:
            config_dir = _get_config_dir()
            config_path = os.path.join(config_dir, "config.json")
        self.config_path = config_path
        self._settings = None
        logger.info("配置文件路径: %s", self.config_path)

    @property
    def settings(self) -> Settings:
        """获取当前配置"""
        if self._settings is None:
            self._settings = self.load()
        return self._settings

    def load(self) -> Settings:
        """从文件加载配置，文件不存在则返回默认配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info("配置文件加载成功: %s", self.config_path)
                return Settings.from_dict(data)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("配置文件读取失败，使用默认配置: %s", e)
                return Settings()
        else:
            logger.info("配置文件不存在，使用默认配置")
            return Settings()

    def save(self, settings: Settings = None):
        """保存配置到文件"""
        if settings is not None:
            self._settings = settings
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._settings.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info("配置已保存: %s", self.config_path)

    def update(self, **kwargs) -> Settings:
        """更新配置项并保存"""
        for key, value in kwargs.items():
            if hasattr(self._settings, key):
                setattr(self._settings, key, value)
            else:
                logger.warning("未知配置项: %s", key)
        self.save()
        return self._settings
