#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏脚本控制面板 - 设置窗口

提供详细的参数设置界面，基于JSON配置文件
"""

import tkinter as tk
from tkinter import ttk
import os
import json
import customtkinter as ctk
from typing import Dict, Any

from utils.config_manager import ConfigManager
from .components.ui_elements import UIElementFactory
from utils.global_manager import global_manager, set_global, get_global, log_info, log_warning, log_error


class SettingsWindow:
    """设置窗口类"""

    def __init__(self, parent=None):
        """初始化设置窗口"""
        self.parent = parent
        self.root = ctk.CTkToplevel(parent) if parent else ctk.CTk()
        self.config_manager = ConfigManager()
        self.ui_config = {}
        self.tabs = {}
        self.tab_elements = {}  # 存储每个选项卡的元素引用

        self.load_ui_config()
        self.setup_window()
        self.create_interface()
        self.load_saved_settings()

    def load_ui_config(self):
        """加载UI配置文件"""
        try:
            self.ui_config = self.config_manager.get_ui_config()
            log_info(f"成功加载UI配置，选项卡数量: {len(self.ui_config.get('tabs', {}))}")
            for tab_key in self.ui_config.get('tabs', {}):
                tab_config = self.ui_config['tabs'][tab_key]
                elements_count = len(tab_config.get('elements', []))
                log_info(f"选项卡 '{tab_key}' 包含 {elements_count} 个元素")
        except Exception as e:
            log_error(f"加载UI配置失败: {e}")
            self.ui_config = {}

    def setup_window(self):
        """设置窗口属性"""
        # 窗口标题
        title = self.ui_config.get('app_title', '游戏脚本设置')
        self.root.title(title)

        # 窗口大小
        window_size = self.ui_config.get('window_size', {'width': 800, 'height': 600})
        width = window_size.get('width', 800)
        height = window_size.get('height', 600)

        # 获取屏幕尺寸并居中显示
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(f'{width}x{height}+{x}+{y}')
        self.root.minsize(600, 400)

        # 设置为模态窗口（如果有关闭窗口）
        if self.parent:
            self.root.transient(self.parent)
            self.root.grab_set()  # 捕获输入焦点，阻塞父窗口操作

        # 隐藏系统标题栏
        self.root.overrideredirect(True)

        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 添加自定义标题栏
        self.create_custom_title_bar()

    def create_custom_title_bar(self):
        """创建自定义标题栏"""
        # 创建主容器
        self.container = ctk.CTkFrame(self.root)
        self.container.pack(fill='both', expand=True, padx=2, pady=2)

        # 创建自定义标题栏
        self.title_bar = ctk.CTkFrame(self.container, height=35, fg_color="#2b2b2b")
        self.title_bar.pack(fill='x', padx=0, pady=(0, 0))
        self.title_bar.pack_propagate(False)  # 防止高度变化

        # 标题
        title_label = ctk.CTkLabel(
            self.title_bar,
            text="游戏脚本设置",
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
            text_color="white"
        )
        title_label.pack(side='left', padx=(10, 0), pady=7)

        # 关闭按钮
        close_btn = ctk.CTkButton(
            self.title_bar,
            text="×",
            command=self.on_closing,
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
            width=35,
            height=25,
            fg_color="red",
            hover_color="darkred",
            text_color="white",
            corner_radius=0
        )
        close_btn.pack(side='right', padx=(0, 0), pady=5)

        # 绑定拖拽事件
        self.title_bar.bind("<Button-1>", self.start_drag)
        self.title_bar.bind("<B1-Motion>", self.on_drag)

        # 存储拖拽起始位置
        self.drag_start_x = 0
        self.drag_start_y = 0

    def start_drag(self, event):
        """开始拖拽"""
        self.drag_start_x = event.x_root - self.root.winfo_x()
        self.drag_start_y = event.y_root - self.root.winfo_y()

    def on_drag(self, event):
        """拖拽中"""
        x = event.x_root - self.drag_start_x
        y = event.y_root - self.drag_start_y
        self.root.geometry(f"+{x}+{y}")

    def create_interface(self):
        """创建设置界面"""
        # 在container中创建内容区域
        content_frame = ctk.CTkFrame(self.container)
        content_frame.pack(fill='both', expand=True, padx=0, pady=(0, 0))

        # 创建选项卡控件
        self.notebook = ctk.CTkTabview(content_frame)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=(10, 10))

        # 获取选项卡配置
        tabs_config = self.ui_config.get('tabs', {})

        # 先创建所有选项卡结构，不设置当前tab
        for tab_key, tab_config in tabs_config.items():
            self._create_tab_structure(tab_key, tab_config)

        # 然后为所有选项卡创建内容
        for tab_key, tab_config in tabs_config.items():
            self._create_tab_content_for_existing_tab(tab_key, tab_config)

        # 最后设置默认选项卡为第一个选项卡
        if tabs_config:
            first_tab_key = list(tabs_config.keys())[0]
            first_tab_name = tabs_config[first_tab_key].get('name', first_tab_key)
            self.notebook.set(first_tab_name)
            log_info(f"设置默认选项卡: {first_tab_name}")

        # 创建底部按钮框架
        self.create_bottom_controls(content_frame)

    def _create_tab_structure(self, tab_key: str, tab_config: Dict[str, Any]):
        """创建选项卡结构（不含内容）"""
        try:
            # 创建选项卡
            tab_name = tab_config.get('name', tab_key)

            # 使用tab_key作为tab的标识符添加到notebook
            # CTkTabview.add(tab_name) 直接使用tab名称
            self.notebook.add(tab_name)

            # 获取当前tab的frame
            tab_frame = self.notebook.tab(tab_name)

            # 存储选项卡引用
            self.tabs[tab_key] = tab_frame

        except Exception as e:
            log_error(f"创建选项卡 {tab_key} 失败: {e}")
            import traceback
            log_error(f"错误详情: {traceback.format_exc()}")

            # 创建一个错误显示
            try:
                # 添加一个错误tab
                self.notebook.add(f"错误_{tab_key}")
                error_frame = ctk.CTkFrame(self.notebook)
                error_label = ctk.CTkLabel(
                    error_frame,
                    text=f"选项卡创建失败: {tab_key}\n错误: {str(e)[:50]}",
                    text_color='red',
                    font=ctk.CTkFont(family="Arial", size=12)
                )
                error_label.pack(expand=True, padx=10, pady=10)
                self.tabs[tab_key] = error_frame
            except Exception as e2:
                log_error(f"创建错误tab也失败: {e2}")
                self.tabs[tab_key] = None

    def _create_tab_content_for_existing_tab(self, tab_key: str, tab_config: Dict[str, Any]):
        """为已存在的选项卡创建内容"""
        try:
            # 获取已存在的选项卡frame
            if tab_key in self.tabs:
                tab_frame = self.tabs[tab_key]
                # 创建选项卡内容
                self.create_tab_content(tab_frame, tab_key, tab_config)
            else:
                log_error(f"选项卡 {tab_key} 不存在，无法创建内容")

        except Exception as e:
            log_error(f"创建选项卡 {tab_key} 内容失败: {e}")
            import traceback
            log_error(f"错误详情: {traceback.format_exc()}")

            # 创建一个错误信息显示
            try:
                if tab_key in self.tabs:
                    error_label = ctk.CTkLabel(
                        self.tabs[tab_key],
                        text=f"选项卡内容创建失败: {e}",
                        text_color='red',
                        font=ctk.CTkFont(family="Arial", size=12)
                    )
                    error_label.pack(expand=True)
            except Exception as e2:
                log_error(f"创建错误信息也失败: {e2}")

    def create_tab(self, tab_key: str, tab_config: Dict[str, Any]):
        """创建选项卡（兼容性方法，不再使用）"""
        pass  # 该方法已废弃，使用上面的新方法

    def create_tab_content(self, parent, tab_key: str, tab_config: Dict[str, Any]):
        """创建选项卡内容"""
        try:
            elements = tab_config.get('elements', [])
            self.tab_elements[tab_key] = []  # 初始化元素列表

            for i, element_config in enumerate(elements):
                element = self.create_element(parent, element_config, tab_key)
                if element:
                    self.tab_elements[tab_key].append(element)
                else:
                    log_error(f"选项卡 {tab_key} 元素 {i+1} 创建失败")

        except Exception as e:
            log_error(f"创建选项卡 {tab_key} 内容失败: {e}")
            # 创建一个错误信息显示
            error_label = ctk.CTkLabel(
                parent,
                text=f"选项卡内容创建失败: {e}",
                text_color='red',
                font=ctk.CTkFont(family="Arial", size=12)
            )
            error_label.pack(expand=True)

    def create_element(self, parent, element_config: Dict[str, Any], tab_key: str) -> Any:
        """
        创建UI元素

        Args:
            parent: 父容器
            element_config: 元素配置
            tab_key: 选项卡键名

        Returns:
            UI元素实例
        """
        element_type = element_config.get('type', 'label')

        # 添加tab_key到配置中，用于保存时构造键名
        element_config_copy = element_config.copy()
        if 'var_name' in element_config:
            element_config_copy['var_name'] = f"{tab_key}.{element_config['var_name']}"

        try:
            element = UIElementFactory.create_element(
                element_type, parent, element_config_copy, self.config_manager
            )
            return element
        except Exception as e:
            print(f"创建UI元素失败 ({element_type}): {e}")
            log_error(f"创建UI元素失败 ({element_type}): {e}")
            # 创建一个错误标签作为占位符
            error_label = ctk.CTkLabel(
                parent,
                text=f"元素创建失败: {element_type}",
                text_color='red'
            )
            error_label.pack(anchor='w', pady=5)
            return error_label

    def create_bottom_controls(self, parent):
        """创建底部控制按钮"""
        bottom_frame = ctk.CTkFrame(parent, fg_color="transparent")
        bottom_frame.pack(fill='x', pady=(10, 0))

        # 左侧按钮
        left_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        left_frame.pack(side='left')

        ctk.CTkButton(
            left_frame,
            text="保存设置",
            command=self.save_settings,
            width=100,
            height=35
        ).pack(side='left', padx=(0, 10))

        ctk.CTkButton(
            left_frame,
            text="加载设置",
            command=self.load_settings,
            width=100,
            height=35
        ).pack(side='left', padx=(0, 10))

        ctk.CTkButton(
            left_frame,
            text="重置",
            command=self.reset_all_settings,
            width=100,
            height=35
        ).pack(side='left', padx=(0, 10))

        # 右侧按钮
        right_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        right_frame.pack(side='right')

        ctk.CTkButton(
            right_frame,
            text="关闭",
            command=self.on_closing,
            width=100,
            height=35
        ).pack(side='right')

    def save_settings(self):
        """保存设置"""
        try:
            # 保存所有选项卡的元素值
            for tab_key, elements in self.tab_elements.items():
                for element in elements:
                    if hasattr(element, 'config') and 'var_name' in element.config:
                        var_name = element.config['var_name']
                        element.save_to_config(var_name)

            # 保存到文件
            if self.config_manager.save_config():
                log_info("设置已保存")
            else:
                log_error("保存设置失败")
        except Exception as e:
            log_error(f"保存设置时发生错误: {e}")

    def load_saved_settings(self):
        """加载已保存的设置（启动时调用）"""
        # 这里可以添加启动时需要执行的逻辑
        pass

    def load_settings(self):
        """重新加载设置"""
        self.config_manager.load_config()
        log_info("设置已重新加载")

    def reset_all_settings(self):
        """重置所有设置"""
        try:
            log_warning("开始重置所有设置")
            # 删除配置文件
            if os.path.exists(self.config_manager.config_path):
                os.remove(self.config_manager.config_path)
                log_info("已删除配置文件")

            # 重新创建默认配置
            self.config_manager.create_default_config()
            log_info("已重新创建默认配置")

            # 重新加载界面
            self.load_settings()

            log_info("所有设置已重置")
        except Exception as e:
            log_error(f"重置设置时发生错误: {e}")

    def on_closing(self):
        """窗口关闭事件"""
        # 释放模态状态
        if self.parent:
            self.root.grab_release()
        self.root.destroy()

    def run(self):
        """运行设置窗口"""
        if not self.parent:  # 如果是独立运行
            self.root.mainloop()