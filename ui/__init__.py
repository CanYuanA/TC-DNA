"""
游戏脚本UI框架

这个包提供了一个基于JSON配置的UI框架，用于创建游戏脚本的参数设置界面。
"""

from .main_interface import MainInterface
from .settings_window import SettingsWindow
from utils.config_manager import ConfigManager
from utils.global_manager import (
    GlobalManager, global_manager,
    get_global, set_global, add_global_listener, remove_global_listener,
    log_info, log_warning, log_error, log_debug, log_critical, log_message,
    get_log_widget, is_log_available
)

__version__ = "1.0.0"
__author__ = "Claude Code"

__all__ = [
    'MainInterface', 'SettingsWindow', 'ConfigManager', 'GlobalManager',
    'global_manager', 'get_global', 'set_global', 'add_global_listener', 'remove_global_listener',
    'log_info', 'log_warning', 'log_error', 'log_debug', 'log_critical', 'log_message',
    'get_log_widget', 'is_log_available'
]