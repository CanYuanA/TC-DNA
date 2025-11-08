#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
键盘输入管理器

提供高级键盘输入功能，支持向目标窗口发送各种键盘消息
使用Win32 API的SendMessage实现对非活动窗口的输入控制
"""

import time
import re
from typing import Union, Optional, List, Dict, Any, Tuple
import threading

try:
    import win32con
    import pywintypes
except ImportError as e:
    print(f"错误：缺少必要的库 - {e}")
    print("请运行: pip install pywin32")
    raise

from .window_message import WindowMessage


class KeyboardInput:
    """键盘输入管理器类"""

    def __init__(self):
        """初始化键盘输入管理器"""
        pass  # 移除锁机制避免死锁

    def _send_key_combination(self, hwnd: int, key: str, press_duration: float = 0.01) -> bool:
        """发送按键组合（如Ctrl+C）"""
        try:
            # 解析按键组合
            parts = key.split('+')
            if len(parts) > 1:
                # 获取修饰键
                modifiers = []
                main_key = parts[-1]

                for part in parts[:-1]:
                    part_lower = part.lower().strip()
                    if part_lower in ['ctrl', 'control']:
                        modifiers.append('ctrl')
                    elif part_lower == 'shift':
                        modifiers.append('shift')
                    elif part_lower == 'alt':
                        modifiers.append('alt')
                    elif part_lower in ['win', 'windows']:
                        modifiers.append('win')

                # 按下修饰键
                for modifier in modifiers:
                    WindowMessage.send_key_down(hwnd, modifier)
                    time.sleep(0.01)

                # 按下主键
                WindowMessage.send_key_down(hwnd, main_key)
                time.sleep(press_duration)
                WindowMessage.send_key_up(hwnd, main_key)

                # 释放修饰键（反向顺序）
                for modifier in reversed(modifiers):
                    WindowMessage.send_key_up(hwnd, modifier)

                return True
            else:
                # 单个键
                return self.send_key(hwnd, key, 1, press_duration)

        except Exception as e:
            raise RuntimeError(f"发送按键组合失败: {e}")

    def send_key(self, hwnd: int, key: str, repeat: int = 1, delay: float = 0.01) -> bool:
        """
        发送单个按键到目标窗口

        Args:
            hwnd: 窗口句柄
            key: 键名（如 'a', 'enter', 'f1' 等）
            repeat: 重复次数
            delay: 每次按键之间的延迟（秒）

        Returns:
            bool: 是否成功
        """
        try:
            for i in range(repeat):
                if key.lower() in ['ctrl+c', 'ctrl+v', 'ctrl+x', 'ctrl+z', 'ctrl+a', 'ctrl+s', 'ctrl+o', 'ctrl+n']:
                    return self._send_key_combination(hwnd, key, delay)
                elif '+' in key:
                    return self._send_key_combination(hwnd, key, delay)
                else:
                    # 单个键
                    WindowMessage.send_key_down(hwnd, key)
                    time.sleep(delay)
                    WindowMessage.send_key_up(hwnd, key)

                if i < repeat - 1:  # 最后一次按键后不延迟
                    time.sleep(delay)

            return True

        except Exception as e:
            raise RuntimeError(f"发送按键失败: {e}")

    def send_keys(self, hwnd: int, text: str, delay: float = 0.01) -> bool:
        """
        发送字符串到目标窗口

        Args:
            hwnd: 窗口句柄
            text: 要发送的文本
            delay: 每个字符之间的延迟（秒）

        Returns:
            bool: 是否成功
        """
        try:
            for char in text:
                if char == '\n':
                    # 发送回车键
                    self.send_key(hwnd, 'enter', 1, delay)
                elif char == '\t':
                    # 发送Tab键
                    self.send_key(hwnd, 'tab', 1, delay)
                elif char == '\r':
                    # 跳过回车符（因为通常与\n一起出现）
                    continue
                else:
                    # 发送普通字符
                    WindowMessage.send_char(hwnd, char)
                    time.sleep(delay)

            return True

        except Exception as e:
            raise RuntimeError(f"发送字符串失败: {e}")

    def send_enhanced_key(self, hwnd: int, key_name: str, shift: bool = False, ctrl: bool = False, alt: bool = False) -> bool:
        """
        发送增强型按键（带修饰键）

        Args:
            hwnd: 窗口句柄
            key_name: 键名
            shift: 是否按住Shift
            ctrl: 是否按住Ctrl
            alt: 是否按住Alt

        Returns:
            bool: 是否成功
        """
        
        try:
            # 按下修饰键
            if shift:
                WindowMessage.send_key_down(hwnd, 'shift')
            if ctrl:
                WindowMessage.send_key_down(hwnd, 'ctrl')
            if alt:
                WindowMessage.send_key_down(hwnd, 'alt')

            time.sleep(0.01)

            # 按下主键
            WindowMessage.send_key_down(hwnd, key_name)
            time.sleep(0.01)
            WindowMessage.send_key_up(hwnd, key_name)

            time.sleep(0.01)

            # 释放修饰键
            if alt:
                WindowMessage.send_key_up(hwnd, 'alt')
            if ctrl:
                WindowMessage.send_key_up(hwnd, 'ctrl')
            if shift:
                WindowMessage.send_key_up(hwnd, 'shift')

            return True

        except Exception as e:
            raise RuntimeError(f"发送增强型按键失败: {e}")

    def send_press_and_hold(self, hwnd: int, key: str, duration: float) -> bool:
        """
        按住按键指定时间

        Args:
            hwnd: 窗口句柄
            key: 键名
            duration: 按住时间（秒）

        Returns:
            bool: 是否成功
        """
        
        try:
            WindowMessage.send_key_down(hwnd, key)
            time.sleep(duration)
            WindowMessage.send_key_up(hwnd, key)
            return True

        except Exception as e:
            raise RuntimeError(f"按住按键失败: {e}")

    def send_hotkey_sequence(self, hwnd: int, keys: List[str], delays: Optional[List[float]] = None) -> bool:
        """
        发送热键序列

        Args:
            hwnd: 窗口句柄
            keys: 键序列
            delays: 每个键之间的延迟（秒），如果为None则使用默认延迟

        Returns:
            bool: 是否成功
        """
        
        try:
            if delays is None:
                delays = [0.05] * len(keys)

            for key, delay in zip(keys, delays):
                if '+' in key:
                    self._send_key_combination(hwnd, key, 0.01)
                else:
                    self.send_key(hwnd, key, 1, 0.01)

                time.sleep(delay)

            return True

        except Exception as e:
            raise RuntimeError(f"发送热键序列失败: {e}")

    def type_text_enhanced(self, hwnd: int, text: str, char_delay: float = 0.01, line_delay: float = 0.1) -> bool:
        """
        增强型文本输入

        Args:
            hwnd: 窗口句柄
            text: 要输入的文本
            char_delay: 字符间延迟
            line_delay: 换行时额外延迟

        Returns:
            bool: 是否成功
        """
        
        try:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if line:  # 非空行
                    self.send_keys(hwnd, line, char_delay)

                if i < len(lines) - 1:  # 不是最后一行
                    self.send_key(hwnd, 'enter', 1, 0.01)
                    time.sleep(line_delay)

            return True

        except Exception as e:
            raise RuntimeError(f"增强型文本输入失败: {e}")

    def clear_input_field(self, hwnd: int, select_all: bool = True) -> bool:
        """
        清空输入框

        Args:
            hwnd: 窗口句柄
            select_all: 是否先全选

        Returns:
            bool: 是否成功
        """
        
        try:
            if select_all:
                # Ctrl+A 全选
                self.send_key(hwnd, 'ctrl+a', 1, 0.01)
                time.sleep(0.05)

            # Delete 删除
            self.send_key(hwnd, 'delete', 1, 0.01)

            return True

        except Exception as e:
            raise RuntimeError(f"清空输入框失败: {e}")

    def get_pressed_keys(self) -> List[str]:
        """获取当前按下的键（用于调试）"""
        # 注意：这里返回空列表，实际应用中需要通过系统API获取
        return []

    def validate_key(self, key: str) -> bool:
        """
        验证键名是否有效

        Args:
            key: 键名

        Returns:
            bool: 是否有效
        """
        try:
            WindowMessage.get_virtual_key(key)
            return True
        except ValueError:
            return False

    def get_key_mapping(self) -> Dict[str, int]:
        """
        获取键名到虚拟键码的映射

        Returns:
            dict: 键名映射字典
        """
        return WindowMessage.VIRTUAL_KEYS.copy()

    def convert_text_to_keys(self, text: str) -> List[str]:
        """
        将文本转换为键序列（用于复杂文本处理）

        Args:
            text: 原始文本

        Returns:
            list: 键序列
        """
        key_sequence = []
        for char in text:
            if char == '\n':
                key_sequence.append('enter')
            elif char == '\t':
                key_sequence.append('tab')
            elif char == ' ':
                key_sequence.append('space')
            else:
                key_sequence.append(char)

        return key_sequence

    # ==================== 精细控制API ====================

    def key_down_press(self, hwnd: int, key: Union[str, int]) -> bool:
        """
        精确控制：按键按下（保持按下状态，不自动释放）

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码

        Returns:
            bool: 是否成功
        """
        
        try:
            return WindowMessage.key_down_press(hwnd, key)
        except Exception as e:
            raise RuntimeError(f"按键按下失败: {e}")

    def key_down_release(self, hwnd: int, key: Union[str, int]) -> bool:
        """
        精确控制：释放按键（从按下状态释放）

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码

        Returns:
            bool: 是否成功
        """
        
        try:
            return WindowMessage.key_down_release(hwnd, key)
        except Exception as e:
            raise RuntimeError(f"按键释放失败: {e}")

    def key_up_press(self, hwnd: int, key: Union[str, int]) -> bool:
        """
        精确控制：键抬起按下

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码

        Returns:
            bool: 是否成功
        """
        
        try:
            return WindowMessage.key_up_press(hwnd, key)
        except Exception as e:
            raise RuntimeError(f"键抬起按下失败: {e}")

    def key_up_release(self, hwnd: int, key: Union[str, int]) -> bool:
        """
        精确控制：键抬起释放

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码

        Returns:
            bool: 是否成功
        """
        
        try:
            return WindowMessage.key_up_release(hwnd, key)
        except Exception as e:
            raise RuntimeError(f"键抬起释放失败: {e}")

    def key_press_and_hold(self, hwnd: int, key: Union[str, int], duration: float) -> bool:
        """
        按下并保持按键指定时间

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码
            duration: 保持时间（秒）

        Returns:
            bool: 是否成功
        """
        
        try:
            return WindowMessage.key_press_and_hold(hwnd, key, duration)
        except Exception as e:
            raise RuntimeError(f"按键保持失败: {e}")

    def send_key_sequence(self, hwnd: int, key_sequence: List[Tuple[str, bool]]) -> bool:
        """
        发送按键序列（用于精确控制按键时序）

        Args:
            hwnd: 窗口句柄
            key_sequence: 按键序列，每个元素为 (key, is_press) ，
                        is_press=True表示按下，False表示释放

        Returns:
            bool: 是否成功
        """
        
        try:
            return WindowMessage.send_key_sequence(hwnd, key_sequence)
        except Exception as e:
            raise RuntimeError(f"发送按键序列失败: {e}")

    def is_key_pressed(self, hwnd: int, key: Union[str, int]) -> bool:
        """
        检查指定键是否当前被按下

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码

        Returns:
            bool: 键是否被按下
        """
        
        try:
            return WindowMessage.is_key_pressed(hwnd, key)
        except Exception as e:
            raise RuntimeError(f"检查按键状态失败: {e}")

    def wait_for_key_release(self, hwnd: int, key: Union[str, int], timeout: float = 5.0) -> bool:
        """
        等待按键释放

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码
            timeout: 超时时间（秒）

        Returns:
            bool: 是否在超时前释放
        """
        
        try:
            return WindowMessage.wait_for_key_release(hwnd, key, timeout)
        except Exception as e:
            raise RuntimeError(f"等待按键释放失败: {e}")

    def simulate_menu_shortcut(self, hwnd: int, key: str) -> bool:
        """
        模拟菜单快捷键（如Alt+F, Alt+E等）

        Args:
            hwnd: 窗口句柄
            key: 快捷键字母

        Returns:
            bool: 是否成功
        """
        
        try:
            return WindowMessage.simulate_menu_shortcut(hwnd, key)
        except Exception as e:
            raise RuntimeError(f"模拟菜单快捷键失败: {e}")

    def build_key_lparam(self, scan_code: int = 0, repeat_count: int = 1, extended_key: bool = False) -> int:
        """
        构建按键消息的lparam值

        Args:
            scan_code: 扫描码
            repeat_count: 重复计数
            extended_key: 是否扩展键

        Returns:
            int: lparam值
        """
        return WindowMessage.build_lparam_for_key(scan_code, repeat_count, extended_key)

    # ==================== 组合键精细控制 ====================

    def press_modifiers_precisely(self, hwnd: int, modifiers: List[str]) -> bool:
        """
        精确按下多个修饰键（不释放）

        Args:
            hwnd: 窗口句柄
            modifiers: 修饰键列表 ['ctrl', 'shift', 'alt', 'win']

        Returns:
            bool: 是否成功
        """
        
        try:
            for modifier in modifiers:
                if not WindowMessage.key_down_press(hwnd, modifier):
                    return False
                time.sleep(0.01)
            return True
        except Exception as e:
            raise RuntimeError(f"按下修饰键失败: {e}")

    def release_modifiers_precisely(self, hwnd: int, modifiers: List[str]) -> bool:
        """
        精确释放多个修饰键

        Args:
            hwnd: 窗口句柄
            modifiers: 修饰键列表 ['ctrl', 'shift', 'alt', 'win']

        Returns:
            bool: 是否成功
        """
        
        try:
            # 按相反顺序释放
            for modifier in reversed(modifiers):
                if not WindowMessage.key_down_release(hwnd, modifier):
                    return False
                time.sleep(0.01)
            return True
        except Exception as e:
            raise RuntimeError(f"释放修饰键失败: {e}")

    def send_chord_key(self, hwnd: int, modifiers: List[str], main_key: str) -> bool:
        """
        发送弦键（修饰键+主键的组合）

        Args:
            hwnd: 窗口句柄
            modifiers: 修饰键列表
            main_key: 主键名

        Returns:
            bool: 是否成功
        """
        
        try:
            # 按下修饰键
            if not self.press_modifiers_precisely(hwnd, modifiers):
                return False

            time.sleep(0.01)

            # 按下并释放主键
            if not WindowMessage.key_down_press(hwnd, main_key):
                self.release_modifiers_precisely(hwnd, modifiers)
                return False

            time.sleep(0.01)

            if not WindowMessage.key_down_release(hwnd, main_key):
                self.release_modifiers_precisely(hwnd, modifiers)
                return False

            time.sleep(0.01)

            # 释放修饰键
            return self.release_modifiers_precisely(hwnd, modifiers)

        except Exception as e:
            raise RuntimeError(f"发送弦键失败: {e}")

    def press_key_precisely(self, hwnd: int, key: Union[str, int], duration: float = 0.01) -> bool:
        """
        精确按下并快速释放键（比send_key更精确）

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码
            duration: 按下时长（秒）

        Returns:
            bool: 是否成功
        """
        
        try:
            if not WindowMessage.key_down_press(hwnd, key):
                return False

            time.sleep(duration)

            return WindowMessage.key_down_release(hwnd, key)

        except Exception as e:
            raise RuntimeError(f"精确按键失败: {e}")

    def toggle_key(self, hwnd: int, key: Union[str, int]) -> bool:
        """
        切换按键状态（如果当前按下则释放，如果当前释放则按下）

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码

        Returns:
            bool: 是否成功
        """
        
        try:
            is_pressed = self.is_key_pressed(hwnd, key)

            if is_pressed:
                # 如果当前按下，则释放
                return WindowMessage.key_down_release(hwnd, key)
            else:
                # 如果当前释放，则按下
                return WindowMessage.key_down_press(hwnd, key)

        except Exception as e:
            raise RuntimeError(f"切换按键失败: {e}")

    def send_pressurized_key_sequence(self, hwnd: int, sequence: List[Tuple[Union[str, int], bool, Optional[float]]]) -> bool:
        """
        发送带压力的按键序列（每个键可以指定按下时间和状态）

        Args:
            hwnd: 窗口句柄
            sequence: 序列列表，每个元素为 (key, is_press, duration) ，
                     is_press为True表示按下，False表示释放，duration为按下时长（秒）

        Returns:
            bool: 是否成功
        """
        
        try:
            for key, is_press, duration in sequence:
                if is_press:
                    # 按下
                    if duration is None or duration <= 0:
                        # 立即按下并保持
                        if not WindowMessage.key_down_press(hwnd, key):
                            return False
                    else:
                        # 按下指定时间后自动释放
                        if not WindowMessage.key_press_and_hold(hwnd, key, duration):
                            return False
                else:
                    # 释放
                    if not WindowMessage.key_down_release(hwnd, key):
                        return False

                time.sleep(0.001)  # 微小延迟

            return True

        except Exception as e:
            raise RuntimeError(f"发送带压力的按键序列失败: {e}")