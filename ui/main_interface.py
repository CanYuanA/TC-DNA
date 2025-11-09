#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏脚本控制面板 - 主界面

提供简单的主界面，包含打开设置页面的按钮
"""

import tkinter as tk
import customtkinter as ctk

from utils.global_manager import global_manager, set_global, get_global, log_info, log_warning, log_error, log_debug, log_critical
from utils.config_manager import ConfigManager
from utils.window import find_window, get_window_info
from utils.task.task_manager import get_task_manager


class MainInterface:
    """主界面类"""

    def __init__(self):
        """初始化主界面"""
        self.root = ctk.CTk()
        self.settings_window = None

        # 状态管理
        self.initialized = False
        self.task_running = False
        self.selected_task_available = False

        # 使用全局管理器
        set_global('main_window', self.root, notify=False)
        set_global('main_interface', self, notify=False)  # 注册主界面实例
        set_global('initialized', True, notify=False)

        self.setup_window()
        self.create_interface()
        self.update_button_states()
        self._register_task_listeners()

    def _register_task_listeners(self):
        """注册任务状态监听"""
        try:
            task_manager = get_task_manager()
            if task_manager:
                # 使用正确的方法名
                task_manager.add_task_callback(self._task_callback)
                log_info("已注册任务状态监听器")
        except Exception as e:
            log_warning(f"注册任务状态监听器失败: {e}")

    def _task_callback(self, event_type: str, task_info):
        """任务状态变化回调"""
        if event_type == 'task_started':
            self.task_running = True
            self.status_label.configure(text="● 运行中", text_color='#FF9800')
            self.update_button_states()
            # 通知任务选择器更新状态显示
            self._update_task_selector_status()
            log_info(f"任务启动回调: {task_info.name}")
        elif event_type == 'task_stopped':
            self.task_running = False
            self.status_label.configure(text="● 已停止", text_color='#f44336')
            self.update_button_states()
            # 通知任务选择器更新状态显示
            self._update_task_selector_status()
            log_info(f"任务停止回调: {task_info.name}")
        elif event_type == 'task_error':
            self.task_running = False
            self.status_label.configure(text="● 错误", text_color='#f44336')
            self.update_button_states()
            # 通知任务选择器更新状态显示
            self._update_task_selector_status()
            log_error(f"任务错误回调: {task_info.name}")

    def _update_task_selector_status(self):
        """通知任务选择器更新所有任务状态显示"""
        try:
            task_selector = get_global('task_selector')
            if task_selector and hasattr(task_selector, 'refresh_task_status'):
                task_selector.refresh_task_status()
        except Exception as e:
            log_warning(f"更新任务选择器状态失败: {e}")

    def update_button_states(self):
        """更新按钮状态"""
        # 获取当前选中任务的状态
        selected_task_running = self._is_task_running()
        selected_task_ready = self._has_enabled_task_selected()

        # 初始化按钮：有任务进行时禁用
        if hasattr(self, 'init_btn'):
            if selected_task_running:
                self.init_btn.configure(state='disabled')
            else:
                self.init_btn.configure(state='normal')

        # 开始任务按钮：选中任务为READY状态且已初始化时启用
        if hasattr(self, 'start_btn'):
            can_start = (
                self.initialized and           # 已初始化
                not selected_task_running and  # 选中任务未运行
                selected_task_ready            # 选中任务为就绪状态
            )

            if can_start:
                self.start_btn.configure(state='normal')
            else:
                self.start_btn.configure(state='disabled')

        # 停止按钮：选中任务为RUNNING状态时启用
        if hasattr(self, 'stop_btn'):
            if selected_task_running:
                self.stop_btn.configure(state='normal')
            else:
                self.stop_btn.configure(state='disabled')

    def _has_enabled_task_selected(self) -> bool:
        """检查是否选择了已启用的任务"""
        try:
            task_selector = get_global('task_selector')
            if not task_selector:
                return False

            selected_task_id = task_selector.get_selected_task_id()
            if not selected_task_id:
                return False

            # 获取任务状态
            task_status = task_selector.task_manager.get_task_status(selected_task_id)
            # 任务必须是就绪状态（已启用且未运行）
            from utils.task.task_manager import TaskState
            return task_status in [TaskState.READY]
        except:
            return False

    def _is_task_running(self) -> bool:
        """检查是否有任务正在运行"""
        try:
            task_selector = get_global('task_selector')
            if not task_selector:
                return False

            selected_task_id = task_selector.get_selected_task_id()
            if not selected_task_id:
                return False

            # 获取任务状态
            task_status = task_selector.task_manager.get_task_status(selected_task_id)
            from utils.task.task_manager import TaskState
            return task_status == TaskState.RUNNING
        except:
            return False

    def update_task_selection_status(self):
        """更新任务选择状态"""
        try:
            task_selector = get_global('task_selector')
            if not task_selector:
                self.selected_task_available = False
            else:
                selected_task_id = task_selector.get_selected_task_id()
                self.selected_task_available = bool(selected_task_id)

            # 更新当前是否有任务运行的状态
            self.task_running = self._is_task_running()
        except Exception as e:
            log_warning(f"更新任务选择状态失败: {e}")
            self.selected_task_available = False
            self.task_running = False

        self.update_button_states()

    def setup_window(self):
        """设置窗口属性"""
        # 窗口标题
        self.root.title("DNAS-二重螺旋-皎皎本")

        # 窗口大小
        width = 800
        height = 1000

        # 获取屏幕尺寸并居中显示
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(f'{width}x{height}+{x}+{y}')
        self.root.minsize(350, 250)

        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_interface(self):
        """创建主界面内容"""
        # 主框架
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 上半部分：控制区域
        self.create_control_area(main_frame)

        # 中间部分：任务选择区域
        self.create_task_area(main_frame)

        # 下半部分：日志区域
        self.create_log_area(main_frame)

    def create_control_area(self, parent):
        """创建控制区域"""
        # 控制区域框架
        control_frame = ctk.CTkFrame(parent)
        control_frame.pack(fill='x', padx=10, pady=(0, 10))

        # 标题
        title_label = ctk.CTkLabel(
            control_frame,
            text="DNAS Version 0.1.0",
            font=ctk.CTkFont(family="Arial", size=18, weight="bold")
        )
        title_label.pack(pady=(10, 5))

        # 按钮区域
        button_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_frame.pack(fill='x', pady=5)

        # 第一行按钮
        first_row = ctk.CTkFrame(button_frame, fg_color="transparent")
        first_row.pack(fill='x', pady=2)

        # 初始化按钮
        self.init_btn = ctk.CTkButton(
            first_row,
            text="🔧 初始化",
            command=self.initialize_game,
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
            width=120,
            height=35
        )
        self.init_btn.pack(side='left', padx=(0, 10))

        # 设置按钮
        settings_btn = ctk.CTkButton(
            first_row,
            text="⚙️ 打开设置",
            command=self.open_settings,
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
            width=120,
            height=35
        )
        settings_btn.pack(side='left', padx=(0, 10))

        # 开始任务按钮
        self.start_btn = ctk.CTkButton(
            first_row,
            text="▶️ 开始任务",
            command=self.start_task,
            font=ctk.CTkFont(family="Arial", size=12),
            width=120,
            height=35
        )
        self.start_btn.pack(side='left', padx=(0, 10))

        # 停止游戏按钮
        self.stop_btn = ctk.CTkButton(
            first_row,
            text="⏹️ 停止",
            command=self.stop_game,
            font=ctk.CTkFont(family="Arial", size=12),
            width=120,
            height=35
        )
        self.stop_btn.pack(side='left', padx=(0, 10))

        # 状态显示
        self.status_label = ctk.CTkLabel(
            button_frame,
            text="● 就绪",
            font=ctk.CTkFont(family="Arial", size=10)
        )
        self.status_label.pack(pady=(5, 0))

    def create_task_area(self, parent):
        """创建任务选择区域"""
        # 任务区域框架
        task_frame = ctk.CTkFrame(parent)
        task_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # 任务区域标题
        task_title = ctk.CTkLabel(
            task_frame,
            text="任务选择",
            font=ctk.CTkFont(family="Arial", size=12, weight="bold")
        )
        task_title.pack(pady=(10, 5))

        # 创建任务选择器
        try:
            from utils.task import TaskSelector
            self.task_selector = TaskSelector(task_frame)
            set_global('task_selector', self.task_selector, notify=False)
            log_info("任务选择器已创建")

            # 初始更新任务选择状态
            self.update_task_selection_status()
        except Exception as e:
            log_error(f"创建任务选择器失败: {e}")
            # 如果任务选择器创建失败，显示错误信息
            error_label = ctk.CTkLabel(
                task_frame,
                text=f"任务选择器初始化失败: {e}",
                text_color='red'
            )
            error_label.pack(expand=True)

    def create_log_area(self, parent):
        """创建日志区域"""
        # 引入日志组件
        from .components.log_widget import LogWidget

        # 日志区域框架
        log_frame = ctk.CTkFrame(parent)
        log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # 日志区域标题
        log_title = ctk.CTkLabel(
            log_frame,
            text="运行日志",
            font=ctk.CTkFont(family="Arial", size=12, weight="bold")
        )
        log_title.pack(pady=(10, 5))

        # 创建日志组件
        self.log_widget = LogWidget(
            log_frame,
            max_lines=500,
            auto_scroll=True,
            show_timestamp=True,
            show_level=True
        )
        self.log_widget.pack(fill='both', expand=True, padx=5, pady=5)

        # 设置到全局管理器
        set_global('log_widget', self.log_widget)

    def initialize_game(self):
        """初始化游戏脚本"""
        try:
            log_info("开始初始化游戏...")

            # 加载配置
            config = ConfigManager()
            window_title = config.get("通用设置.捕获窗口标题", "null")
            log_info(f"正在查找游戏窗口: {window_title}")

            # 查找窗口
            window_info = find_window(title=window_title, partial_match=True)

            if window_info and window_info.is_valid():
                log_info(f"找到游戏窗口: {window_info.title} (PID: {window_info.pid})")
                log_info(f"窗口位置: ({window_info.x}, {window_info.y}) 尺寸: {window_info.width}x{window_info.height}")

                # 导入窗口管理器
                from utils.window.window_manager import get_window_manager
                window_manager = get_window_manager()

                log_info("正在配置窗口...")

                # 将窗口置于顶层并调整1920x1080客户区
                if window_manager.set_foreground_and_1920x1080(window_info.handle):
                    log_info("窗口已成功置于顶层并调整为1920x1080客户区")

                    # 重新获取窗口信息以确认设置结果
                    updated_info = window_manager.get_window_info(window_info.handle)
                    if updated_info:
                        log_info(f"更新后窗口信息: 位置({updated_info.x}, {updated_info.y}) 尺寸: {updated_info.width}x{updated_info.height}")
                else:
                    log_warning("窗口配置部分失败，但继续初始化")

                # 将窗口信息保存到全局变量
                set_global('target_window', window_info, notify=True)

                # 初始化OCR模型
                log_info("正在初始化OCR模型...")
                try:
                    from utils.image import get_image_manager
                    image_manager = get_image_manager()
                    if image_manager.ocr_recognition.initialize():
                        log_info("OCR模型初始化成功")
                    else:
                        log_warning("OCR模型初始化失败，但继续初始化其他组件")
                except Exception as ocr_e:
                    log_warning(f"OCR模型初始化失败: {ocr_e}")

                # 更新状态
                self.status_label.configure(text="● 已初始化", text_color='#4CAF50')
                set_global('initialized', True, notify=False)
                self.initialized = True

                # 记录成功信息
                log_info(f"游戏窗口初始化完成！窗口: {window_info.title}, 状态: 已置顶并调整为1920x1080客户区")

                # 更新按钮状态
                self.update_button_states()

            else:
                log_warning(f"未找到游戏窗口: {window_title}")
                log_warning(f"未找到标题包含 '{window_title}' 的窗口。请确认：1. 游戏已启动 2. 窗口标题正确 3. 窗口处于可见状态。当前设置的目标窗口标题: {window_title}")

        except Exception as e:
            log_error(f"初始化失败: {e}")
            log_error(f"初始化游戏时发生错误: {e}")

    def open_settings(self):
        """打开设置窗口"""
        settings_window_obj = get_global('settings_window')
        if settings_window_obj is None or not settings_window_obj.root.winfo_exists():
            try:
                # 导入设置窗口
                from .settings_window import SettingsWindow

                # 创建设置窗口
                self.settings_window = SettingsWindow(self.root)
                set_global('settings_window', self.settings_window)

                # 监听设置窗口关闭事件
                self.settings_window.root.protocol("WM_DELETE_WINDOW", self.on_settings_closing)
            except Exception as e:
                log_error(f"无法打开设置窗口: {e}")
        else:
            # 如果窗口已存在，则将其置前
            settings_window_obj.root.lift()
            settings_window_obj.root.focus_force()

    def start_task(self):
        """开始选中的任务"""
        try:
            # 获取任务选择器
            task_selector = get_global('task_selector')
            if not task_selector:
                log_warning("任务选择器未初始化")
                return

            # 获取选中的任务
            selected_task_id = task_selector.get_selected_task_id()
            if not selected_task_id:
                log_warning("请先选择要执行的任务")
                return

            # 记录日志
            log_info(f"开始启动任务: {selected_task_id}")

            # 启动任务
            success = task_selector.start_selected_task()

            if success:
                log_info("任务启动完成")
                # 立即更新任务选择状态
                self.update_task_selection_status()
            else:
                log_warning("任务启动失败")
                self.status_label.configure(text="● 启动失败", text_color='#f44336')

        except Exception as e:
            log_error(f"启动任务失败: {e}")
            self.status_label.configure(text="● 错误", text_color='#f44336')

    def stop_game(self):
        """停止游戏脚本"""
        try:
            # 记录日志
            log_info("正在停止游戏脚本...")

            # 获取任务选择器并停止当前运行的任务
            task_selector = get_global('task_selector')
            if task_selector:
                task_selector.stop_selected_task()

            # 状态更新由回调函数处理

        except Exception as e:
            log_error(f"停止脚本失败: {e}")

    def on_settings_closing(self):
        """设置窗口关闭事件"""
        if self.settings_window and self.settings_window.root.winfo_exists():
            self.settings_window.root.destroy()
        self.settings_window = None

    def on_closing(self):
        """主窗口关闭事件"""
        # 先关闭设置窗口
        if self.settings_window and self.settings_window.root.winfo_exists():
            self.settings_window.root.destroy()

        # 关闭主窗口
        self.root.destroy()

    def run(self):
        """运行主界面"""
        self.root.mainloop()