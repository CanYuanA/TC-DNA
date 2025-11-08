#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏脚本全局变量管理器

统一管理游戏中所有全局状态和数据，包括窗口句柄、配置、状态等
提供线程安全的全局变量访问和管理功能
"""

import threading
import time
import json
import os
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging


class GameState(Enum):
    """游戏状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
    CONNECTING = "connecting"


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class WindowInfo:
    """窗口信息"""
    title: str = ""
    handle: int = 0
    width: int = 0
    height: int = 0
    x: int = 0
    y: int = 0
    visible: bool = True
    active: bool = False


@dataclass
class GameProcessInfo:
    """游戏进程信息"""
    process_id: int = 0
    process_name: str = ""
    window_handle: int = 0
    memory_usage: int = 0
    cpu_usage: float = 0.0
    start_time: float = 0.0


@dataclass
class ScriptConfig:
    """脚本配置信息"""
    script_name: str = ""
    config_data: Optional[Dict[str, Any]] = None
    auto_start: bool = False
    enabled: bool = True

    def __post_init__(self):
        if self.config_data is None:
            self.config_data = {}


class GlobalEvent:
    """全局事件类"""

    def __init__(self, event_type: str, data: Any = None):
        self.event_type = event_type
        self.data = data
        self.timestamp = time.time()

    def __repr__(self):
        return f"GlobalEvent(type='{self.event_type}', time={self.timestamp})"


