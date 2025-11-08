#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输入管理器模块

提供模拟键盘和鼠标输入的API，支持向非活动窗口发送输入消息
使用Win32 API的SendMessage实现窗口自动化
"""

from .input_manager import InputManager
from .keyboard import KeyboardInput
from .mouse import MouseInput
from .window_message import WindowMessage

# 创建全局输入管理器实例
_input_manager = None

def get_input_manager() -> InputManager:
    """获取全局输入管理器实例"""
    global _input_manager
    if _input_manager is None:
        _input_manager = InputManager()
    return _input_manager

def send_key(hwnd: int, key: str, repeat: int = 1, delay: float = 0.01):
    """发送键盘消息到指定窗口"""
    manager = get_input_manager()
    manager.keyboard.send_key(hwnd, key, repeat, delay)

def send_keys(hwnd: int, text: str, delay: float = 0.01):
    """发送字符串到指定窗口"""
    manager = get_input_manager()
    manager.keyboard.send_keys(hwnd, text, delay)

def send_mouse_click(hwnd: int, x: int, y: int, button: str = "left", double: bool = False):
    """发送鼠标点击到指定窗口坐标"""
    manager = get_input_manager()
    manager.mouse.send_click(hwnd, x, y, button, double)

def send_mouse_move(hwnd: int, x: int, y: int):
    """发送鼠标移动到指定窗口坐标"""
    manager = get_input_manager()
    manager.mouse.send_move(hwnd, x, y)

def send_mouse_wheel(hwnd: int, delta: int, x: int = 0, y: int = 0):
    """发送鼠标滚轮消息"""
    manager = get_input_manager()
    manager.mouse.send_wheel(hwnd, delta, x, y)

# ===== 精细控制便捷函数 =====

def key_down_press(hwnd: int, key):
    """精确控制：按键按下（保持按下状态，不自动释放）"""
    manager = get_input_manager()
    return manager.keyboard.key_down_press(hwnd, key)

def key_down_release(hwnd: int, key):
    """精确控制：释放按键（从按下状态释放）"""
    manager = get_input_manager()
    return manager.keyboard.key_down_release(hwnd, key)

def key_press_and_hold(hwnd: int, key, duration: float):
    """按下并保持按键指定时间"""
    manager = get_input_manager()
    return manager.keyboard.key_press_and_hold(hwnd, key, duration)

def send_key_sequence(hwnd: int, key_sequence):
    """发送按键序列（用于精确控制按键时序）"""
    manager = get_input_manager()
    return manager.keyboard.send_key_sequence(hwnd, key_sequence)

def is_key_pressed(hwnd: int, key):
    """检查指定键是否当前被按下"""
    manager = get_input_manager()
    return manager.keyboard.is_key_pressed(hwnd, key)

def wait_for_key_release(hwnd: int, key, timeout: float = 5.0):
    """等待按键释放"""
    manager = get_input_manager()
    return manager.keyboard.wait_for_key_release(hwnd, key, timeout)

def press_modifiers_precisely(hwnd: int, modifiers):
    """精确按下多个修饰键（不释放）"""
    manager = get_input_manager()
    return manager.keyboard.press_modifiers_precisely(hwnd, modifiers)

def release_modifiers_precisely(hwnd: int, modifiers):
    """精确释放多个修饰键"""
    manager = get_input_manager()
    return manager.keyboard.release_modifiers_precisely(hwnd, modifiers)

def send_chord_key(hwnd: int, modifiers, main_key):
    """发送弦键（修饰键+主键的组合）"""
    manager = get_input_manager()
    return manager.keyboard.send_chord_key(hwnd, modifiers, main_key)

def toggle_key(hwnd: int, key):
    """切换按键状态（如果当前按下则释放，如果当前释放则按下）"""
    manager = get_input_manager()
    return manager.keyboard.toggle_key(hwnd, key)

def send_pressurized_key_sequence(hwnd: int, sequence):
    """发送带压力的按键序列（每个键可以指定按下时间和状态）"""
    manager = get_input_manager()
    return manager.keyboard.send_pressurized_key_sequence(hwnd, sequence)

def mouse_down_press(hwnd: int, x: int, y: int, button: str = "left"):
    """精确控制：鼠标按下（保持按下状态，不自动释放）"""
    manager = get_input_manager()
    return manager.mouse.mouse_down_press(hwnd, x, y, button)

def mouse_down_release(hwnd: int, x: int, y: int, button: str = "left"):
    """精确控制：释放鼠标（从按下状态释放）"""
    manager = get_input_manager()
    return manager.mouse.mouse_down_release(hwnd, x, y, button)

def mouse_press_and_hold(hwnd: int, x: int, y: int, button: str = "left", duration: float = 0.1):
    """按下并保持鼠标指定时间"""
    manager = get_input_manager()
    return manager.mouse.mouse_press_and_hold(hwnd, x, y, button, duration)

def send_mouse_sequence(hwnd: int, mouse_sequence):
    """发送鼠标序列（用于精确控制鼠标时序）"""
    manager = get_input_manager()
    return manager.mouse.send_mouse_sequence(hwnd, mouse_sequence)

def press_mouse_precisely(hwnd: int, x: int, y: int, button: str = "left", duration: float = 0.01):
    """精确按下并快速释放鼠标（比send_click更精确）"""
    manager = get_input_manager()
    return manager.mouse.press_mouse_precisely(hwnd, x, y, button, duration)

def send_multi_button_press(hwnd: int, x: int, y: int, buttons):
    """同时按下多个鼠标按钮"""
    manager = get_input_manager()
    return manager.mouse.send_multi_button_press(hwnd, x, y, buttons)

def release_multi_button(hwnd: int, x: int, y: int, buttons):
    """释放多个鼠标按钮"""
    manager = get_input_manager()
    return manager.mouse.release_multi_button(hwnd, x, y, buttons)

def send_complex_click_sequence(hwnd: int, sequence):
    """发送复杂点击序列（每个点击可以指定按钮、状态和时长）"""
    manager = get_input_manager()
    return manager.mouse.send_complex_click_sequence(hwnd, sequence)

def simulate_mouse_gesture(hwnd: int, gesture):
    """模拟鼠标手势（每个点可以指定按键和按下时间）"""
    manager = get_input_manager()
    return manager.mouse.simulate_mouse_gesture(hwnd, gesture)

def get_mouse_button_state(button: str):
    """获取鼠标按钮状态"""
    manager = get_input_manager()
    return manager.mouse.get_mouse_button_state(button)

def wait_for_mouse_release(hwnd: int, button: str, timeout: float = 5.0):
    """等待鼠标按钮释放"""
    manager = get_input_manager()
    return manager.mouse.wait_for_mouse_release(hwnd, button, timeout)

# ===== 系统级控制便捷函数 =====

def simulate_menu_shortcut(hwnd: int, key: str):
    """模拟菜单快捷键（如Alt+F, Alt+E等）"""
    manager = get_input_manager()
    return manager.keyboard.simulate_menu_shortcut(hwnd, key)

def send_system_command(hwnd: int, command: str):
    """发送系统命令（如最大化、最小化、关闭等）"""
    return WindowMessage.send_system_command(hwnd, command)

def send_raw_input_event(hwnd: int, event_type: str, x: int = 0, y: int = 0, data: int = 0):
    """发送原始输入事件"""
    return WindowMessage.send_raw_input_event(hwnd, event_type, x, y, data)

# ===== 工具函数 =====

def build_key_lparam(scan_code: int = 0, repeat_count: int = 1, extended_key: bool = False):
    """构建按键消息的lparam值"""
    return WindowMessage.build_lparam_for_key(scan_code, repeat_count, extended_key)

def build_mouse_lparam(x: int, y: int):
    """构建鼠标消息的lparam值"""
    return WindowMessage.build_lparam_for_mouse(x, y)

__all__ = [
    'InputManager',
    'KeyboardInput',
    'MouseInput',
    'WindowMessage',
    'get_input_manager',

    # 基础输入函数
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
    'build_mouse_lparam'
]