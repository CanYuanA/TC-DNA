#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TC-DNA 工具包

提供游戏自动化脚本所需的各种工具模块
"""

# 导入核心工具
from .global_manager import (
    get_global,
    set_global,
    add_global_listener,
    log_info,
    log_warning,
    log_error,
    GlobalManager
)

from .config_manager import ConfigManager

from .window.window_manager import WindowManager, WindowInfo, get_window_manager

# 导入任务管理
from .task.task_manager import TaskManager, get_task_manager
from .task.task_ui import TaskSelector

# 导入输入管理
from .input.input_manager import InputManager
from .input import (
    get_input_manager,
    send_key,
    send_keys,
    send_mouse_click,
    send_mouse_move,
    send_mouse_wheel,
    # 精细键盘控制
    key_down_press,
    key_down_release,
    key_press_and_hold,
    send_key_sequence,
    is_key_pressed,
    wait_for_key_release,
    press_modifiers_precisely,
    release_modifiers_precisely,
    send_chord_key,
    toggle_key,
    send_pressurized_key_sequence,
    # 精细鼠标控制
    mouse_down_press,
    mouse_down_release,
    mouse_press_and_hold,
    send_mouse_sequence,
    press_mouse_precisely,
    send_multi_button_press,
    release_multi_button,
    send_complex_click_sequence,
    simulate_mouse_gesture,
    get_mouse_button_state,
    wait_for_mouse_release,
    # 系统级控制
    simulate_menu_shortcut,
    send_system_command,
    send_raw_input_event,
    # 工具函数
    build_key_lparam,
    build_mouse_lparam
)

# 导入管理功能
from .admin import is_admin

__all__ = [
    # 核心工具
    'get_global',
    'set_global',
    'add_global_listener',
    'log_info',
    'log_warning',
    'log_error',
    'GlobalManager',
    'ConfigManager',

    # 窗口管理
    'WindowManager',
    'WindowInfo',
    'get_window_manager',

    # 任务管理
    'TaskManager',
    'get_task_manager',
    'TaskSelector',

    # 输入管理
    'InputManager',
    'get_input_manager',
    'send_key',
    'send_keys',
    'send_mouse_click',
    'send_mouse_move',
    'send_mouse_wheel',

    # 精细键盘控制
    'key_down_press',
    'key_down_release',
    'key_press_and_hold',
    'send_key_sequence',
    'is_key_pressed',
    'wait_for_key_release',
    'press_modifiers_precisely',
    'release_modifiers_precisely',
    'send_chord_key',
    'toggle_key',
    'send_pressurized_key_sequence',

    # 精细鼠标控制
    'mouse_down_press',
    'mouse_down_release',
    'mouse_press_and_hold',
    'send_mouse_sequence',
    'press_mouse_precisely',
    'send_multi_button_press',
    'release_multi_button',
    'send_complex_click_sequence',
    'simulate_mouse_gesture',
    'get_mouse_button_state',
    'wait_for_mouse_release',

    # 系统级控制
    'simulate_menu_shortcut',
    'send_system_command',
    'send_raw_input_event',

    # 工具函数
    'build_key_lparam',
    'build_mouse_lparam',

    # 管理功能
    'is_admin'
]