#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输入管理器

整合键盘和鼠标输入功能，提供统一的API接口
使用Win32 API的SendMessage实现对非活动窗口的自动化控制
"""

import time
from typing import Optional, Dict, Any, Union, List, Tuple
import threading

from .keyboard import KeyboardInput
from .mouse import MouseInput
from .window_message import WindowMessage
from ..global_manager import get_global, set_global, log_info, log_warning, log_error


class InputManager:
    """输入管理器主类"""

    def __init__(self):
        """初始化输入管理器"""
        self.keyboard = KeyboardInput()
        self.mouse = MouseInput()
        # 移除锁机制避免死锁
        self._is_enabled = True

        # 从全局状态获取目标窗口
        self._target_window = None
        self._update_target_window()

        # 监听全局状态变化
        self._register_global_listeners()

    def _update_target_window(self):
        """更新目标窗口"""
        try:
            self._target_window = get_global('target_window')
        except Exception:
            self._target_window = None

    def _register_global_listeners(self):
        """注册全局状态监听器"""
        try:
            from ..global_manager import add_global_listener
            add_global_listener('target_window', self._on_target_window_change)
        except ImportError:
            # 如果无法导入global_manager，静默处理
            pass

    def _on_target_window_change(self, key: str, value: Any):
        """目标窗口变化回调"""
        self._target_window = value
        if value:
            log_info(f"输入管理器已切换到目标窗口: {value.title}")
        else:
            log_warning("输入管理器：未找到目标窗口")

    def get_target_window_handle(self) -> Optional[int]:
        """获取目标窗口句柄"""
        if self._target_window and hasattr(self._target_window, 'handle'):
            return self._target_window.handle
        return None

    def is_window_focused(self, hwnd: Optional[int] = None) -> bool:
        """检查窗口是否获得焦点"""
        if hwnd is None:
            hwnd = self.get_target_window_handle()

        if not hwnd:
            return False

        try:
            import win32gui
            foreground_hwnd = win32gui.GetForegroundWindow()
            return foreground_hwnd == hwnd
        except Exception:
            return False

    def ensure_window_focus(self, hwnd: Optional[int] = None) -> bool:
        """确保窗口获得焦点"""
        if hwnd is None:
            hwnd = self.get_target_window_handle()

        if not hwnd:
            raise ValueError("未设置目标窗口")

        try:
            return WindowMessage.send_focus(hwnd)
        except Exception as e:
            log_error(f"设置窗口焦点失败: {e}")
            return False

    # ==================== 高级操作方法 ====================

    def type_text(self, text: str, delay: float = 0.01, use_target_window: bool = True) -> bool:
        """
        向目标窗口输入文本

        Args:
            text: 要输入的文本
            delay: 字符间延迟
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法输入文本")

            log_info(f"输入文本: {text[:50]}{'...' if len(text) > 50 else ''}")
            return self.keyboard.send_keys(hwnd, text, delay)

        except Exception as e:
            log_error(f"输入文本失败: {e}")
            return False

    def press_key(self, key: str, repeat: int = 1, delay: float = 0.01, use_target_window: bool = True) -> bool:
        """
        按下指定键

        Args:
            key: 键名
            repeat: 重复次数
            delay: 延迟
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法按键")

            log_info(f"按键: {key} x{repeat}")
            return self.keyboard.send_key(hwnd, key, repeat, delay)

        except Exception as e:
            log_error(f"按键失败: {e}")
            return False

    def click(self, x: int, y: int, button: str = "left", double: bool = False, use_target_window: bool = True) -> bool:
        """
        点击指定位置

        Args:
            x: X坐标（客户区坐标）
            y: Y坐标（客户区坐标）
            button: 鼠标按键
            double: 是否双击
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法点击")

            log_info(f"点击位置: ({x}, {y}) {button}{' 双击' if double else ''}")
            return self.mouse.send_click(hwnd, x, y, button, double)

        except Exception as e:
            log_error(f"点击失败: {e}")
            return False

    def move_to(self, x: int, y: int, use_target_window: bool = True) -> bool:
        """
        移动鼠标到指定位置

        Args:
            x: X坐标（客户区坐标）
            y: Y坐标（客户区坐标）
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法移动鼠标")

            return self.mouse.send_move(hwnd, x, y)

        except Exception as e:
            log_error(f"移动鼠标失败: {e}")
            return False

    def scroll(self, direction: str, lines: int = 3, x: int = 0, y: int = 0, use_target_window: bool = True) -> bool:
        """
        滚动滚轮

        Args:
            direction: 滚动方向 ('up', 'down', 'left', 'right')
            lines: 滚动行数
            x: X坐标（客户区坐标）
            y: Y坐标（客户区坐标）
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法滚动")

            log_info(f"滚动: {direction} {lines}行")
            return self.mouse.send_scroll(hwnd, direction, lines, x, y)

        except Exception as e:
            log_error(f"滚动失败: {e}")
            return False

    # ==================== 常用快捷操作 ====================

    def copy(self, use_target_window: bool = True) -> bool:
        """复制（Ctrl+C）"""
        return self.press_key('ctrl+c', use_target_window=use_target_window)

    def paste(self, use_target_window: bool = True) -> bool:
        """粘贴（Ctrl+V）"""
        return self.press_key('ctrl+v', use_target_window=use_target_window)

    def cut(self, use_target_window: bool = True) -> bool:
        """剪切（Ctrl+X）"""
        return self.press_key('ctrl+x', use_target_window=use_target_window)

    def select_all(self, use_target_window: bool = True) -> bool:
        """全选（Ctrl+A）"""
        return self.press_key('ctrl+a', use_target_window=use_target_window)

    def save(self, use_target_window: bool = True) -> bool:
        """保存（Ctrl+S）"""
        return self.press_key('ctrl+s', use_target_window=use_target_window)

    def undo(self, use_target_window: bool = True) -> bool:
        """撤销（Ctrl+Z）"""
        return self.press_key('ctrl+z', use_target_window=use_target_window)

    def redo(self, use_target_window: bool = True) -> bool:
        """重做（Ctrl+Y）"""
        return self.press_key('ctrl+y', use_target_window=use_target_window)

    def enter(self, use_target_window: bool = True) -> bool:
        """回车"""
        return self.press_key('enter', use_target_window=use_target_window)

    def escape(self, use_target_window: bool = True) -> bool:
        """Esc键"""
        return self.press_key('esc', use_target_window=use_target_window)

    def tab(self, use_target_window: bool = True) -> bool:
        """Tab键"""
        return self.press_key('tab', use_target_window=use_target_window)

    def space(self, use_target_window: bool = True) -> bool:
        """空格键"""
        return self.press_key('space', use_target_window=use_target_window)

    # ==================== 组合操作 ====================

    def click_and_type(self, x: int, y: int, text: str, button: str = "left", delay: float = 0.01) -> bool:
        """
        点击位置后输入文本

        Args:
            x: X坐标
            y: Y坐标
            text: 要输入的文本
            button: 鼠标按键
            delay: 字符间延迟

        Returns:
            bool: 是否成功
        """
        
        try:
            # 点击位置
            if not self.click(x, y, button):
                return False

            time.sleep(0.05)  # 等待点击生效

            # 输入文本
            return self.type_text(text, delay)

        except Exception as e:
            log_error(f"点击并输入失败: {e}")
            return False

    def drag_and_drop(self, start_x: int, start_y: int, end_x: int, end_y: int, button: str = "left") -> bool:
        """
        拖拽操作

        Args:
            start_x: 起始X坐标
            start_y: 起始Y坐标
            end_x: 结束X坐标
            end_y: 结束Y坐标
            button: 鼠标按键

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle()
            if not hwnd:
                raise ValueError("未设置目标窗口，无法拖拽")

            log_info(f"拖拽: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
            return self.mouse.send_drag(hwnd, start_x, start_y, end_x, end_y, button)

        except Exception as e:
            log_error(f"拖拽失败: {e}")
            return False

    # ==================== 状态管理 ====================

    def enable(self):
        """启用输入管理器"""
        self._is_enabled = True
        log_info("输入管理器已启用")

    def disable(self):
        """禁用输入管理器"""
        self._is_enabled = False
        log_info("输入管理器已禁用")

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._is_enabled

    # ==================== 工具方法 ====================

    def get_window_info(self) -> Optional[Dict[str, Any]]:
        """获取当前目标窗口信息"""
        if not self._target_window:
            return None

        hwnd = self.get_target_window_handle()
        if not hwnd:
            return None

        try:
            width, height = self.mouse.get_window_size(hwnd)
            is_focused = self.is_window_focused(hwnd)

            return {
                'title': self._target_window.title,
                'handle': hwnd,
                'size': (width, height),
                'is_focused': is_focused,
                'is_valid': WindowMessage.is_valid_window(hwnd)
            }
        except Exception as e:
            log_error(f"获取窗口信息失败: {e}")
            return None

    def set_custom_window(self, hwnd: int) -> bool:
        """
        设置自定义目标窗口

        Args:
            hwnd: 窗口句柄

        Returns:
            bool: 是否成功
        """
        try:
            if not WindowMessage.is_valid_window(hwnd):
                raise ValueError(f"无效的窗口句柄: {hwnd}")

            # 临时设置窗口信息
            import win32gui
            title = win32gui.GetWindowText(hwnd)

            # 更新全局状态
            set_global('target_window', self._target_window, notify=True)

            log_info(f"已设置自定义目标窗口: {title}")
            return True

        except Exception as e:
            log_error(f"设置自定义窗口失败: {e}")
            return False

    def execute_action_sequence(self, actions: List[Dict[str, Any]]) -> bool:
        """
        执行动作序列

        Args:
            actions: 动作列表，每个动作为字典

        动作格式示例:
        [
            {'type': 'click', 'x': 100, 'y': 200, 'delay': 0.1},
            {'type': 'type', 'text': 'Hello World', 'delay': 0.01},
            {'type': 'key', 'key': 'enter', 'delay': 0.05},
            {'type': 'wait', 'duration': 1.0}
        ]

        Returns:
            bool: 是否成功
        """
        
        try:
            log_info(f"开始执行动作序列，共{len(actions)}个动作")

            for i, action in enumerate(actions):
                action_type = action.get('type')
                delay = action.get('delay', 0.1)

                if action_type == 'click':
                    self.click(
                        action['x'],
                        action['y'],
                        action.get('button', 'left'),
                        action.get('double', False),
                        use_target_window=True
                    )
                elif action_type == 'type':
                    self.type_text(
                        action['text'],
                        action.get('char_delay', 0.01),
                        use_target_window=True
                    )
                elif action_type == 'key':
                    self.press_key(
                        action['key'],
                        action.get('repeat', 1),
                        action.get('delay', 0.01),
                        use_target_window=True
                    )
                elif action_type == 'scroll':
                    self.scroll(
                        action['direction'],
                        action.get('lines', 3),
                        action.get('x', 0),
                        action.get('y', 0),
                        use_target_window=True
                    )
                elif action_type == 'wait':
                    time.sleep(action.get('duration', 1.0))
                else:
                    log_warning(f"未知的动作类型: {action_type}")
                    continue

                if i < len(actions) - 1:  # 最后一次动作后不延迟
                    time.sleep(delay)

            log_info("动作序列执行完成")
            return True

        except Exception as e:
            log_error(f"执行动作序列失败: {e}")
            return False

    # ==================== 精细控制API ====================

    # ===== 键盘精细控制 =====

    def key_down_press(self, key: Union[str, int], use_target_window: bool = True) -> bool:
        """
        精确控制：按键按下（保持按下状态，不自动释放）

        Args:
            key: 键名或虚拟键码
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法按键按下")

            log_info(f"按键按下: {key}")
            return self.keyboard.key_down_press(hwnd, key)

        except Exception as e:
            log_error(f"按键按下失败: {e}")
            return False

    def key_down_release(self, key: Union[str, int], use_target_window: bool = True) -> bool:
        """
        精确控制：释放按键（从按下状态释放）

        Args:
            key: 键名或虚拟键码
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法释放按键")

            log_info(f"按键释放: {key}")
            return self.keyboard.key_down_release(hwnd, key)

        except Exception as e:
            log_error(f"按键释放失败: {e}")
            return False

    def key_press_and_hold(self, key: Union[str, int], duration: float, use_target_window: bool = True) -> bool:
        """
        按下并保持按键指定时间

        Args:
            key: 键名或虚拟键码
            duration: 保持时间（秒）
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法按键保持")

            log_info(f"按键保持: {key} ({duration}秒)")
            return self.keyboard.key_press_and_hold(hwnd, key, duration)

        except Exception as e:
            log_error(f"按键保持失败: {e}")
            return False

    def send_key_sequence(self, key_sequence: List[Tuple[str, bool]], use_target_window: bool = True) -> bool:
        """
        发送按键序列（用于精确控制按键时序）

        Args:
            key_sequence: 按键序列，每个元素为 (key, is_press) ，
                        is_press=True表示按下，False表示释放
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法发送按键序列")

            log_info(f"发送按键序列: {len(key_sequence)}个操作")
            return self.keyboard.send_key_sequence(hwnd, key_sequence)

        except Exception as e:
            log_error(f"发送按键序列失败: {e}")
            return False

    def is_key_pressed(self, key: Union[str, int], use_target_window: bool = True) -> bool:
        """
        检查指定键是否当前被按下

        Args:
            key: 键名或虚拟键码
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 键是否被按下
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                return False

            return self.keyboard.is_key_pressed(hwnd, key)

        except Exception as e:
            log_error(f"检查按键状态失败: {e}")
            return False

    def wait_for_key_release(self, key: Union[str, int], timeout: float = 5.0, use_target_window: bool = True) -> bool:
        """
        等待按键释放

        Args:
            key: 键名或虚拟键码
            timeout: 超时时间（秒）
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否在超时前释放
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                return False

            log_info(f"等待按键释放: {key} (超时: {timeout}秒)")
            return self.keyboard.wait_for_key_release(hwnd, key, timeout)

        except Exception as e:
            log_error(f"等待按键释放失败: {e}")
            return False

    def press_modifiers_precisely(self, modifiers: List[str], use_target_window: bool = True) -> bool:
        """
        精确按下多个修饰键（不释放）

        Args:
            modifiers: 修饰键列表 ['ctrl', 'shift', 'alt', 'win']
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法按下修饰键")

            log_info(f"精确按下修饰键: {modifiers}")
            return self.keyboard.press_modifiers_precisely(hwnd, modifiers)

        except Exception as e:
            log_error(f"按下修饰键失败: {e}")
            return False

    def release_modifiers_precisely(self, modifiers: List[str], use_target_window: bool = True) -> bool:
        """
        精确释放多个修饰键

        Args:
            modifiers: 修饰键列表 ['ctrl', 'shift', 'alt', 'win']
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法释放修饰键")

            log_info(f"精确释放修饰键: {modifiers}")
            return self.keyboard.release_modifiers_precisely(hwnd, modifiers)

        except Exception as e:
            log_error(f"释放修饰键失败: {e}")
            return False

    def send_chord_key(self, modifiers: List[str], main_key: str, use_target_window: bool = True) -> bool:
        """
        发送弦键（修饰键+主键的组合）

        Args:
            modifiers: 修饰键列表
            main_key: 主键名
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法发送弦键")

            log_info(f"发送弦键: {'+'.join(modifiers)}+{main_key}")
            return self.keyboard.send_chord_key(hwnd, modifiers, main_key)

        except Exception as e:
            log_error(f"发送弦键失败: {e}")
            return False

    def toggle_key(self, key: Union[str, int], use_target_window: bool = True) -> bool:
        """
        切换按键状态（如果当前按下则释放，如果当前释放则按下）

        Args:
            key: 键名或虚拟键码
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法切换按键")

            log_info(f"切换按键: {key}")
            return self.keyboard.toggle_key(hwnd, key)

        except Exception as e:
            log_error(f"切换按键失败: {e}")
            return False

    def send_pressurized_key_sequence(self, sequence: List[Tuple[Union[str, int], bool, Optional[float]]], use_target_window: bool = True) -> bool:
        """
        发送带压力的按键序列（每个键可以指定按下时间和状态）

        Args:
            sequence: 序列列表，每个元素为 (key, is_press, duration) ，
                     is_press为True表示按下，False表示释放，duration为按下时长（秒）
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法发送压力序列")

            log_info(f"发送压力按键序列: {len(sequence)}个操作")
            return self.keyboard.send_pressurized_key_sequence(hwnd, sequence)

        except Exception as e:
            log_error(f"发送压力按键序列失败: {e}")
            return False

    # ===== 鼠标精细控制 =====

    def mouse_down_press(self, x: int, y: int, button: str = "left", use_target_window: bool = True) -> bool:
        """
        精确控制：鼠标按下（保持按下状态，不自动释放）

        Args:
            x: 客户区X坐标
            y: 客户区Y坐标
            button: 鼠标按键 ('left', 'right', 'middle')
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法鼠标按下")

            log_info(f"鼠标按下: ({x}, {y}) {button}")
            return self.mouse.mouse_down_press(hwnd, x, y, button)

        except Exception as e:
            log_error(f"鼠标按下失败: {e}")
            return False

    def mouse_down_release(self, x: int, y: int, button: str = "left", use_target_window: bool = True) -> bool:
        """
        精确控制：释放鼠标（从按下状态释放）

        Args:
            x: 客户区X坐标
            y: 客户区Y坐标
            button: 鼠标按键 ('left', 'right', 'middle')
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法释放鼠标")

            log_info(f"鼠标释放: ({x}, {y}) {button}")
            return self.mouse.mouse_down_release(hwnd, x, y, button)

        except Exception as e:
            log_error(f"鼠标释放失败: {e}")
            return False

    def mouse_press_and_hold(self, x: int, y: int, button: str = "left", duration: float = 0.1, use_target_window: bool = True) -> bool:
        """
        按下并保持鼠标指定时间

        Args:
            x: 客户区X坐标
            y: 客户区Y坐标
            button: 鼠标按键
            duration: 保持时间（秒）
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法鼠标保持")

            log_info(f"鼠标保持: ({x}, {y}) {button} ({duration}秒)")
            return self.mouse.mouse_press_and_hold(hwnd, x, y, button, duration)

        except Exception as e:
            log_error(f"鼠标保持失败: {e}")
            return False

    def send_mouse_sequence(self, mouse_sequence: List[Tuple[str, int, int, bool]], use_target_window: bool = True) -> bool:
        """
        发送鼠标序列（用于精确控制鼠标时序）

        Args:
            mouse_sequence: 鼠标序列，每个元素为 (action, x, y, is_press) ，
                          action为 'left', 'right', 'middle'，is_press为True表示按下，False表示释放
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法发送鼠标序列")

            log_info(f"发送鼠标序列: {len(mouse_sequence)}个操作")
            return self.mouse.send_mouse_sequence(hwnd, mouse_sequence)

        except Exception as e:
            log_error(f"发送鼠标序列失败: {e}")
            return False

    def press_mouse_precisely(self, x: int, y: int, button: str = "left", duration: float = 0.01, use_target_window: bool = True) -> bool:
        """
        精确按下并快速释放鼠标（比send_click更精确）

        Args:
            x: 客户区X坐标
            y: 客户区Y坐标
            button: 鼠标按键
            duration: 按下时长（秒）
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法精确鼠标按下")

            log_info(f"精确鼠标按下: ({x}, {y}) {button} ({duration}秒)")
            return self.mouse.press_mouse_precisely(hwnd, x, y, button, duration)

        except Exception as e:
            log_error(f"精确鼠标按下失败: {e}")
            return False

    def send_multi_button_press(self, x: int, y: int, buttons: List[str], use_target_window: bool = True) -> bool:
        """
        同时按下多个鼠标按钮

        Args:
            x: 客户区X坐标
            y: 客户区Y坐标
            buttons: 按钮列表 ['left', 'right', 'middle']
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法多按钮按下")

            log_info(f"多按钮按下: ({x}, {y}) {buttons}")
            return self.mouse.send_multi_button_press(hwnd, x, y, buttons)

        except Exception as e:
            log_error(f"多按钮按下失败: {e}")
            return False

    def release_multi_button(self, x: int, y: int, buttons: List[str], use_target_window: bool = True) -> bool:
        """
        释放多个鼠标按钮

        Args:
            x: 客户区X坐标
            y: 客户区Y坐标
            buttons: 按钮列表 ['left', 'right', 'middle']
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法多按钮释放")

            log_info(f"多按钮释放: ({x}, {y}) {buttons}")
            return self.mouse.release_multi_button(hwnd, x, y, buttons)

        except Exception as e:
            log_error(f"多按钮释放失败: {e}")
            return False

    def send_complex_click_sequence(self, sequence: List[Tuple[int, int, str, bool, Optional[float]]], use_target_window: bool = True) -> bool:
        """
        发送复杂点击序列（每个点击可以指定按钮、状态和时长）

        Args:
            sequence: 序列列表，每个元素为 (x, y, button, is_press, duration) ，
                     is_press为True表示按下，False表示释放，duration为按下时长（秒）
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法发送复杂点击序列")

            log_info(f"发送复杂点击序列: {len(sequence)}个操作")
            return self.mouse.send_complex_click_sequence(hwnd, sequence)

        except Exception as e:
            log_error(f"发送复杂点击序列失败: {e}")
            return False

    def simulate_mouse_gesture(self, gesture: List[Tuple[int, int, Optional[str], Optional[float]]], use_target_window: bool = True) -> bool:
        """
        模拟鼠标手势（每个点可以指定按键和按下时间）

        Args:
            gesture: 手势列表，每个元素为 (x, y, button, press_duration) ，
                    button为鼠标按键，press_duration为按下时长（秒），None表示移动
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法模拟鼠标手势")

            log_info(f"模拟鼠标手势: {len(gesture)}个点")
            return self.mouse.simulate_mouse_gesture(hwnd, gesture)

        except Exception as e:
            log_error(f"模拟鼠标手势失败: {e}")
            return False

    def get_mouse_button_state(self, button: str) -> bool:
        """
        获取鼠标按钮状态

        Args:
            button: 鼠标按键 ('left', 'right', 'middle')

        Returns:
            bool: 按钮是否被按下
        """
        try:
            return self.mouse.get_mouse_button_state(button)
        except Exception as e:
            log_error(f"获取鼠标按钮状态失败: {e}")
            return False

    def wait_for_mouse_release(self, button: str, timeout: float = 5.0, use_target_window: bool = True) -> bool:
        """
        等待鼠标按钮释放

        Args:
            button: 鼠标按键
            timeout: 超时时间（秒）
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否在超时前释放
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                return False

            log_info(f"等待鼠标释放: {button} (超时: {timeout}秒)")
            return self.mouse.wait_for_mouse_release(hwnd, button, timeout)

        except Exception as e:
            log_error(f"等待鼠标释放失败: {e}")
            return False

    # ===== 系统级控制 =====

    def simulate_menu_shortcut(self, key: str, use_target_window: bool = True) -> bool:
        """
        模拟菜单快捷键（如Alt+F, Alt+E等）

        Args:
            key: 快捷键字母
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法模拟菜单快捷键")

            log_info(f"模拟菜单快捷键: Alt+{key}")
            return self.keyboard.simulate_menu_shortcut(hwnd, key)

        except Exception as e:
            log_error(f"模拟菜单快捷键失败: {e}")
            return False

    def send_system_command(self, command: str, use_target_window: bool = True) -> bool:
        """
        发送系统命令（如最大化、最小化、关闭等）

        Args:
            command: 命令名称 ('minimize', 'maximize', 'restore', 'close', 'activate')
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法发送系统命令")

            log_info(f"发送系统命令: {command}")
            return WindowMessage.send_system_command(hwnd, command)

        except Exception as e:
            log_error(f"发送系统命令失败: {e}")
            return False

    def send_raw_input_event(self, event_type: str, x: int = 0, y: int = 0, data: int = 0, use_target_window: bool = True) -> bool:
        """
        发送原始输入事件

        Args:
            event_type: 事件类型 ('mouse', 'keyboard')
            x: X坐标
            y: Y坐标
            data: 附加数据
            use_target_window: 是否使用目标窗口

        Returns:
            bool: 是否成功
        """
        
        try:
            hwnd = self.get_target_window_handle() if use_target_window else None
            if not hwnd:
                raise ValueError("未设置目标窗口，无法发送原始输入事件")

            log_info(f"发送原始输入事件: {event_type}")
            return WindowMessage.send_raw_input_event(hwnd, event_type, x, y, data)

        except Exception as e:
            log_error(f"发送原始输入事件失败: {e}")
            return False

    # ===== 工具方法 =====

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