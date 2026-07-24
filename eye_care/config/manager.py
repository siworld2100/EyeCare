"""配置管理器 - 负责配置文件的读写"""

import os
import sys
import json
import logging
from .settings import Settings

logger = logging.getLogger(__name__)


def _get_app_dir():
    """获取程序所在目录（兼容打包后）"""
    if getattr(sys, 'frozen', False):
        # 打包后：exe 所在的目录
        return os.path.dirname(sys.executable)
    else:
        # 开发模式：项目根目录
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ConfigManager:
    """配置文件读写管理"""

    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        Args:
            config_path: 配置文件路径，默认为 data/config.json
        """
        if config_path is None:
            app_dir = _get_app_dir()
            config_path = os.path.join(app_dir, "data", "config.json")
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
