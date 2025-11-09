#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
窗口消息发送器

使用Win32 API的SendMessage向目标窗口发送各种消息
支持键盘、鼠标和其他窗口消息
"""

import time
import ctypes
from typing import Optional, Union, List, Tuple
from ctypes import wintypes

try:
    import win32gui
    import win32con
    import win32api
    import pywintypes
except ImportError as e:
    print(f"错误：缺少必要的库 - {e}")
    print("请运行: pip install pywin32")
    raise

# 加载Windows API
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class WindowMessage:
    """窗口消息发送器类"""

    # 虚拟键码映射
    VIRTUAL_KEYS = {
        # 字母键
        'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46,
        'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C,
        'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52,
        's': 0x53, 't': 0x54, 'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58,
        'y': 0x59, 'z': 0x5A,
        # 数字键
        '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
        '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
        # 功能键
        'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74,
        'f6': 0x75, 'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79,
        'f11': 0x7A, 'f12': 0x7B,
        # 特殊键
        'space': 0x20, 'enter': 0x0D, 'esc': 0x1B, 'tab': 0x09,
        'backspace': 0x08, 'delete': 0x2E, 'insert': 0x2D, 'home': 0x24,
        'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22,
        'left': 0x25, 'up': 0x26, 'right': 0x27, 'down': 0x28,
        # 符号键
        ';': 0xBA, '=': 0xBB, ',': 0xBC, '-': 0xBD, '.': 0xBE, '/': 0xBF,
        '`': 0xC0, '[': 0xDB, '\\': 0xDC, ']': 0xDD, "'": 0xDE,
        # 修饰键
        'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12, 'win': 0x5B
    }

    # 鼠标按键常量
    MOUSE_LEFT_DOWN = 0x0002
    MOUSE_LEFT_UP = 0x0004
    MOUSE_RIGHT_DOWN = 0x0008
    MOUSE_RIGHT_UP = 0x0010
    MOUSE_MIDDLE_DOWN = 0x0020
    MOUSE_MIDDLE_UP = 0x0040

    @staticmethod
    def get_virtual_key(key: str) -> int:
        """获取虚拟键码"""
        key = key.lower()
        if key in WindowMessage.VIRTUAL_KEYS:
            return WindowMessage.VIRTUAL_KEYS[key]
        # 如果是字符，返回ASCII码
        if len(key) == 1:
            return ord(key.upper())
        raise ValueError(f"未知的键: {key}")

    @staticmethod
    def is_valid_window(hwnd: int) -> bool:
        """检查窗口句柄是否有效"""
        try:
            return hwnd != 0 and win32gui.IsWindow(hwnd)
        except Exception:
            return False

    @staticmethod
    def send_message(hwnd: int, msg: int, wparam: int = 0, lparam: int = 0) -> Optional[int]:
        """发送窗口消息"""
        if not WindowMessage.is_valid_window(hwnd):
            raise ValueError(f"无效的窗口句柄: {hwnd}")

        try:
            result = win32gui.SendMessage(hwnd, msg, wparam, lparam)
            return result
        except pywintypes.error as e:
            raise RuntimeError(f"发送消息失败: {e}")

    @staticmethod
    def post_message(hwnd: int, msg: int, wparam: int = 0, lparam: int = 0) -> bool:
        """投递窗口消息（非阻塞）"""
        if not WindowMessage.is_valid_window(hwnd):
            raise ValueError(f"无效的窗口句柄: {hwnd}")

        try:
            return win32gui.PostMessage(hwnd, msg, wparam, lparam)
        except pywintypes.error as e:
            raise RuntimeError(f"投递消息失败: {e}")

    @staticmethod
    def send_key_down(hwnd: int, key: Union[str, int]) -> bool:
        """发送按键按下消息"""
        if isinstance(key, str):
            key = WindowMessage.get_virtual_key(key)

        return WindowMessage.send_message(hwnd, win32con.WM_KEYDOWN, key, 0)

    @staticmethod
    def send_key_up(hwnd: int, key: Union[str, int]) -> bool:
        """发送按键释放消息"""
        if isinstance(key, str):
            key = WindowMessage.get_virtual_key(key)

        # 对于按键释放，需要包含重复计数和扫描码信息
        lparam = 0x00000001  # 重复计数为1，扫描码为0
        return WindowMessage.send_message(hwnd, win32con.WM_KEYUP, key, lparam)

    @staticmethod
    def send_char(hwnd: int, char: str) -> bool:
        """发送字符消息"""
        # 转换字符为Unicode码点
        char_code = ord(char)
        # WM_CHAR消息的lparam包含字符重复信息和键盘状态
        lparam = 0x00000001  # 重复计数为1

        return WindowMessage.send_message(hwnd, win32con.WM_CHAR, char_code, lparam)

    @staticmethod
    def send_mouse_click(hwnd: int, x: int, y: int, button: str = "left") -> bool:
        """发送鼠标点击消息"""
        # 创建lparam，包含x,y坐标信息
        lparam = (y << 16) | (x & 0xFFFF)

        if button.lower() == "left":
            # 左键按下
            WindowMessage.send_message(hwnd, win32con.WM_LBUTTONDOWN, WindowMessage.MOUSE_LEFT_DOWN, lparam)
            # 短暂延迟后释放
            time.sleep(0.01)
            return WindowMessage.send_message(hwnd, win32con.WM_LBUTTONUP, WindowMessage.MOUSE_LEFT_UP, lparam)
        elif button.lower() == "right":
            # 右键按下
            WindowMessage.send_message(hwnd, win32con.WM_RBUTTONDOWN, WindowMessage.MOUSE_RIGHT_DOWN, lparam)
            time.sleep(0.01)
            return WindowMessage.send_message(hwnd, win32con.WM_RBUTTONUP, WindowMessage.MOUSE_RIGHT_UP, lparam)
        elif button.lower() == "middle":
            # 中键按下
            WindowMessage.send_message(hwnd, win32con.WM_MBUTTONDOWN, WindowMessage.MOUSE_MIDDLE_DOWN, lparam)
            time.sleep(0.01)
            return WindowMessage.send_message(hwnd, win32con.WM_MBUTTONUP, WindowMessage.MOUSE_MIDDLE_UP, lparam)
        else:
            raise ValueError(f"未知的鼠标按键: {button}")

    @staticmethod
    def send_mouse_double_click(hwnd: int, x: int, y: int, button: str = "left") -> bool:
        """发送鼠标双击消息"""
        lparam = (y << 16) | (x & 0xFFFF)

        if button.lower() == "left":
            # 双击消息
            return WindowMessage.send_message(hwnd, win32con.WM_LBUTTONDBLCLK, WindowMessage.MOUSE_LEFT_DOWN, lparam)
        elif button.lower() == "right":
            return WindowMessage.send_message(hwnd, win32con.WM_RBUTTONDBLCLK, WindowMessage.MOUSE_RIGHT_DOWN, lparam)
        elif button.lower() == "middle":
            return WindowMessage.send_message(hwnd, win32con.WM_MBUTTONDBLCLK, WindowMessage.MOUSE_MIDDLE_DOWN, lparam)
        else:
            raise ValueError(f"未知的鼠标按键: {button}")

    @staticmethod
    def send_mouse_move(hwnd: int, x: int, y: int) -> bool:
        """发送鼠标移动消息"""
        lparam = (y << 16) | (x & 0xFFFF)
        return WindowMessage.send_message(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)

    @staticmethod
    def send_mouse_wheel(hwnd: int, delta: int, x: int = 0, y: int = 0) -> bool:
        """发送鼠标滚轮消息"""
        # 滚轮消息的wparam包含按钮状态和滚轮增量
        # delta通常为120或-120，表示向上或向下滚动一格
        wparam = (delta << 16) & 0xFFFF
        # lparam包含鼠标位置
        lparam = (y << 16) | (x & 0xFFFF)
        return WindowMessage.send_message(hwnd, win32con.WM_MOUSEWHEEL, wparam, lparam)

    @staticmethod
    def send_focus(hwnd: int) -> bool:
        """发送焦点消息到窗口"""
        # 激活窗口
        try:
            win32gui.SetForegroundWindow(hwnd)
            # 发送激活消息
            WindowMessage.send_message(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
            return True
        except Exception as e:
            raise RuntimeError(f"设置窗口焦点失败: {e}")

    @staticmethod
    def get_window_client_rect(hwnd: int) -> Optional[Tuple[int, int, int, int]]:
        """获取窗口客户区坐标"""
        try:
            return win32gui.GetClientRect(hwnd)
        except Exception as e:
            raise RuntimeError(f"获取窗口客户区坐标失败: {e}")

    @staticmethod
    def screen_to_client(hwnd: int, x: int, y: int) -> Tuple[int, int]:
        """将屏幕坐标转换为客户区坐标"""
        try:
            point = win32gui.ScreenToClient(hwnd, (x, y))
            return point
        except Exception as e:
            raise RuntimeError(f"坐标转换失败: {e}")

    @staticmethod
    def client_to_screen(hwnd: int, x: int, y: int) -> Tuple[int, int]:
        """将客户区坐标转换为屏幕坐标"""
        try:
            point = win32gui.ClientToScreen(hwnd, (x, y))
            return point
        except Exception as e:
            raise RuntimeError(f"坐标转换失败: {e}")

    # ==================== 精细键盘控制API ====================

    @staticmethod
    def key_down_press(hwnd: int, key: Union[str, int]) -> bool:
        """
        精确控制：按键按下（保持按下状态，不自动释放）

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码

        Returns:
            bool: 是否成功
        """
        try:
            if isinstance(key, str):
                key_code = WindowMessage.get_virtual_key(key)
            else:
                key_code = key

            # WM_KEYDOWN消息，按键按下（仅按下，不释放）
            # lparam = 重复计数(1) | 扫描码(0) | 扩展键标志(0) | 保留(0) | 环境键(0) | 过渡状态(0)
            lparam = 0x00000001  # 重复计数为1，扫描码为0
            result = WindowMessage.send_message(hwnd, win32con.WM_KEYDOWN, key_code, lparam)
            return result is not None or result == 0

        except Exception as e:
            raise RuntimeError(f"按键按下失败: {e}")

    @staticmethod
    def key_down_release(hwnd: int, key: Union[str, int]) -> bool:
        """
        精确控制：释放按键（从按下状态释放）

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码

        Returns:
            bool: 是否成功
        """
        try:
            if isinstance(key, str):
                key_code = WindowMessage.get_virtual_key(key)
            else:
                key_code = key

            # WM_KEYUP消息，按键释放
            lparam = 0x00000001  # 重复计数为1，扫描码为0
            result = WindowMessage.send_message(hwnd, win32con.WM_KEYUP, key_code, lparam)
            return result is not None or result == 0

        except Exception as e:
            raise RuntimeError(f"按键释放失败: {e}")

    @staticmethod
    def key_up_press(hwnd: int, key: Union[str, int]) -> bool:
        """
        精确控制：键抬起按下（通常与shift等修饰键相关）

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码

        Returns:
            bool: 是否成功
        """
        try:
            if isinstance(key, str):
                key_code = WindowMessage.get_virtual_key(key)
            else:
                key_code = key

            # 键抬起按下通常用于特殊键或修饰键
            lparam = 0x00000001
            result = WindowMessage.send_message(hwnd, win32con.WM_KEYUP, key_code, lparam)
            return result is not None or result == 0

        except Exception as e:
            raise RuntimeError(f"键抬起按下失败: {e}")

    @staticmethod
    def key_up_release(hwnd: int, key: Union[str, int]) -> bool:
        """
        精确控制：键抬起释放

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码

        Returns:
            bool: 是否成功
        """
        # key_up_press和key_up_release基本相同，都是释放按键
        return WindowMessage.key_up_press(hwnd, key)

    # ==================== 精细鼠标控制API ====================

    @staticmethod
    def mouse_down_press(hwnd: int, x: int, y: int, button: str = "left") -> bool:
        """
        精确控制：鼠标按下（保持按下状态，不自动释放）

        Args:
            hwnd: 窗口句柄
            x: 客户区X坐标
            y: 客户区Y坐标
            button: 鼠标按键 ('left', 'right', 'middle')

        Returns:
            bool: 是否成功
        """
        try:
            lparam = (y << 16) | (x & 0xFFFF)

            if button.lower() == "left":
                return WindowMessage.send_message(hwnd, win32con.WM_LBUTTONDOWN, WindowMessage.MOUSE_LEFT_DOWN, lparam)
            elif button.lower() == "right":
                return WindowMessage.send_message(hwnd, win32con.WM_RBUTTONDOWN, WindowMessage.MOUSE_RIGHT_DOWN, lparam)
            elif button.lower() == "middle":
                return WindowMessage.send_message(hwnd, win32con.WM_MBUTTONDOWN, WindowMessage.MOUSE_MIDDLE_DOWN, lparam)
            else:
                raise ValueError(f"未知的鼠标按键: {button}")

        except Exception as e:
            raise RuntimeError(f"鼠标按下失败: {e}")

    @staticmethod
    def mouse_down_release(hwnd: int, x: int, y: int, button: str = "left") -> bool:
        """
        精确控制：鼠标按下释放（从按下状态释放）

        Args:
            hwnd: 窗口句柄
            x: 客户区X坐标
            y: 客户区Y坐标
            button: 鼠标按键 ('left', 'right', 'middle')

        Returns:
            bool: 是否成功
        """
        try:
            lparam = (y << 16) | (x & 0xFFFF)

            if button.lower() == "left":
                return WindowMessage.send_message(hwnd, win32con.WM_LBUTTONUP, WindowMessage.MOUSE_LEFT_UP, lparam)
            elif button.lower() == "right":
                return WindowMessage.send_message(hwnd, win32con.WM_RBUTTONUP, WindowMessage.MOUSE_RIGHT_UP, lparam)
            elif button.lower() == "middle":
                return WindowMessage.send_message(hwnd, win32con.WM_MBUTTONUP, WindowMessage.MOUSE_MIDDLE_UP, lparam)
            else:
                raise ValueError(f"未知的鼠标按键: {button}")

        except Exception as e:
            raise RuntimeError(f"鼠标按下释放失败: {e}")

    @staticmethod
    def mouse_up_press(hwnd: int, x: int, y: int, button: str = "left") -> bool:
        """
        精确控制：鼠标抬起按下

        Args:
            hwnd: 窗口句柄
            x: 客户区X坐标
            y: 客户区Y坐标
            button: 鼠标按键 ('left', 'right', 'middle')

        Returns:
            bool: 是否成功
        """
        # 鼠标抬起的按下操作，通常与特殊鼠标消息相关
        return WindowMessage.mouse_down_release(hwnd, x, y, button)

    @staticmethod
    def mouse_up_release(hwnd: int, x: int, y: int, button: str = "left") -> bool:
        """
        精确控制：鼠标抬起释放

        Args:
            hwnd: 窗口句柄
            x: 客户区X坐标
          y: 客户区Y坐标
          button: 鼠标按键 ('left', 'right', 'middle')

        Returns:
            bool: 是否成功
        """
        # 鼠标抬起的释放操作
        return WindowMessage.mouse_up_press(hwnd, x, y, button)

    # ==================== 高级精细控制API ====================

    @staticmethod
    def key_press_and_hold(hwnd: int, key: Union[str, int], duration: float) -> bool:
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
            # 按下按键
            if not WindowMessage.key_down_press(hwnd, key):
                return False

            # 保持指定时间
            time.sleep(duration)

            # 释放按键
            return WindowMessage.key_down_release(hwnd, key)

        except Exception as e:
            raise RuntimeError(f"按键保持失败: {e}")

    @staticmethod
    def mouse_press_and_hold(hwnd: int, x: int, y: int, button: str = "left", duration: float = 0.1) -> bool:
        """
        按下并保持鼠标指定时间

        Args:
            hwnd: 窗口句柄
            x: 客户区X坐标
            y: 客户区Y坐标
            button: 鼠标按键
            duration: 保持时间（秒）

        Returns:
            bool: 是否成功
        """
        try:
            # 按下鼠标
            if not WindowMessage.mouse_down_press(hwnd, x, y, button):
                return False

            # 保持指定时间
            time.sleep(duration)

            # 释放鼠标
            return WindowMessage.mouse_down_release(hwnd, x, y, button)

        except Exception as e:
            raise RuntimeError(f"鼠标保持失败: {e}")

    @staticmethod
    def send_key_sequence(hwnd: int, key_sequence: List[Tuple[str, bool]]) -> bool:
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
            for key, is_press in key_sequence:
                if isinstance(key, str):
                    key_code = WindowMessage.get_virtual_key(key)
                else:
                    key_code = key

                lparam = 0x00000001

                if is_press:
                    result = WindowMessage.send_message(hwnd, win32con.WM_KEYDOWN, key_code, lparam)
                else:
                    result = WindowMessage.send_message(hwnd, win32con.WM_KEYUP, key_code, lparam)

                # 微小延迟确保消息处理顺序
                time.sleep(0.001)

            return True

        except Exception as e:
            raise RuntimeError(f"发送按键序列失败: {e}")

    @staticmethod
    def send_mouse_sequence(hwnd: int, mouse_sequence: List[Tuple[str, int, int, bool]]) -> bool:
        """
        发送鼠标序列（用于精确控制鼠标时序）

        Args:
            hwnd: 窗口句柄
            mouse_sequence: 鼠标序列，每个元素为 (action, x, y, is_press) ，
                          action为 'left', 'right', 'middle'，is_press为True表示按下，False表示释放

        Returns:
            bool: 是否成功
        """
        try:
            for action, x, y, is_press in mouse_sequence:
                lparam = (y << 16) | (x & 0xFFFF)

                if action == "left":
                    msg = win32con.WM_LBUTTONDOWN if is_press else win32con.WM_LBUTTONUP
                elif action == "right":
                    msg = win32con.WM_RBUTTONDOWN if is_press else win32con.WM_RBUTTONUP
                elif action == "middle":
                    msg = win32con.WM_MBUTTONDOWN if is_press else win32con.WM_MBUTTONUP
                else:
                    raise ValueError(f"未知的鼠标动作: {action}")

                result = WindowMessage.send_message(hwnd, msg, 0, lparam)

                # 微小延迟确保消息处理顺序
                time.sleep(0.001)

            return True

        except Exception as e:
            raise RuntimeError(f"发送鼠标序列失败: {e}")

    # ==================== 状态管理API ====================

    @staticmethod
    def get_async_key_state(virtual_key: int) -> bool:
        """
        获取虚拟键的当前状态

        Args:
            virtual_key: 虚拟键码

        Returns:
            bool: 键是否被按下
        """
        try:
            # 使用GetAsyncKeyState获取按键状态
            state = user32.GetAsyncKeyState(virtual_key)
            return (state & 0x8000) != 0  # 检查最高位
        except Exception:
            return False

    @staticmethod
    def is_key_pressed(hwnd: int, key: Union[str, int]) -> bool:
        """
        检查指定键是否当前被按下（仅检查该窗口的消息队列）

        Args:
            hwnd: 窗口句柄
            key: 键名或虚拟键码

        Returns:
            bool: 键是否被按下
        """
        try:
            if isinstance(key, str):
                virtual_key = WindowMessage.get_virtual_key(key)
            else:
                virtual_key = key

            # 使用GetAsyncKeyState检查系统级别的按键状态
            return WindowMessage.get_async_key_state(virtual_key)

        except Exception:
            return False

    @staticmethod
    def wait_for_key_release(hwnd: int, key: Union[str, int], timeout: float = 5.0) -> bool:
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
            import time
            start_time = time.time()

            if isinstance(key, str):
                virtual_key = WindowMessage.get_virtual_key(key)
            else:
                virtual_key = key

            while time.time() - start_time < timeout:
                if not WindowMessage.get_async_key_state(virtual_key):
                    return True
                time.sleep(0.01)

            return False  # 超时

        except Exception as e:
            raise RuntimeError(f"等待按键释放失败: {e}")

    # ==================== 特殊功能API ====================

    @staticmethod
    def simulate_menu_shortcut(hwnd: int, key: str) -> bool:
        """
        模拟菜单快捷键（如Alt+F, Alt+E等）

        Args:
            hwnd: 窗口句柄
            key: 快捷键字母

        Returns:
            bool: 是否成功
        """
        try:
            # 发送Alt键按下
            WindowMessage.key_down_press(hwnd, 'alt')
            time.sleep(0.01)

            # 发送快捷键字母
            WindowMessage.key_down_press(hwnd, key)
            WindowMessage.key_down_release(hwnd, key)
            time.sleep(0.01)

            # 释放Alt键
            WindowMessage.key_down_release(hwnd, 'alt')

            return True

        except Exception as e:
            raise RuntimeError(f"模拟菜单快捷键失败: {e}")

    @staticmethod
    def send_system_command(hwnd: int, command: str) -> bool:
        """
        发送系统命令（如最大化、最小化、关闭等）

        Args:
            hwnd: 窗口句柄
            command: 命令名称 ('minimize', 'maximize', 'restore', 'close', 'activate')

        Returns:
            bool: 是否成功
        """
        try:
            if command == 'minimize':
                return WindowMessage.send_message(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_MINIMIZE, 0)
            elif command == 'maximize':
                return WindowMessage.send_message(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_MAXIMIZE, 0)
            elif command == 'restore':
                return WindowMessage.send_message(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
            elif command == 'close':
                return WindowMessage.send_message(hwnd, win32con.WM_CLOSE, 0, 0)
            elif command == 'activate':
                return WindowMessage.send_focus(hwnd)
            else:
                raise ValueError(f"未知的系统命令: {command}")

        except Exception as e:
            raise RuntimeError(f"发送系统命令失败: {e}")

    @staticmethod
    def send_raw_input_event(hwnd: int, event_type: str, x: int = 0, y: int = 0, data: int = 0) -> bool:
        """
        发送原始输入事件

        Args:
            hwnd: 窗口句柄
            event_type: 事件类型 ('mouse', 'keyboard')
            x: X坐标
            y: Y坐标
            data: 附加数据

        Returns:
            bool: 是否成功
        """
        try:
            if event_type == 'mouse':
                # 原始鼠标事件
                lparam = (y << 16) | (x & 0xFFFF)
                return WindowMessage.send_message(hwnd, win32con.WM_INPUT, data, lparam)
            elif event_type == 'keyboard':
                # 原始键盘事件
                lparam = (data << 16) | (x & 0xFFFF)
                return WindowMessage.send_message(hwnd, win32con.WM_INPUT, data, lparam)
            else:
                raise ValueError(f"未知的输入事件类型: {event_type}")

        except Exception as e:
            raise RuntimeError(f"发送原始输入事件失败: {e}")

    # ==================== 辅助工具API ====================

    @staticmethod
    def build_lparam_for_key(scan_code: int = 0, repeat_count: int = 1, extended_key: bool = False) -> int:
        """
        构建按键消息的lparam值

        Args:
            scan_code: 扫描码
            repeat_count: 重复计数
            extended_key: 是否扩展键

        Returns:
            int: lparam值
        """
        # lparam格式: 重复计数(16位) | 扫描码(16位) | 扩展键标志 | 保留位 | 环境键 | 过渡状态
        lparam = repeat_count
        lparam |= (scan_code & 0xFF) << 16
        if extended_key:
            lparam |= 0x01000000
        return lparam

    @staticmethod
    def build_lparam_for_mouse(x: int, y: int) -> int:
        """
        构建鼠标消息的lparam值

        Args:
            x: X坐标
            y: Y坐标

        Returns:
            int: lparam值
        """
        return (y << 16) | (x & 0xFFFF)