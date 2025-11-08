#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CustomTkinter兼容性模块

提供tkinter到CustomTkinter的兼容性映射，减少代码改动
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

# 主题设置
ctk.set_appearance_mode("dark")  # 可选: "light", "dark", "system"
ctk.set_default_color_theme("blue")  # 可选: "blue", "green", "dark-blue"

class CompatibilityWrapper:
    """CustomTkinter兼容性包装器"""

    @staticmethod
    def get_widget_class(tkinter_class_name: str):
        """获取对应的CustomTkinter组件类"""
        mapping = {
            'Frame': ctk.CTkFrame,
            'Label': ctk.CTkLabel,
            'Button': ctk.CTkButton,
            'Entry': ctk.CTkEntry,
            'Text': ctk.CTkTextbox,
            'Checkbutton': ctk.CTkCheckBox,
            'Radiobutton': ctk.CTkRadioButton,
            'Scale': ctk.CTkSlider,
            'Scrollbar': ctk.CTkScrollbar,
            'Listbox': ctk.CTkScrollableFrame,  # CustomTkinter没有原生Listbox，用可滚动框架替代
            'Notebook': ctk.CTkTabview,
            'Progressbar': ctk.CTkProgressBar,
            'Spinbox': ctk.CTkEntry,  # 近似替代
            'Canvas': ctk.CTkCanvas,  # CustomTkinter提供Canvas
        }
        return mapping.get(tkinter_class_name, getattr(ctk, f"CTk{tkinter_class_name}", ctk.CTkFrame))

    @staticmethod
    def convert_color(color_str: str, default_color: str = None) -> str:
        """转换颜色格式"""
        if not color_str:
            return default_color

        # 处理常见的颜色名称
        color_mapping = {
            'white': '#ffffff',
            'black': '#000000',
            'red': '#ff0000',
            'green': '#00ff00',
            'blue': '#0000ff',
            'lightgray': '#d3d3d3',
            'lightgrey': '#d3d3d3',
            'gray': '#808080',
            'grey': '#808080',
            'darkgray': '#a9a9a9',
            'darkgrey': '#a9a9a9',
        }

        color_lower = color_str.lower()
        if color_lower in color_mapping:
            return color_mapping[color_lower]

        # 如果已经是十六进制格式，直接返回
        if color_str.startswith('#') and len(color_str) in [4, 7, 9]:
            return color_str

        return color_str

    @staticmethod
    def create_widget(widget_class, parent, **kwargs):
        """创建组件的兼容性方法"""
        # 处理颜色参数
        if 'bg' in kwargs:
            kwargs['bg_color'] = CompatibilityWrapper.convert_color(kwargs.pop('bg'))
        if 'fg' in kwargs:
            fg_color = kwargs.pop('fg')
            kwargs['text_color'] = CompatibilityWrapper.convert_color(fg_color)

        # 处理字体
        if 'font' in kwargs:
            font = kwargs['font']
            if isinstance(font, tuple) and len(font) >= 2:
                font_family, font_size = font[0], font[1]
                font_weight = font[2] if len(font) > 2 else 'normal'
                kwargs['font'] = (font_family, font_size)
                if font_weight == 'bold':
                    kwargs['font'] = ctk.CTkFont(family=font_family, size=font_size, weight='bold')

        # 处理relief参数
        if 'relief' in kwargs:
            relief = kwargs.pop('relief')
            if relief == 'flat':
                kwargs['border_width'] = 0
            elif relief in ['raised', 'sunken', 'ridge', 'groove']:
                kwargs['border_width'] = 2

        # 处理cursor
        if 'cursor' in kwargs:
            cursor = kwargs.pop('cursor')
            if cursor == 'hand2':
                kwargs['cursor'] = 'hand'

        return widget_class(parent, **kwargs)

# 兼容性导入
class Tk:
    """兼容性Tk类"""
    def __init__(self):
        self.root = ctk.CTk()
        self._setup_methods()

    def _setup_methods(self):
        """设置方法映射"""
        self.title = self.root.title
        self.geometry = self.root.geometry
        self.minsize = self.root.minsize
        self.protocol = self.root.protocol
        self.mainloop = self.root.mainloop
        self.winfo_screenwidth = self.root.winfo_screenwidth
        self.winfo_screenheight = self.root.winfo_screenheight
        self.destroy = self.root.destroy
        self.winfo_exists = lambda: self.root.winfo_exists()

    def __getattr__(self, name):
        return getattr(self.root, name)

# 兼容性函数
def Toplevel(parent=None, **kwargs):
    """兼容性Toplevel函数"""
    if parent is None:
        return ctk.CTkToplevel()
    else:
        return ctk.CTkToplevel(parent)

def StringVar():
    """兼容性StringVar函数"""
    return ctk.StringVar()

def IntVar():
    """兼容性IntVar函数"""
    return ctk.IntVar()

def BooleanVar():
    """兼容性BooleanVar函数"""
    return ctk.BooleanVar()

def DoubleVar():
    """兼容性DoubleVar函数"""
    return ctk.DoubleVar()

def Variable():
    """兼容性Variable函数"""
    return ctk.Variable()

# 导出所有需要的组件
__all__ = [
    'ctk', 'CompatibilityWrapper', 'Tk', 'Toplevel',
    'StringVar', 'IntVar', 'BooleanVar', 'DoubleVar', 'Variable'
]