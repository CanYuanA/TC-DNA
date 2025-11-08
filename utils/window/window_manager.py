#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
窗口管理器

提供Windows窗口的查找、操作、管理功能
使用pywin32库实现
"""

import time
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import os

try:
    import win32gui
    import win32api
    import win32con
    import win32process
    import win32pipe
    import win32event
    import psutil
    import pywintypes
except ImportError as e:
    print(f"错误：缺少必要的库 - {e}")
    print("请运行: pip install pywin32 psutil")
    raise


@dataclass
class WindowInfo:
    """窗口信息数据类"""
    title: str = ""
    class_name: str = ""
    handle: int = 0
    rect: Tuple[int, int, int, int] = (0, 0, 0, 0)  # (left, top, right, bottom)
    style: int = 0
    ex_style: int = 0
    pid: int = 0
    process_name: str = ""
    is_visible: bool = False
    is_minimized: bool = False
    is_maximized: bool = False
    width: int = 0
    height: int = 0
    x: int = 0
    y: int = 0

    @property
    def center_x(self) -> int:
        """窗口中心X坐标"""
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        """窗口中心Y坐标"""
        return self.y + self.height // 2

    @property
    def area(self) -> int:
        """窗口面积"""
        return self.width * self.height

    def is_valid(self) -> bool:
        """检查窗口是否有效"""
        return self.handle != 0 and self.title != ""


class WindowNotFoundError(Exception):
    """窗口未找到异常"""
    pass


class WindowManager:
    """窗口管理器"""

    def __init__(self):
        """初始化窗口管理器"""
        self._window_cache = {}
        self._last_cache_time = 0
        self._cache_duration = 1.0  # 缓存持续时间（秒）

    def find_window_by_title(self, title: str, partial_match: bool = True) -> Optional[WindowInfo]:
        """
        根据窗口标题查找窗口

        Args:
            title: 窗口标题
            partial_match: 是否部分匹配

        Returns:
            窗口信息，如果未找到则返回None
        """
        windows = self.enum_windows()
        title_lower = title.lower()

        for window in windows:
            if partial_match:
                if title_lower in window.title.lower():
                    return window
            else:
                if window.title.lower() == title_lower:
                    return window

        return None

    def find_window_by_class(self, class_name: str, partial_match: bool = True) -> Optional[WindowInfo]:
        """
        根据窗口类名查找窗口

        Args:
            class_name: 窗口类名
            partial_match: 是否部分匹配

        Returns:
            窗口信息，如果未找到则返回None
        """
        windows = self.enum_windows()
        class_name_lower = class_name.lower()

        for window in windows:
            if partial_match:
                if class_name_lower in window.class_name.lower():
                    return window
            else:
                if window.class_name.lower() == class_name_lower:
                    return window

        return None

    def find_window_by_process(self, process_name: str, partial_match: bool = True) -> Optional[WindowInfo]:
        """
        根据进程名查找窗口

        Args:
            process_name: 进程名（如"notepad.exe"）
            partial_match: 是否部分匹配

        Returns:
            窗口信息，如果未找到则返回None
        """
        windows = self.enum_windows()
        process_name_lower = process_name.lower()

        for window in windows:
            if partial_match:
                if process_name_lower in window.process_name.lower():
                    return window
            else:
                if window.process_name.lower() == process_name_lower:
                    return window

        return None

    def find_windows_by_title(self, title: str, partial_match: bool = True) -> List[WindowInfo]:
        """
        根据窗口标题查找所有匹配窗口

        Args:
            title: 窗口标题
            partial_match: 是否部分匹配

        Returns:
            窗口信息列表
        """
        windows = self.enum_windows()
        title_lower = title.lower()
        result = []

        for window in windows:
            if partial_match:
                if title_lower in window.title.lower():
                    result.append(window)
            else:
                if window.title.lower() == title_lower:
                    result.append(window)

        return result

    def enum_windows(self, use_cache: bool = True) -> List[WindowInfo]:
        """
        枚举所有窗口

        Args:
            use_cache: 是否使用缓存

        Returns:
            窗口信息列表
        """
        current_time = time.time()

        # 检查缓存
        if use_cache and current_time - self._last_cache_time < self._cache_duration:
            return list(self._window_cache.values())

        windows = []
        window_handles = []

        def enum_windows_callback(hwnd, lParam):
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                window_handles.append(hwnd)
            return True

        try:
            # 枚举窗口
            win32gui.EnumWindows(enum_windows_callback, 0)

            # 获取每个窗口的详细信息
            for hwnd in window_handles:
                try:
                    window_info = self.get_window_info(hwnd)
                    if window_info and window_info.title.strip():
                        windows.append(window_info)
                except Exception as e:
                    logging.debug(f"获取窗口信息失败: {e}")
                    continue

            # 更新缓存
            if use_cache:
                self._window_cache = {w.handle: w for w in windows}
                self._last_cache_time = current_time

            return windows

        except Exception as e:
            logging.error(f"枚举窗口失败: {e}")
            return []

    def get_window_info(self, hwnd: int) -> Optional[WindowInfo]:
        """
        获取窗口详细信息

        Args:
            hwnd: 窗口句柄

        Returns:
            窗口信息
        """
        try:
            # 检查窗口是否有效
            if not win32gui.IsWindow(hwnd):
                return None

            # 获取窗口标题
            try:
                title = win32gui.GetWindowText(hwnd)
            except Exception:
                title = ""

            # 获取窗口类名
            try:
                class_name = win32gui.GetClassName(hwnd)
            except Exception:
                class_name = ""
            if not class_name:
                class_name = ""
            # 获取窗口位置和大小
            try:
                rect = win32gui.GetWindowRect(hwnd)
                left, top, right, bottom = rect
                width = right - left
                height = bottom - top
            except Exception:
                left = top = right = bottom = width = height = 0

            # 获取窗口样式
            try:
                style = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE)
                ex_style = win32api.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            except Exception:
                style = ex_style = 0

            # 检查窗口状态
            try:
                is_visible = win32gui.IsWindowVisible(hwnd)
                is_minimized = win32gui.IsIconic(hwnd)
            except Exception:
                is_visible = is_minimized = False

            # 获取进程信息
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process_name = self._get_process_name_by_pid(pid)
            except Exception:
                pid = 0
                process_name = ""

            # 检查是否最大化
            is_maximized = (style & win32con.WS_MAXIMIZE) != 0

            # 构造窗口信息
            window_info = WindowInfo(
                title=title,
                class_name=class_name,
                handle=hwnd,
                rect=(left, top, right, bottom),
                style=style,
                ex_style=ex_style,
                pid=pid,
                process_name=process_name,
                is_visible=bool(is_visible),
                is_minimized=bool(is_minimized),
                is_maximized=is_maximized,
                width=width,
                height=height,
                x=left,
                y=top
            )

            return window_info

        except Exception as e:
            logging.error(f"获取窗口信息失败: {e}")
            return None

    def _get_process_name_by_pid(self, pid: int) -> str:
        """
        通过进程ID获取进程名

        Args:
            pid: 进程ID

        Returns:
            进程名
        """
        try:
            # 使用psutil获取进程名
            process = psutil.Process(pid)
            return process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            try:
                # 备选方法：使用win32process
                _, modules = win32process.EnumProcessModules(
                    win32api.GetCurrentProcess()
                )
                # 如果是当前进程，尝试获取模块名
                if pid == win32api.GetCurrentProcessId():
                    module_name = win32process.GetModuleFileNameEx(
                        win32api.GetCurrentProcess(), modules[0]
                    )
                    return os.path.basename(module_name)
            except Exception:
                pass
            return ""

    def activate_window(self, hwnd: int) -> bool:
        """
        激活窗口

        Args:
            hwnd: 窗口句柄

        Returns:
            是否成功
        """
        try:
            # 如果窗口最小化，先恢复
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            # 激活窗口
            win32gui.SetForegroundWindow(hwnd)
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

            return True
        except Exception as e:
            logging.error(f"激活窗口失败: {e}")
            return False

    def close_window(self, hwnd: int) -> bool:
        """
        关闭窗口

        Args:
            hwnd: 窗口句柄

        Returns:
            是否成功
        """
        try:
            # 发送关闭消息
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            return True
        except Exception as e:
            logging.error(f"关闭窗口失败: {e}")
            return False

    def minimize_window(self, hwnd: int) -> bool:
        """
        最小化窗口

        Args:
            hwnd: 窗口句柄

        Returns:
            是否成功
        """
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return True
        except Exception as e:
            logging.error(f"最小化窗口失败: {e}")
            return False

    def maximize_window(self, hwnd: int) -> bool:
        """
        最大化窗口

        Args:
            hwnd: 窗口句柄

        Returns:
            是否成功
        """
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return True
        except Exception as e:
            logging.error(f"最大化窗口失败: {e}")
            return False

    def is_window_valid(self, hwnd: int) -> bool:
        """
        检查窗口是否有效

        Args:
            hwnd: 窗口句柄

        Returns:
            是否有效
        """
        try:
            return bool(win32gui.IsWindow(hwnd))
        except Exception:
            return False

    def get_window_rect(self, hwnd: int) -> Optional[Tuple[int, int, int, int]]:
        """
        获取窗口矩形区域

        Args:
            hwnd: 窗口句柄

        Returns:
            窗口矩形 (left, top, right, bottom)
        """
        try:
            return win32gui.GetWindowRect(hwnd)
        except Exception as e:
            logging.error(f"获取窗口矩形失败: {e}")
            return None

    def bring_to_front(self, hwnd: int) -> bool:
        """
        将窗口置于前台

        Args:
            hwnd: 窗口句柄

        Returns:
            是否成功
        """
        try:
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            logging.error(f"置顶窗口失败: {e}")
            return False

    def move_window(self, hwnd: int, x: int, y: int) -> bool:
        """
        移动窗口到指定位置

        Args:
            hwnd: 窗口句柄
            x: 新的X坐标
            y: 新的Y坐标

        Returns:
            是否成功
        """
        try:
            # 获取当前窗口大小
            rect = win32gui.GetWindowRect(hwnd)
            current_width = rect[2] - rect[0]
            current_height = rect[3] - rect[1]

            # 移动窗口
            win32gui.SetWindowPos(
                hwnd,
                0,  # 插入位置（0表示不改变z-order）
                x, y,  # 新的位置
                current_width, current_height,  # 保持当前大小
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            )
            return True
        except Exception as e:
            logging.error(f"移动窗口失败: {e}")
            return False

    def resize_window(self, hwnd: int, width: int, height: int) -> bool:
        """
        调整窗口大小

        Args:
            hwnd: 窗口句柄
            width: 新宽度
            height: 新高度

        Returns:
            是否成功
        """
        try:
            # 获取当前窗口位置
            rect = win32gui.GetWindowRect(hwnd)
            current_x = rect[0]
            current_y = rect[1]

            # 调整窗口大小
            win32gui.SetWindowPos(
                hwnd,
                0,  # 插入位置
                0, 0,  # 位置不变
                width, height,  # 新大小
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE
            )
            return True
        except Exception as e:
            logging.error(f"调整窗口大小失败: {e}")
            return False

    def set_window_always_on_top(self, hwnd: int) -> bool:
        """
        设置窗口始终置于顶层

        Args:
            hwnd: 窗口句柄

        Returns:
            是否成功
        """
        try:
            # 移除当前置顶状态
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
            )
            return True
        except Exception as e:
            logging.error(f"设置窗口置顶失败: {e}")
            return False

    def remove_always_on_top(self, hwnd: int) -> bool:
        """
        移除窗口始终置顶状态

        Args:
            hwnd: 窗口句柄

        Returns:
            是否成功
        """
        try:
            # 恢复到普通窗口
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_NOTOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
            )
            return True
        except Exception as e:
            logging.error(f"移除窗口置顶失败: {e}")
            return False

    def set_client_area_1920x1080(self, hwnd: int) -> bool:
        """
        将窗口客户区调整为1920*1080，并将客户区左上角与屏幕左上角对齐

        Args:
            hwnd: 窗口句柄

        Returns:
            是否成功
        """
        try:
            # 获取窗口边框和标题栏的尺寸
            client_rect = win32gui.GetClientRect(hwnd)
            window_rect = win32gui.GetWindowRect(hwnd)

            # 计算边框和标题栏的额外尺寸
            border_width = (window_rect[2] - window_rect[0]) - client_rect[2]
            title_height = window_rect[3] - window_rect[1] - client_rect[3]

            # 目标客户区大小
            client_width = 1920
            client_height = 1080

            # 计算窗口总大小（包含边框和标题栏）
            total_width = client_width + border_width
            total_height = client_height + title_height

            # 计算目标窗口位置（使客户区左上角对齐屏幕左上角）
            target_x = 0 - border_width // 2
            target_y = 0 - title_height

            # 设置窗口位置到屏幕左上角，总大小为1920*1080客户区+边框
            win32gui.SetWindowPos(
                hwnd,
                0,  # 不改变z-order
                target_x, target_y,  # 目标位置
                total_width, total_height,  # 窗口总大小
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            )

            return True
        except Exception as e:
            logging.error(f"设置1920x1080客户区失败: {e}")
            return False

    def set_foreground_and_1920x1080(self, hwnd: int) -> bool:
        """
        激活窗口并设置1920x1080客户区

        Args:
            hwnd: 窗口句柄

        Returns:
            是否成功
        """
        try:
            # 首先激活窗口
            if not self.activate_window(hwnd):
                logging.warning("激活窗口失败")

            # 设置1920x1080客户区
            if not self.set_client_area_1920x1080(hwnd):
                logging.warning("设置1920x1080客户区失败")

            return True
        except Exception as e:
            logging.error(f"设置窗口前置和1920x1080失败: {e}")
            return False


# 全局窗口管理器实例
_window_manager = None


def get_window_manager() -> WindowManager:
    """获取全局窗口管理器实例"""
    global _window_manager
    if _window_manager is None:
        _window_manager = WindowManager()
    return _window_manager


def find_window(title: Optional[str] = None, class_name: Optional[str] = None, process_name: Optional[str] = None, partial_match: bool = True) -> Optional[WindowInfo]:
    """
    快捷函数：查找窗口

    Args:
        title: 窗口标题
        class_name: 窗口类名
        process_name: 进程名
        partial_match: 是否部分匹配

    Returns:
        窗口信息，如果未找到则返回None
    """
    manager = get_window_manager()

    if title:
        return manager.find_window_by_title(title, partial_match)
    elif class_name:
        return manager.find_window_by_class(class_name, partial_match)
    elif process_name:
        return manager.find_window_by_process(process_name, partial_match)
    else:
        return None


def find_windows(title: Optional[str] = None, class_name: Optional[str] = None, process_name: Optional[str] = None, partial_match: bool = True) -> List[WindowInfo]:
    """
    快捷函数：查找所有匹配窗口

    Args:
        title: 窗口标题
        class_name: 窗口类名
        process_name: 进程名
        partial_match: 是否部分匹配

    Returns:
        窗口信息列表
    """
    manager = get_window_manager()

    if title:
        return manager.find_windows_by_title(title, partial_match)
    else:
        # 对于class_name和process_name，暂时返回空列表
        # 可以后续扩展find_windows_by_class和find_windows_by_process方法
        return []


def get_window_info(hwnd: int) -> Optional[WindowInfo]:
    """
    快捷函数：获取窗口信息

    Args:
        hwnd: 窗口句柄

    Returns:
        窗口信息
    """
    manager = get_window_manager()
    return manager.get_window_info(hwnd)