#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鼠标输入管理器

提供高级鼠标输入功能，支持向目标窗口发送各种鼠标消息
使用Win32 API的SendMessage实现对非活动窗口的鼠标控制
"""

import time
import ctypes
from typing import Union, Optional, List, Tuple
import threading

try:
    import win32con
    import win32gui
    import pywintypes
except ImportError as e:
    print(f"错误：缺少必要的库 - {e}")
    print("请运行: pip install pywin32")
    raise

# 加载Windows API
user32 = ctypes.windll.user32

from .window_message import WindowMessage


class MouseInput:
    """鼠标输入管理器类"""

    def __init__(self):
        """初始化鼠标输入管理器"""
        pass  # 移除锁机制避免死锁

    def send_click(self, hwnd: int, x: int, y: int, button: str = "left", double: bool = False) -> bool:
        """
        发送鼠标点击到目标窗口的客户区坐标

        Args:
            hwnd: 窗口句柄
            x: 客户区X坐标
            y: 客户区Y坐标
            button: 鼠标按键 ('left', 'right', 'middle')
            double: 是否双击

        Returns:
            bool: 是否成功
        """
        
        try:
            if double:
                return WindowMessage.send_mouse_double_click(hwnd, x, y, button)
            else:
                return WindowMessage.send_mouse_click(hwnd, x, y, button)

        except Exception as e:
            raise RuntimeError(f"发送鼠标点击失败: {e}")

    def send_move(self, hwnd: int, x: int, y: int) -> bool:
        """
        发送鼠标移动到目标窗口的客户区坐标

        Args:
            hwnd: 窗口句柄
            x: 客户区X坐标
            y: 客户区Y坐标

        Returns:
            bool: 是否成功
        """
        
        try:
            return WindowMessage.send_mouse_move(hwnd, x, y)

        except Exception as e:
            raise RuntimeError(f"发送鼠标移动失败: {e}")

    def send_wheel(self, hwnd: int, delta: int, x: int = 0, y: int = 0) -> bool:
        """
        发送鼠标滚轮消息

        Args:
            hwnd: 窗口句柄
            delta: 滚轮增量（正数向上，负数向下，通常为±120的倍数）
            x: 客户区X坐标
            y: 客户区Y坐标

        Returns:
            bool: 是否成功
        """
        
        try:
            return WindowMessage.send_mouse_wheel(hwnd, delta, x, y)

        except Exception as e:
            raise RuntimeError(f"发送鼠标滚轮失败: {e}")

    def send_drag(self, hwnd: int, start_x: int, start_y: int, end_x: int, end_y: int, button: str = "left") -> bool:
        """
        发送拖拽操作

        Args:
            hwnd: 窗口句柄
            start_x: 起始X坐标（客户区）
            start_y: 起始Y坐标（客户区）
            end_x: 结束X坐标（客户区）
            end_y: 结束Y坐标（客户区）
            button: 鼠标按键

        Returns:
            bool: 是否成功
        """
        
        try:
            # 移动到起始位置
            self.send_move(hwnd, start_x, start_y)
            time.sleep(0.01)

            # 按下鼠标
            if button.lower() == "left":
                WindowMessage.send_message(hwnd, win32con.WM_LBUTTONDOWN, WindowMessage.MOUSE_LEFT_DOWN,
                                            (start_y << 16) | (start_x & 0xFFFF))
            elif button.lower() == "right":
                WindowMessage.send_message(hwnd, win32con.WM_RBUTTONDOWN, WindowMessage.MOUSE_RIGHT_DOWN,
                                            (start_y << 16) | (start_x & 0xFFFF))
            else:
                raise ValueError(f"不支持的鼠标按键: {button}")

            time.sleep(0.01)

            # 移动到结束位置（分步移动以模拟真实拖拽）
            steps = max(1, int(abs(end_x - start_x) / 10))
            for i in range(steps + 1):
                current_x = start_x + (end_x - start_x) * i // steps
                current_y = start_y + (end_y - start_y) * i // steps
                self.send_move(hwnd, current_x, current_y)
                time.sleep(0.001)

            time.sleep(0.01)

            # 释放鼠标
            if button.lower() == "left":
                WindowMessage.send_message(hwnd, win32con.WM_LBUTTONUP, WindowMessage.MOUSE_LEFT_UP,
                                            (end_y << 16) | (end_x & 0xFFFF))
            elif button.lower() == "right":
                WindowMessage.send_message(hwnd, win32con.WM_RBUTTONUP, WindowMessage.MOUSE_RIGHT_UP,
                                            (end_y << 16) | (end_x & 0xFFFF))

            return True

        except Exception as e:
            raise RuntimeError(f"发送拖拽操作失败: {e}")

    def send_click_sequence(self, hwnd: int, positions: List[Tuple[int, int]], button: str = "left", delays: Optional[List[float]] = None) -> bool:
        """
        发送点击序列

        Args:
            hwnd: 窗口句柄
            positions: 坐标列表 [(x1, y1), (x2, y2), ...]
            button: 鼠标按键
            delays: 每个点击之间的延迟

        Returns:
            bool: 是否成功
        """
        
        try:
            if delays is None:
                delays = [0.1] * len(positions)

            for i, ((x, y), delay) in enumerate(zip(positions, delays)):
                # 移动到位置
                self.send_move(hwnd, x, y)
                time.sleep(0.01)

                # 点击
                self.send_click(hwnd, x, y, button, False)

                if i < len(positions) - 1:
                    time.sleep(delay)

            return True

        except Exception as e:
            raise RuntimeError(f"发送点击序列失败: {e}")

    def send_scroll(self, hwnd: int, direction: str, lines: int = 3, x: int = 0, y: int = 0) -> bool:
        """
        发送滚轮滚动消息

        Args:
            hwnd: 窗口句柄
            direction: 滚动方向 ('up', 'down', 'left', 'right')
            lines: 滚动行数
            x: 客户区X坐标
            y: 客户区Y坐标

        Returns:
            bool: 是否成功
        """
        
        try:
            if direction.lower() == 'up':
                delta = 120 * lines  # 向上滚动
            elif direction.lower() == 'down':
                delta = -120 * lines  # 向下滚动
            elif direction.lower() == 'left':
                # 水平滚动需要特殊处理，这里简化为垂直滚动的相反方向
                delta = 120 * lines
            elif direction.lower() == 'right':
                delta = -120 * lines
            else:
                raise ValueError(f"未知的滚动方向: {direction}")

            return self.send_wheel(hwnd, delta, x, y)

        except Exception as e:
            raise RuntimeError(f"发送滚轮滚动失败: {e}")

    def get_screen_position(self, hwnd: int, client_x: int, client_y: int) -> Tuple[int, int]:
        """
        将客户区坐标转换为屏幕坐标

        Args:
            hwnd: 窗口句柄
            client_x: 客户区X坐标
            client_y: 客户区Y坐标

        Returns:
            tuple: 屏幕坐标 (x, y)
        """
        try:
            return WindowMessage.client_to_screen(hwnd, client_x, client_y)
        except Exception as e:
            raise RuntimeError(f"坐标转换失败: {e}")

    def get_client_position(self, hwnd: int, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """
        将屏幕坐标转换为客户区坐标

        Args:
            hwnd: 窗口句柄
            screen_x: 屏幕X坐标
            screen_y: 屏幕Y坐标

        Returns:
            tuple: 客户区坐标 (x, y)
        """
        try:
            return WindowMessage.screen_to_client(hwnd, screen_x, screen_y)
        except Exception as e:
            raise RuntimeError(f"坐标转换失败: {e}")

    def validate_position(self, hwnd: int, x: int, y: int) -> bool:
        """
        验证坐标是否在窗口客户区内

        Args:
            hwnd: 窗口句柄
            x: X坐标
            y: Y坐标

        Returns:
            bool: 是否有效
        """
        try:
            rect = WindowMessage.get_window_client_rect(hwnd)
            if rect is None:
                return False
            left, top, right, bottom = rect
            return left <= x <= right and top <= y <= bottom
        except Exception:
            return False

    def get_window_size(self, hwnd: int) -> Tuple[int, int]:
        """
        获取窗口客户区大小

        Args:
            hwnd: 窗口句柄

        Returns:
            tuple: 客户区大小 (width, height)
        """
        try:
            rect = WindowMessage.get_window_client_rect(hwnd)
            if rect is None:
                return (0, 0)
            left, top, right, bottom = rect
            return (right - left, bottom - top)
        except Exception as e:
            raise RuntimeError(f"获取窗口大小失败: {e}")

    def click_and_wait(self, hwnd: int, x: int, y: int, wait_time: float, button: str = "left", double: bool = False) -> bool:
        """
        点击并等待

        Args:
            hwnd: 窗口句柄
            x: X坐标
            y: Y坐标
            wait_time: 等待时间（秒）
            button: 鼠标按键
            double: 是否双击

        Returns:
            bool: 是否成功
        """
        
        try:
            # 点击
            self.send_click(hwnd, x, y, button, double)
            # 等待
            time.sleep(wait_time)
            return True

        except Exception as e:
            raise RuntimeError(f"点击并等待失败: {e}")

    def send_complex_gesture(self, hwnd: int, gesture_points: List[Tuple[int, int]], button: str = "left") -> bool:
        """
        发送复杂手势（多段拖拽）

        Args:
            hwnd: 窗口句柄
            gesture_points: 手势点列表 [(x1, y1), (x2, y2), ...]
            button: 鼠标按键

        Returns:
            bool: 是否成功
        """
        
        try:
            if len(gesture_points) < 2:
                raise ValueError("手势点至少需要2个点")

            # 按下鼠标在第一个点
            start_x, start_y = gesture_points[0]
            self.send_move(hwnd, start_x, start_y)
            time.sleep(0.01)

            if button.lower() == "left":
                WindowMessage.send_message(hwnd, win32con.WM_LBUTTONDOWN, WindowMessage.MOUSE_LEFT_DOWN,
                                            (start_y << 16) | (start_x & 0xFFFF))
            elif button.lower() == "right":
                WindowMessage.send_message(hwnd, win32con.WM_RBUTTONDOWN, WindowMessage.MOUSE_RIGHT_DOWN,
                                            (start_y << 16) | (start_x & 0xFFFF))
            else:
                raise ValueError(f"不支持的鼠标按键: {button}")

            time.sleep(0.01)

            # 移动到各个点
            for x, y in gesture_points[1:]:
                self.send_move(hwnd, x, y)
                time.sleep(0.005)  # 手势移动时延迟较短

            # 释放鼠标
            end_x, end_y = gesture_points[-1]
            if button.lower() == "left":
                WindowMessage.send_message(hwnd, win32con.WM_LBUTTONUP, WindowMessage.MOUSE_LEFT_UP,
                                            (end_y << 16) | (end_x & 0xFFFF))
            elif button.lower() == "right":
                WindowMessage.send_message(hwnd, win32con.WM_RBUTTONUP, WindowMessage.MOUSE_RIGHT_UP,
                                            (end_y << 16) | (end_x & 0xFFFF))

            return True

        except Exception as e:
            raise RuntimeError(f"发送复杂手势失败: {e}")

    def center_click(self, hwnd: int, button: str = "left", double: bool = False) -> bool:
        """
        点击窗口中心

        Args:
            hwnd: 窗口句柄
            button: 鼠标按键
            double: 是否双击

        Returns:
            bool: 是否成功
        """
        try:
            width, height = self.get_window_size(hwnd)
            center_x = width // 2
            center_y = height // 2
            return self.send_click(hwnd, center_x, center_y, button, double)

        except Exception as e:
            raise RuntimeError(f"点击窗口中心失败: {e}")

    # ==================== 精细控制API ====================

    def mouse_down_press(self, hwnd: int, x: int, y: int, button: str = "left") -> bool:
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
            return WindowMessage.mouse_down_press(hwnd, x, y, button)
        except Exception as e:
            raise RuntimeError(f"鼠标按下失败: {e}")

    def mouse_down_release(self, hwnd: int, x: int, y: int, button: str = "left") -> bool:
        """
        精确控制：释放鼠标（从按下状态释放）

        Args:
            hwnd: 窗口句柄
            x: 客户区X坐标
            y: 客户区Y坐标
            button: 鼠标按键 ('left', 'right', 'middle')

        Returns:
            bool: 是否成功
        """
        
        try:
            return WindowMessage.mouse_down_release(hwnd, x, y, button)
        except Exception as e:
            raise RuntimeError(f"鼠标释放失败: {e}")

    def mouse_up_press(self, hwnd: int, x: int, y: int, button: str = "left") -> bool:
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
        
        try:
            return WindowMessage.mouse_up_press(hwnd, x, y, button)
        except Exception as e:
            raise RuntimeError(f"鼠标抬起按下失败: {e}")

    def mouse_up_release(self, hwnd: int, x: int, y: int, button: str = "left") -> bool:
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
        
        try:
            return WindowMessage.mouse_up_release(hwnd, x, y, button)
        except Exception as e:
            raise RuntimeError(f"鼠标抬起释放失败: {e}")

    def mouse_press_and_hold(self, hwnd: int, x: int, y: int, button: str = "left", duration: float = 0.1) -> bool:
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
            return WindowMessage.mouse_press_and_hold(hwnd, x, y, button, duration)
        except Exception as e:
            raise RuntimeError(f"鼠标保持失败: {e}")

    def send_mouse_sequence(self, hwnd: int, mouse_sequence: List[Tuple[str, int, int, bool]]) -> bool:
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
            return WindowMessage.send_mouse_sequence(hwnd, mouse_sequence)
        except Exception as e:
            raise RuntimeError(f"发送鼠标序列失败: {e}")

    def press_mouse_precisely(self, hwnd: int, x: int, y: int, button: str = "left", duration: float = 0.01) -> bool:
        """
        精确按下并快速释放鼠标（比send_click更精确）

        Args:
            hwnd: 窗口句柄
            x: 客户区X坐标
            y: 客户区Y坐标
            button: 鼠标按键
            duration: 按下时长（秒）

        Returns:
            bool: 是否成功
        """
        
        try:
            if not self.mouse_down_press(hwnd, x, y, button):
                return False

            time.sleep(duration)

            return self.mouse_down_release(hwnd, x, y, button)

        except Exception as e:
            raise RuntimeError(f"精确鼠标按下失败: {e}")

    def toggle_mouse_button(self, hwnd: int, x: int, y: int, button: str = "left") -> bool:
        """
        切换鼠标按钮状态

        Args:
            hwnd: 窗口句柄
            x: 客户区X坐标
            y: 客户区Y坐标
            button: 鼠标按键

        Returns:
            bool: 是否成功
        """
        
        try:
            # 检查当前状态（简化实现）
            # 实际应用中可以通过特定方法检查鼠标状态

            # 模拟按下
            return self.mouse_press_and_hold(hwnd, x, y, button, 0.05)

        except Exception as e:
            raise RuntimeError(f"切换鼠标按钮失败: {e}")

    def send_multi_button_press(self, hwnd: int, x: int, y: int, buttons: List[str]) -> bool:
        """
        同时按下多个鼠标按钮

        Args:
            hwnd: 窗口句柄
            x: 客户区X坐标
            y: 客户区Y坐标
            buttons: 按钮列表 ['left', 'right', 'middle']

        Returns:
            bool: 是否成功
        """
        
        try:
            # 按下所有按钮
            for button in buttons:
                if not self.mouse_down_press(hwnd, x, y, button):
                    # 如果失败，释放已按下的按钮
                    for prev_button in buttons[:buttons.index(button)]:
                        self.mouse_down_release(hwnd, x, y, prev_button)
                    return False
                time.sleep(0.001)

            return True

        except Exception as e:
            raise RuntimeError(f"多按钮按下失败: {e}")

    def release_multi_button(self, hwnd: int, x: int, y: int, buttons: List[str]) -> bool:
        """
        释放多个鼠标按钮

        Args:
            hwnd: 窗口句柄
            x: 客户区X坐标
            y: 客户区Y坐标
            buttons: 按钮列表 ['left', 'right', 'middle']

        Returns:
            bool: 是否成功
        """
        
        try:
            # 相反顺序释放按钮
            for button in reversed(buttons):
                if not self.mouse_down_release(hwnd, x, y, button):
                    return False
                time.sleep(0.001)

            return True

        except Exception as e:
            raise RuntimeError(f"多按钮释放失败: {e}")

    def send_complex_click_sequence(self, hwnd: int, sequence: List[Tuple[int, int, str, bool, Optional[float]]]) -> bool:
        """
        发送复杂点击序列（每个点击可以指定按钮、状态和时长）

        Args:
            hwnd: 窗口句柄
            sequence: 序列列表，每个元素为 (x, y, button, is_press, duration) ，
                     is_press为True表示按下，False表示释放，duration为按下时长（秒）

        Returns:
            bool: 是否成功
        """
        
        try:
            for x, y, button, is_press, duration in sequence:
                if is_press:
                    # 按下
                    if duration is None or duration <= 0:
                        # 立即按下并保持
                        if not self.mouse_down_press(hwnd, x, y, button):
                            return False
                    else:
                        # 按下指定时间后自动释放
                        if not self.mouse_press_and_hold(hwnd, x, y, button, duration):
                            return False
                else:
                    # 释放
                    if not self.mouse_down_release(hwnd, x, y, button):
                        return False

                time.sleep(0.001)  # 微小延迟

            return True

        except Exception as e:
            raise RuntimeError(f"发送复杂点击序列失败: {e}")

    def simulate_mouse_gesture(self, hwnd: int, gesture: List[Tuple[int, int, Optional[str], Optional[float]]]) -> bool:
        """
        模拟鼠标手势（每个点可以指定按键和按下时间）

        Args:
            hwnd: 窗口句柄
            gesture: 手势列表，每个元素为 (x, y, button, press_duration) ，
                    button为鼠标按键，press_duration为按下时长（秒），None表示移动

        Returns:
            bool: 是否成功
        """
        
        try:
            if len(gesture) < 2:
                raise ValueError("手势点至少需要2个点")

            # 移动到起始位置
            start_x, start_y, button, press_duration = gesture[0]
            self.send_move(hwnd, start_x, start_y)
            time.sleep(0.01)

            # 如果第一个点指定了按键和时长，则按下
            if button is not None and press_duration is not None:
                if not self.mouse_press_and_hold(hwnd, start_x, start_y, button, press_duration):
                    return False
            elif button is not None:
                if not self.mouse_down_press(hwnd, start_x, start_y, button):
                    return False

            # 移动到后续点
            for x, y, button, press_duration in gesture[1:]:
                self.send_move(hwnd, x, y)
                time.sleep(0.005)  # 手势移动时延迟较短

                # 如果指定了按键和时长，则处理
                if button is not None and press_duration is not None:
                    if not self.mouse_press_and_hold(hwnd, x, y, button, press_duration):
                        return False
                elif button is not None:
                    if not self.mouse_down_press(hwnd, x, y, button):
                        return False

            return True

        except Exception as e:
            raise RuntimeError(f"模拟鼠标手势失败: {e}")

    def build_mouse_lparam(self, x: int, y: int) -> int:
        """
        构建鼠标消息的lparam值

        Args:
            x: X坐标
            y: Y坐标

        Returns:
            int: lparam值
        """
        return WindowMessage.build_lparam_for_mouse(x, y)

    def get_mouse_button_state(self, button: str) -> bool:
        """
        获取鼠标按钮状态

        Args:
            button: 鼠标按键 ('left', 'right', 'middle')

        Returns:
            bool: 按钮是否被按下
        """
        try:
            # 使用GetAsyncKeyState获取鼠标状态
            if button.lower() == 'left':
                return (user32.GetAsyncKeyState(0x01) & 0x8000) != 0
            elif button.lower() == 'right':
                return (user32.GetAsyncKeyState(0x02) & 0x8000) != 0
            elif button.lower() == 'middle':
                return (user32.GetAsyncKeyState(0x04) & 0x8000) != 0
            else:
                return False
        except Exception:
            return False

    def wait_for_mouse_release(self, hwnd: int, button: str, timeout: float = 5.0) -> bool:
        """
        等待鼠标按钮释放

        Args:
            hwnd: 窗口句柄
            button: 鼠标按键
            timeout: 超时时间（秒）

        Returns:
            bool: 是否在超时前释放
        """
        try:
            start_time = time.time()

            while time.time() - start_time < timeout:
                if not self.get_mouse_button_state(button):
                    return True
                time.sleep(0.01)

            return False  # 超时

        except Exception as e:
            raise RuntimeError(f"等待鼠标释放失败: {e}")