class GlobalManager:
    """全局变量管理器"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化全局管理器"""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._lock = threading.RLock()
        self._data = {}
        self._listeners = {}
        self._event_history = []
        self._max_history = 1000

        # 设置默认变量
        self._set_default_values()

        # 设置日志
        self._setup_logging()

    def _setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger('GameScript.GlobalManager')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _set_default_values(self):
        """设置默认全局变量"""
        default_values = {
            # 窗口相关
            'main_window': None,
            'settings_window': None,
            'current_window': None,
            'game_window': WindowInfo(),

            # 游戏进程相关
            'game_process': GameProcessInfo(),
            'game_state': GameState.STOPPED,
            'game_mode': 'general',

            # 脚本相关
            'active_scripts': {},
            'script_configs': {},

            # UI相关
            'ui_scale': 1.0,
            'theme': 'default',
            'language': 'zh-CN',

            # 性能监控
            'fps': 0,
            'memory_usage': 0,
            'cpu_usage': 0.0,

            # 状态标志
            'initialized': False,
            'debug_mode': False,
            'auto_save': True,

            # 时间戳
            'start_time': time.time(),
            'last_activity': time.time(),
        }

        for key, value in default_values.items():
            self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取全局变量

        Args:
            key: 变量键名
            default: 默认值

        Returns:
            变量值
        """
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any, notify: bool = True) -> None:
        """
        设置全局变量

        Args:
            key: 变量键名
            value: 变量值
            notify: 是否通知监听器
        """
        with self._lock:
            old_value = self._data.get(key)
            self._data[key] = value

            # 记录时间戳
            if key != 'last_activity':
                self._data['last_activity'] = time.time()

            self.logger.debug(f"设置全局变量: {key} = {value}")

            # 发送事件通知
            if notify and old_value != value:
                self._notify_listeners(key, value, old_value)

    def delete(self, key: str) -> bool:
        """
        删除全局变量

        Args:
            key: 变量键名

        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._data:
                del self._data[key]
                self.logger.debug(f"删除全局变量: {key}")
                return True
            return False

    def has_key(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 变量键名

        Returns:
            是否存在
        """
        with self._lock:
            return key in self._data

    def get_all(self) -> Dict[str, Any]:
        """
        获取所有全局变量

        Returns:
            所有全局变量的副本
        """
        with self._lock:
            return self._data.copy()

    def clear(self, keep_default: bool = True):
        """
        清空所有变量

        Args:
            keep_default: 是否保留默认变量
        """
        with self._lock:
            if keep_default:
                default_keys = set()
                # 重新设置默认变量
                old_data = self._data.copy()
                self._set_default_values()
                # 恢复非默认变量
                for key, value in old_data.items():
                    if key not in self._data:
                        self._data[key] = value
            else:
                self._data.clear()
                self._set_default_values()

    def update(self, data: Dict[str, Any], notify: bool = True):
        """
        批量更新变量

        Args:
            data: 要更新的数据
            notify: 是否通知监听器
        """
        with self._lock:
            for key, value in data.items():
                self.set(key, value, notify)

    # 事件监听机制

    def add_listener(self, key: str, callback: Callable):
        """
        添加事件监听器

        Args:
            key: 要监听的变量键名
            callback: 回调函数，参数为 (key, new_value, old_value)
        """
        with self._lock:
            if key not in self._listeners:
                self._listeners[key] = []
            self._listeners[key].append(callback)

    def remove_listener(self, key: str, callback: Callable) -> bool:
        """
        移除事件监听器

        Args:
            key: 变量键名
            callback: 回调函数

        Returns:
            是否移除成功
        """
        with self._lock:
            if key in self._listeners and callback in self._listeners[key]:
                self._listeners[key].remove(callback)
                return True
            return False

    def _notify_listeners(self, key: str, new_value: Any, old_value: Any):
        """通知监听器"""
        event = GlobalEvent('variable_changed', {
            'key': key,
            'new_value': new_value,
            'old_value': old_value
        })

        # 记录事件历史
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # 调用监听器
        if key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(key, new_value, old_value)
                except Exception as e:
                    self.logger.error(f"监听器执行失败 ({key}): {e}")

    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[GlobalEvent]:
        """
        获取事件历史

        Args:
            event_type: 事件类型过滤
            limit: 返回数量限制

        Returns:
            事件列表
        """
        with self._lock:
            events = self._event_history
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            return events[-limit:]

    # 游戏相关方法

    def set_game_state(self, state: GameState):
        """设置游戏状态"""
        old_state = self.get('game_state')
        self.set('game_state', state)
        if old_state != state:
            self.logger.info(f"游戏状态改变: {old_state} -> {state}")

    def set_game_window(self, window_info: WindowInfo):
        """设置游戏窗口信息"""
        self.set('game_window', window_info)
        self.logger.debug(f"设置游戏窗口: {window_info.title}")

    def register_script(self, script_name: str, config: ScriptConfig):
        """注册脚本"""
        self.set(f'script.{script_name}', config)
        self.logger.info(f"注册脚本: {script_name}")

    def unregister_script(self, script_name: str):
        """取消注册脚本"""
        self.delete(f'script.{script_name}')
        self.logger.info(f"取消注册脚本: {script_name}")

    def get_script(self, script_name: str) -> Optional[ScriptConfig]:
        """获取脚本配置"""
        return self.get(f'script.{script_name}')

    def get_all_scripts(self) -> Dict[str, ScriptConfig]:
        """获取所有脚本"""
        scripts = {}
        with self._lock:
            for key, value in self._data.items():
                if key.startswith('script.') and isinstance(value, ScriptConfig):
                    scripts[key[7:]] = value  # 去掉 'script.' 前缀
        return scripts

    # 窗口管理方法

    def set_main_window(self, window):
        """设置主窗口"""
        self.set('main_window', window)

    def get_main_window(self):
        """获取主窗口"""
        return self.get('main_window')

    def set_settings_window(self, window):
        """设置设置窗口"""
        self.set('settings_window', window)

    def get_settings_window(self):
        """获取设置窗口"""
        return self.get('settings_window')

    # 配置持久化

    def save_state(self, filepath: str = "ui/global_state.json"):
        """
        保存全局状态

        Args:
            filepath: 保存路径
        """
        try:
            with self._lock:
                state_data = {}
                for key, value in self._data.items():
                    # 跳过无法序列化的对象
                    if isinstance(value, (type, type(None), str, int, float, bool, dict, list)):
                        state_data[key] = value
                    else:
                        # 尝试转换为字典
                        try:
                            if hasattr(value, '__dict__'):
                                state_data[key] = asdict(value)
                            else:
                                state_data[key] = str(value)
                        except:
                            state_data[key] = None

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2, default=str)

            self.logger.info(f"全局状态已保存到: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"保存全局状态失败: {e}")
            return False

    def load_state(self, filepath: str = "ui/global_state.json"):
        """
        加载全局状态

        Args:
            filepath: 加载路径
        """
        try:
            if not os.path.exists(filepath):
                self.logger.warning(f"状态文件不存在: {filepath}")
                return False

            with open(filepath, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            with self._lock:
                # 只加载不包含敏感对象的数据
                for key, value in state_data.items():
                    if key in ['ui_scale', 'theme', 'language', 'debug_mode', 'auto_save']:
                        self._data[key] = value

            self.logger.info(f"全局状态已从 {filepath} 加载")
            return True
        except Exception as e:
            self.logger.error(f"加载全局状态失败: {e}")
            return False

    # 统计信息

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                'total_variables': len(self._data),
                'listeners_count': sum(len(listeners) for listeners in self._listeners.values()),
                'event_history_size': len(self._event_history),
                'uptime': time.time() - self.get('start_time', time.time()),
                'last_activity': self.get('last_activity'),
            }

    def reset(self):
        """重置所有状态"""
        self.logger.info("重置全局管理器状态")
        self.clear(keep_default=True)
        self._event_history.clear()
        self._set_default_values()

    def __repr__(self):
        return f"GlobalManager(stats={self.get_stats()})"


# 全局实例
global_manager = GlobalManager()

# 便利函数
def get_global(key: str, default: Any = None) -> Any:
    """获取全局变量"""
    return global_manager.get(key, default)

def set_global(key: str, value: Any, notify: bool = True):
    """设置全局变量"""
    return global_manager.set(key, value, notify)

def add_global_listener(key: str, callback: Callable):
    """添加全局变量监听器"""
    return global_manager.add_listener(key, callback)

def remove_global_listener(key: str, callback: Callable):
    """移除全局变量监听器"""
    return global_manager.remove_listener(key, callback)

# 日志便利函数
def log_info(message: str):
    """记录信息日志"""
    log_widget = get_global('log_widget')
    if log_widget and hasattr(log_widget, 'add_log'):
        log_widget.add_log("INFO", message)
    else:
        # 回退到标准日志记录器
        logging.getLogger('GameScript').info(message)

def log_warning(message: str):
    """记录警告日志"""
    log_widget = get_global('log_widget')
    if log_widget and hasattr(log_widget, 'add_log'):
        log_widget.add_log("WARNING", message)
    else:
        logging.getLogger('GameScript').warning(message)

def log_error(message: str):
    """记录错误日志"""
    log_widget = get_global('log_widget')
    if log_widget and hasattr(log_widget, 'add_log'):
        log_widget.add_log("ERROR", message)
    else:
        logging.getLogger('GameScript').error(message)

def log_debug(message: str):
    """记录调试日志"""
    log_widget = get_global('log_widget')
    if log_widget and hasattr(log_widget, 'add_log'):
        log_widget.add_log("DEBUG", message)
    else:
        logging.getLogger('GameScript').debug(message)

def log_critical(message: str):
    """记录严重错误日志"""
    log_widget = get_global('log_widget')
    if log_widget and hasattr(log_widget, 'add_log'):
        log_widget.add_log("CRITICAL", message)
    else:
        logging.getLogger('GameScript').critical(message)

def log_message(level: str, message: str):
    """记录通用日志消息"""
    log_widget = get_global('log_widget')
    if log_widget and hasattr(log_widget, 'add_log'):
        log_widget.add_log(level.upper(), message)
    else:
        logger = logging.getLogger('GameScript')
        level_lower = level.lower()
        if level_lower == 'debug':
            logger.debug(message)
        elif level_lower == 'info':
            logger.info(message)
        elif level_lower == 'warning':
            logger.warning(message)
        elif level_lower == 'error':
            logger.error(message)
        elif level_lower == 'critical':
            logger.critical(message)
        else:
            logger.info(message)

def get_log_widget():
    """获取日志组件"""
    return get_global('log_widget')

def is_log_available() -> bool:
    """检查日志组件是否可用"""
    log_widget = get_global('log_widget')
    return log_widget is not None and hasattr(log_widget, 'add_log')