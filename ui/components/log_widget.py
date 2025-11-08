#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志显示组件

提供日志显示、过滤、管理功能
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import logging
import sys
import time
import threading
from datetime import datetime
from typing import List, Optional, Callable
from enum import Enum
import queue

import customtkinter as ctk

from utils.global_manager import log_error


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogWidget(ctk.CTkFrame):
    """日志显示组件"""

    def __init__(self, parent=None, **kwargs):
        """
        初始化日志组件

        Args:
            parent: 父组件
            **kwargs: 额外参数，包括max_lines, auto_scroll, show_timestamp, show_level
        """
        # 从kwargs中提取LogWidget特有的参数
        self.max_lines = kwargs.pop('max_lines', 1000)
        self.auto_scroll = kwargs.pop('auto_scroll', True)
        self.show_timestamp = kwargs.pop('show_timestamp', True)
        self.show_level = kwargs.pop('show_level', True)

        # 调用父类构造函数
        super().__init__(parent, **kwargs)

        # 日志队列和缓冲区
        self.log_queue = queue.Queue()
        self.log_buffer = []  # 存储字典格式的日志条目
        self.is_processing = False
        self._buffer_lock = threading.Lock()  # 缓冲区锁

        # 日志级别过滤器
        self.level_filter = {
            LogLevel.DEBUG: True,
            LogLevel.INFO: True,
            LogLevel.WARNING: True,
            LogLevel.ERROR: True,
            LogLevel.CRITICAL: True
        }

        # 回调函数
        self.log_callbacks = []

        # 创建界面
        self.create_widgets()

        # 启动日志处理线程
        self.start_log_processor()

        # 添加默认处理器
        self.setup_default_logger()

    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill='both', expand=True)

        # 工具栏框架
        toolbar_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        toolbar_frame.pack(fill='x', padx=5, pady=(5, 0))

        # 级别过滤器
        ctk.CTkLabel(toolbar_frame, text="级别:").pack(side='left')

        self.level_vars = {}
        for level in LogLevel:
            var = ctk.BooleanVar(value=True)
            self.level_vars[level] = var

            cb = ctk.CTkCheckBox(
                toolbar_frame,
                text=level.value,
                variable=var,
                command=self._on_level_filter_changed
            )
            cb.pack(side='left', padx=(5, 10))

        # 控制按钮
        separator = ctk.CTkFrame(toolbar_frame, width=2, height=20)
        separator.pack(side='left', fill='y', padx=10)

        # 清空按钮
        clear_btn = ctk.CTkButton(
            toolbar_frame,
            text="清空",
            command=self.clear_log,
            width=60,
            height=25
        )
        clear_btn.pack(side='right', padx=(5, 0))

        # 暂停/继续按钮
        self.pause_btn = ctk.CTkButton(
            toolbar_frame,
            text="暂停",
            command=self.toggle_pause,
            width=60,
            height=25
        )
        self.pause_btn.pack(side='right', padx=(5, 0))

        # 保存按钮
        save_btn = ctk.CTkButton(
            toolbar_frame,
            text="保存",
            command=self.save_log,
            width=60,
            height=25
        )
        save_btn.pack(side='right', padx=(5, 0))

        # 日志显示区域
        log_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        log_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # 创建文本框（使用CustomTkinter的CTkTextbox）
        self.text_widget = ctk.CTkTextbox(
            log_frame,
            height=300,
            state='disabled',
            font=ctk.CTkFont(family="Consolas", size=9)
        )
        self.text_widget.pack(fill='both', expand=True)

        # 状态栏
        status_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        status_frame.pack(fill='x', padx=5, pady=(0, 5))

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="就绪"
        )
        self.status_label.pack(side='left')

        # 行数显示
        self.lines_label = ctk.CTkLabel(
            status_frame,
            text="0 行"
        )
        self.lines_label.pack(side='right')

    def setup_default_logger(self):
        """设置默认日志处理器"""
        # 创建自定义日志处理器
        class GuiLogHandler(logging.Handler):
            def __init__(self, log_widget):
                super().__init__()
                self.log_widget = log_widget

            def emit(self, record):
                try:
                    # 格式化日志消息
                    msg = self.format(record)
                    self.log_widget.add_log(record.levelname, msg)
                except Exception:
                    pass

        # 获取或创建日志记录器
        logger = logging.getLogger('GameScript')
        if not logger.handlers:
            logger.setLevel(logging.DEBUG)

            # 添加GUI处理器
            gui_handler = GuiLogHandler(self)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            gui_handler.setFormatter(formatter)
            logger.addHandler(gui_handler)

            # 添加控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

    def start_log_processor(self):
        """启动日志处理线程"""
        def process_logs():
            while True:
                try:
                    # 从队列获取日志消息
                    level, message = self.log_queue.get(timeout=0.1)
                    if level is None:  # 退出信号
                        break

                    # 添加时间戳
                    timestamp = datetime.now()
                    log_entry = {
                        'timestamp': timestamp,
                        'level': level,
                        'message': message
                    }

                    # 线程安全地添加到缓冲区
                    with self._buffer_lock:
                        self.log_buffer.append(log_entry)

                        # 限制缓冲区大小
                        if len(self.log_buffer) > self.max_lines:
                            self.log_buffer.pop(0)

                    # 立即更新显示（确保顺序）
                    self._display_log(log_entry)

                except queue.Empty:
                    continue
                except Exception as e:
                    # 确保打印错误不会影响日志系统
                    try:
                        print(f"日志处理错误: {e}")
                    except:
                        pass

        # 启动处理线程
        self.log_thread = threading.Thread(target=process_logs, daemon=True)
        self.log_thread.start()

    def add_log(self, level: str, message: str):
        """
        添加日志消息

        Args:
            level: 日志级别
            message: 日志消息
        """
        try:
            # 获取日志级别枚举
            log_level = LogLevel(level.upper())

            # 检查过滤器
            if not self.level_filter[log_level]:
                return

            # 添加到队列
            self.log_queue.put((log_level, message))

        except ValueError:
            # 无效级别，作为INFO处理
            self.log_queue.put((LogLevel.INFO, message))

    def _display_log(self, log_entry):
        """显示日志消息（必须在主线程调用）"""
        try:
            # 启用文本框
            self.text_widget.configure(state='normal')

            # 准备显示内容
            display_text = ""

            # 添加时间戳
            if self.show_timestamp:
                timestamp = log_entry['timestamp'].strftime("%H:%M:%S")
                display_text += f"[{timestamp}] "

            # 添加级别
            if self.show_level:
                display_text += f"{log_entry['level'].value}: "

            # 添加消息
            display_text += log_entry['message']

            # 插入文本
            self.text_widget.insert(tk.END, display_text + "\n", log_entry['level'].value)

            # 自动滚动
            if self.auto_scroll:
                self.text_widget.see(tk.END)

            # 限制行数
            try:
                lines = int(self.text_widget.index('end-1c').split('.')[0])
                if lines > self.max_lines:
                    # 删除前面的行
                    delete_count = min(10, lines - self.max_lines)
                    for _ in range(delete_count):
                        self.text_widget.delete('1.0', '2.0')
            except Exception:
                # 如果行数计算出错，清空整个文本框
                self.text_widget.delete('1.0', tk.END)

            # 禁用文本框
            self.text_widget.configure(state='disabled')

            # 更新状态
            self._update_status()

        except Exception as e:
            # 防止UI更新错误影响程序
            try:
                print(f"显示日志错误: {e}")
            except:
                pass

    def _update_status(self):
        """更新状态信息"""
        try:
            # 获取当前行数
            lines = int(self.text_widget.index('end-1c').split('.')[0])
            self.lines_label.configure(text=f"{lines} 行")

            # 检查是否在处理中
            if not self.is_processing:
                self.status_label.configure(text="就绪")

        except Exception as e:
            print(f"更新状态错误: {e}")

    def _on_level_filter_changed(self):
        """级别过滤器改变事件"""
        # 更新过滤器
        for level, var in self.level_vars.items():
            self.level_filter[level] = var.get()

        # 重新显示所有日志
        self._redisplay_all_logs()

    def _redisplay_all_logs(self):
        """重新显示所有日志"""
        # 清空显示
        self.text_widget.configure(state='normal')
        self.text_widget.delete('1.0', tk.END)

        # 重新显示缓冲区中的日志
        with self._buffer_lock:
            for log_entry in self.log_buffer:
                if self.level_filter.get(log_entry['level'], True):
                    display_text = ""
                    if self.show_timestamp:
                        timestamp = log_entry['timestamp'].strftime('%H:%M:%S')
                        display_text += f"[{timestamp}] "
                    if self.show_level:
                        display_text += f"{log_entry['level'].value}: "
                    display_text += log_entry['message']

                    self.text_widget.insert(tk.END, display_text + "\n", log_entry['level'].value)

        self.text_widget.configure(state='disabled')
        self._update_status()

    def clear_log(self):
        """清空日志"""
        self.text_widget.configure(state='normal')
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.configure(state='disabled')

        # 线程安全地清空缓冲区
        with threading.Lock():
            self.log_buffer.clear()

        self._update_status()

    def toggle_pause(self):
        """切换暂停/继续状态"""
        if self.is_processing:
            self.is_processing = False
            self.pause_btn.configure(text="继续")
            self.status_label.configure(text="已暂停")
        else:
            self.is_processing = True
            self.pause_btn.configure(text="暂停")
            self.status_label.configure(text="运行中")

    def save_log(self):
        """保存日志到文件"""
        from tkinter import filedialog
        import os

        filename = filedialog.asksaveasfilename(
            title="保存日志",
            defaultextension=".txt",
            filetypes=[
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    # 写入头信息
                    f.write(f"游戏脚本日志\n")
                    f.write(f"保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")

                    # 写入日志内容
                    content = self.text_widget.get('1.0', tk.END)
                    f.write(content)

                self.status_label.configure(text=f"已保存到: {os.path.basename(filename)}")

            except Exception as e:
                log_error(f"保存日志失败: {e}")

    def add_log_callback(self, callback: Callable[[str, str], None]):
        """
        添加日志回调函数

        Args:
            callback: 回调函数，参数为 (level, message)
        """
        self.log_callbacks.append(callback)

    def remove_log_callback(self, callback: Callable[[str, str], None]):
        """移除日志回调函数"""
        if callback in self.log_callbacks:
            self.log_callbacks.remove(callback)

    def get_log_content(self) -> str:
        """
        获取日志内容

        Returns:
            日志文本内容
        """
        return self.text_widget.get('1.0', tk.END)

    def set_max_lines(self, max_lines: int):
        """
        设置最大行数

        Args:
            max_lines: 最大行数
        """
        self.max_lines = max_lines

    def set_auto_scroll(self, auto_scroll: bool):
        """
        设置自动滚动

        Args:
            auto_scroll: 是否自动滚动
        """
        self.auto_scroll = auto_scroll

    def __del__(self):
        """析构函数"""
        try:
            # 发送退出信号
            self.log_queue.put((None, None))
            if hasattr(self, 'log_thread'):
                self.log_thread.join(timeout=1)
        except:
            pass


# 日志记录器实例
logger = logging.getLogger('GameScript.LogWidget')