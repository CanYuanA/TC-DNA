#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务选择UI组件

提供任务列表显示、选择、执行功能
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Dict, List, Optional, Callable, Any
from utils.task.task_manager import get_task_manager, TaskInfo, TaskState
from utils.global_manager import log_info, log_warning, log_error


class TaskSelector:
    """任务选择器"""

    def __init__(self, parent):
        """
        初始化任务选择器

        Args:
            parent: 父容器
        """
        self.parent = parent
        self.task_manager = get_task_manager()
        self.selected_task_id = None
        self.task_widgets = {}  # 存储任务UI组件

        # 设置全局状态监听
        self.setup_global_listeners()
        self.task_callbacks = {}

        # 创建界面
        self.create_widgets()

        # 先加载任务数据
        self.task_manager.load_tasks()

        # 更新分类下拉框
        self.update_category_dropdown()

        # 加载任务
        self.load_tasks()

    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        self.frame = ctk.CTkFrame(self.parent)
        self.frame.pack(fill='both', expand=True, padx=5, pady=5)

        # 标题框架
        title_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        title_frame.pack(fill='x', pady=(0, 5))

        # 标题
        title_label = ctk.CTkLabel(
            title_frame,
            text="任务列表",
            font=ctk.CTkFont(family="Arial", size=14, weight="bold")
        )
        title_label.pack(side='left')

        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            title_frame,
            text="刷新",
            command=self.refresh_tasks,
            width=60,
            height=30
        )
        refresh_btn.pack(side='right')

        # 分类选择
        self.category_var = ctk.StringVar(value="所有分类")
        category_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        category_frame.pack(fill='x', pady=(0, 5))

        ctk.CTkLabel(category_frame, text="分类:").pack(side='left')
        self.category_combo = ctk.CTkComboBox(
            category_frame,
            values=["所有分类"],  # 先设为默认，后续会更新
            variable=self.category_var,  # 绑定StringVar
            command=self.on_category_changed,
            width=150
        )
        self.category_combo.pack(side='left', padx=(5, 0))

        # 立即更新分类下拉框
        self.update_category_dropdown()

        # 任务列表和信息显示框架
        content_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        content_frame.pack(fill='both', expand=True)

        # 左侧任务列表框架
        list_frame = ctk.CTkScrollableFrame(content_frame)
        list_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        # 存储任务列表frame供后续使用
        self.task_list_frame = list_frame

        # 右侧信息显示框架
        info_frame = ctk.CTkFrame(content_frame)
        info_frame.pack(side='right', fill='y', padx=(5, 0), ipadx=200)

        # 任务信息显示
        self.task_info_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        self.task_info_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 创建信息显示标签
        self.task_name_label = ctk.CTkLabel(
            self.task_info_frame,
            text="",
            font=ctk.CTkFont(family="Arial", size=14, weight="bold")
        )
        self.task_name_label.pack(anchor='w', pady=(0, 5))

        self.task_desc_label = ctk.CTkLabel(
            self.task_info_frame,
            text="",
            wraplength=200,
            justify='left'
        )
        self.task_desc_label.pack(anchor='w', pady=(0, 10))

        # 任务设置框架
        self.settings_frame = ctk.CTkFrame(self.task_info_frame)
        self.settings_frame.pack(fill='x', pady=(0, 10))

        settings_title = ctk.CTkLabel(
            self.settings_frame,
            text="任务设置",
            font=ctk.CTkFont(family="Arial", size=12, weight="bold")
        )
        settings_title.pack(pady=(5, 0))

        # 任务设置显示区域
        self.settings_text = ctk.CTkTextbox(self.settings_frame, height=200, state='disabled')
        self.settings_text.pack(fill='both', expand=True, padx=5, pady=5)

        # 任务状态显示
        self.status_frame = ctk.CTkFrame(self.task_info_frame, fg_color="transparent")
        self.status_frame.pack(fill='x', pady=(10, 0))

        ctk.CTkLabel(self.status_frame, text="状态:").pack(side='left')
        self.task_status_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            text_color='blue'
        )
        self.task_status_label.pack(side='left', padx=(5, 0))




    def load_tasks(self):
        """加载任务列表"""
        # 获取当前分类
        current_category = self.category_var.get()

        # 清空现有任务
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()

        self.task_widgets.clear()

        # 获取任务列表
        if current_category == "所有分类":
            tasks = self.task_manager.get_all_tasks()
        else:
            tasks = self.task_manager.get_tasks_by_category(current_category)

        # 创建任务卡片
        for task in tasks:
            self.create_task_card(task)

    def create_task_card(self, task_info: TaskInfo):
        """创建任务卡片"""
        task_id = task_info.task_id

        # 卡片框架
        card_frame = ctk.CTkFrame(self.task_list_frame, border_width=2)
        card_frame.pack(fill='x', padx=2, pady=2)

        # 点击事件
        def on_click():
            self.select_task(task_id)

        # 内容框架
        content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        content_frame.pack(fill='x', padx=10, pady=5)

        # 任务信息显示
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(fill='x')

        # 任务图标和名称
        name_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_frame.pack(fill='x')

        # 图标
        icon_label = ctk.CTkLabel(
            name_frame,
            text=task_info.icon,
            font=ctk.CTkFont(family="Arial", size=16)
        )
        icon_label.pack(side='left')

        # 任务名称
        name_label = ctk.CTkLabel(
            name_frame,
            text=task_info.name,
            font=ctk.CTkFont(family="Arial", size=12, weight="bold")
        )
        name_label.pack(side='left', padx=(5, 0))

        # 状态标签
        status_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        status_frame.pack(fill='x', pady=(5, 0))

        # 状态标签
        status_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=ctk.CTkFont(family="Arial", size=9)
        )
        status_label.pack(side='left')

        # 分类标签
        category_label = ctk.CTkLabel(
            status_frame,
            text=f"分类: {task_info.category}",
            font=ctk.CTkFont(family="Arial", size=9),
            text_color='#bbbbbb'  # 暗黑主题下的浅灰色
        )
        category_label.pack(side='right')

        # 将点击事件绑定到所有组件
        for widget in [card_frame, content_frame, info_frame, name_frame,
                      icon_label, name_label, status_frame, status_label, category_label]:
            widget.bind("<Button-1>", lambda e: on_click())

        # 存储组件引用
        self.task_widgets[task_id] = {
            'card': card_frame,
            'name_label': name_label,
            'status_label': status_label,
            'info': task_info
        }

        # 绑定悬停事件
        card_frame.bind("<Enter>", lambda e: self.on_task_hover(task_id, True))
        card_frame.bind("<Leave>", lambda e: self.on_task_hover(task_id, False))

        # 更新状态显示
        self.update_task_status(task_id)

    def setup_global_listeners(self):
        """设置全局状态监听"""
        try:
            from utils.global_manager import global_manager
            # 监听任务状态变化
            global_manager.add_listener('task.*.status', self.on_global_task_status_change)
            log_info("已设置任务状态全局监听")
        except Exception as e:
            log_warning(f"设置全局监听失败: {e}")

    def on_global_task_status_change(self, key, value):
        """全局任务状态变化回调"""
        # 从key中提取任务ID
        if key.startswith('task.') and key.endswith('.status'):
            task_id = key[5:-7]  # 去掉 "task." 和 ".status"
            if task_id in self.task_widgets:
                # 更新状态显示
                self.update_task_status(task_id)

    def on_task_hover(self, task_id: str, entering: bool):
        """任务卡片悬停事件"""
        if task_id in self.task_widgets:
            card = self.task_widgets[task_id]['card']
            if entering:
                # 如果不是当前选中的任务，才应用悬停效果
                if task_id != self.selected_task_id:
                    card.configure(fg_color='#404040')  # 暗黑主题悬停效果
            else:
                # 如果不是当前选中的任务，重新应用正确的状态颜色
                if task_id != self.selected_task_id:
                    self.update_task_status(task_id)


    def select_task(self, task_id: str):
        """选择任务"""
        if task_id == self.selected_task_id:
            return

        # 清除之前的选择
        prev_task_id = self.selected_task_id

        # 设置当前选择
        self.selected_task_id = task_id
        if prev_task_id and prev_task_id in self.task_widgets:
            # 恢复之前任务的状态显示
            self.update_task_status(prev_task_id)

        # 高亮选择的任务
        if task_id in self.task_widgets:
            # 显示任务信息
            self.show_task_info(task_id)

        # 更新新选择任务的状态显示
        self.update_task_status(task_id)

        # 通知主界面更新按钮状态
        try:
            from utils.global_manager import get_global
            main_interface = get_global('main_interface')
            if main_interface and hasattr(main_interface, 'update_task_selection_status'):
                main_interface.update_task_selection_status()
        except:
            pass  # 静默失败，不影响主要功能

    def show_task_info(self, task_id: str):
        """显示任务信息"""
        if task_id not in self.task_widgets:
            return

        task_info = self.task_widgets[task_id]['info']

        # 更新任务名称
        self.task_name_label.configure(text=f"{task_info.icon} {task_info.name}")

        # 更新任务描述
        self.task_desc_label.configure(text=task_info.description)

        # 更新任务设置
        self.update_task_settings_display(task_info)

        # 更新任务状态
        self.update_task_status_display(task_id)

    def update_task_settings_display(self, task_info):
        """更新任务设置显示"""
        settings = task_info.get_settings()

        self.settings_text.configure(state='normal')
        self.settings_text.delete('1.0', tk.END)

        if settings:
            # 如果有设置，显示设置内容
            for key, value in settings.items():
                line = f"• {key}: {value}\n"
                self.settings_text.insert(tk.END, line)
        else:
            # 如果没有设置，显示提示信息
            self.settings_text.insert(tk.END, "该任务无需特殊设置\n(通过设置窗口配置)")

        self.settings_text.configure(state='disabled')

    def update_task_status_display(self, task_id: str):
        """更新任务状态显示"""
        status = self.task_manager.get_task_status(task_id)

        status_map = {
            TaskState.DISABLED: ("已禁用", "gray"),
            TaskState.READY: ("就绪", "green"),
            TaskState.RUNNING: ("运行中", "blue"),
            TaskState.ERROR: ("错误", "red")
        }

        status_text, status_color = status_map.get(status, ("未知", "black"))
        self.task_status_label.configure(text=status_text, text_color=status_color)

    def update_task_status(self, task_id: str):
        """更新任务状态显示"""
        if task_id not in self.task_widgets:
            return

        task_info = self.task_widgets[task_id]['info']
        status_label = self.task_widgets[task_id]['status_label']
        card_frame = self.task_widgets[task_id]['card']
        status = self.task_manager.get_task_status(task_id)

        # 根据状态设置文本和颜色（支持暗黑主题）
        if status == TaskState.DISABLED:
            status_text = "● 已禁用"
            status_color = "#999999"  # 暗灰色
        elif status == TaskState.READY:
            status_text = "● 就绪"
            status_color = "#4CAF50"  # 绿色
        elif status == TaskState.RUNNING:
            status_text = "● 执行中"
            status_color = "#2196F3"  # 蓝色
        elif status == TaskState.ERROR:
            status_text = "● 错误"
            status_color = "#F44336"  # 红色
        else:
            status_text = "● 未知"
            status_color = "#999999"  # 暗灰色

        # 设置状态标签
        status_label.configure(text=status_text, text_color=status_color)

        # 设置卡片颜色（暗黑主题）
        is_selected = (task_id == self.selected_task_id)

        if status == TaskState.DISABLED:
            # 不可用：深灰色
            card_color = '#2d2d2d'
            border_color = '#555555'
        elif status == TaskState.RUNNING and is_selected:
            # 进行中选中：深蓝色
            card_color = '#1976d2'
            border_color = '#1565c0'
        elif status == TaskState.RUNNING and not is_selected:
            # 进行中未选中：中等蓝色
            card_color = '#3f51b5'
            border_color = '#2196f3'
        elif status == TaskState.READY and is_selected:
            # 就绪选中：深绿色
            card_color = '#2e7d32'
            border_color = '#4caf50'
        elif status == TaskState.READY and not is_selected:
            # 就绪未选中：深灰色
            card_color = '#383838'
            border_color = '#4caf50'
        elif status == TaskState.ERROR and is_selected:
            # 错误选中：深红色
            card_color = '#c62828'
            border_color = '#f44336'
        elif status == TaskState.ERROR and not is_selected:
            # 错误未选中：深灰色
            card_color = '#383838'
            border_color = '#f44336'
        else:
            # 其他状态：深灰色
            card_color = '#383838'
            border_color = '#666666'

        # 应用颜色
        card_frame.configure(fg_color=card_color, border_width=2)

        # 通知主界面更新按钮状态
        if is_selected:
            try:
                from utils.global_manager import get_global
                main_interface = get_global('main_interface')
                if main_interface and hasattr(main_interface, 'update_task_selection_status'):
                    main_interface.update_task_selection_status()
            except:
                pass

    def refresh_task_status(self):
        """刷新所有任务状态"""
        for task_id in self.task_widgets.keys():
            self.update_task_status(task_id)

    def get_selected_task_id(self) -> Optional[str]:
        """获取当前选中的任务ID"""
        return self.selected_task_id

    def update_category_dropdown(self):
        """更新分类下拉框"""
        # 重新加载任务数据
        self.task_manager.load_tasks()

        all_tasks = self.task_manager.get_all_tasks()
        categories = self.task_manager.get_task_categories()

        # 确保有"所有分类"选项
        all_categories = ["所有分类"] + categories

        # 使用 configure 方法正确设置值
        self.category_combo.configure(values=all_categories)

        # 如果没有设置当前值，设置默认值
        if not self.category_var.get() or self.category_var.get() not in all_categories:
            self.category_var.set("所有分类")

    def on_category_changed(self, value):
        """分类选择改变事件"""
        self.load_tasks()

    def refresh_tasks(self):
        """刷新任务列表"""
        self.task_manager.load_tasks()
        self.load_tasks()
        log_info("任务列表已刷新")

    def start_selected_task(self):
        """开始选中的任务"""
        if not self.selected_task_id:
            return False

        task_info = self.task_manager.get_task(self.selected_task_id)
        if not task_info:
            return False

        if not task_info.is_available():
            log_error(f"任务 '{task_info.name}' 不可用，请检查脚本文件是否存在")
            return False

        # 启动任务
        success = self.task_manager.start_task(self.selected_task_id)

        if success:
            log_info(f"任务 '{task_info.name}' 已启动")
        else:
            log_error(f"任务 '{task_info.name}' 启动失败")

        return success

    def stop_selected_task(self):
        """停止选中的任务"""
        if not self.selected_task_id:
            return

        task_info = self.task_manager.get_task(self.selected_task_id)
        if not task_info:
            return

        # 停止任务
        self.task_manager.stop_task(self.selected_task_id)
        log_info(f"任务 '{task_info.name}' 已停止")

    def edit_task_settings(self):
        """编辑任务设置"""
        log_info("任务设置功能待实现")


