import json
import os
from typing import Dict, Any, Optional


class ConfigManager:
    """配置文件管理器"""

    def __init__(self, config_path: str = "user_data/settings.json"):
        """
        初始化配置管理器

        Args:
            config_path: 设置文件路径
        """
        self.config_path = config_path
        self.config_data = {}
        self.load_config()

    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
            else:
                # 如果配置文件不存在，创建默认配置
                self.create_default_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.create_default_config()

    def create_default_config(self) -> None:
        """创建默认配置文件"""
        self.config_data = {}
        self.save_config()

    def save_config(self) -> bool:
        """
        保存配置文件

        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保目录存在
            config_dir = os.path.dirname(self.config_path)
            if config_dir:  # 如果有目录部分
                os.makedirs(config_dir, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的层级键，如 'general.game_path'
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config_data

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key: 配置键，支持点号分隔的层级键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config_data

        # 导航到最后一层
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config_data.copy()

    def set_all(self, config_data: Dict[str, Any]) -> None:
        """设置所有配置"""
        self.config_data = config_data.copy()

    def delete(self, key: str) -> bool:
        """
        删除配置项

        Args:
            key: 配置键

        Returns:
            bool: 是否删除成功
        """
        keys = key.split('.')
        config = self.config_data

        try:
            # 导航到最后一层
            for k in keys[:-1]:
                config = config[k]

            # 删除键
            del config[keys[-1]]
            return True
        except (KeyError, TypeError):
            return False

    def has_key(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 配置键

        Returns:
            bool: 是否存在
        """
        return self.get(key) is not None

    def get_ui_config(self, ui_config_path: str = "config/ui_config.json") -> Dict[str, Any]:
        """
        获取UI配置文件

        Args:
            ui_config_path: UI配置文件路径

        Returns:
            UI配置字典
        """
        try:
            with open(ui_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载UI配置文件失败: {e}")
            return {}

    def export_config(self, export_path: str) -> bool:
        """
        导出配置到文件

        Args:
            export_path: 导出路径

        Returns:
            bool: 是否导出成功
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False

    def import_config(self, import_path: str) -> bool:
        """
        从文件导入配置

        Args:
            import_path: 导入路径

        Returns:
            bool: 是否导入成功
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)

            self.config_data.update(imported_config)
            self.save_config()
            return True
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False