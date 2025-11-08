import tkinter as tk
from tkinter import ttk, filedialog
from typing import Any, Dict, List, Optional, Callable
import re

# 使用CustomTkinter
import customtkinter as ctk
from ..compatibility import CompatibilityWrapper


class BaseUIElement:
    """UI元素基类"""

    def __init__(self, parent, config: Dict[str, Any], manager):
        """
        初始化UI元素

        Args:
            parent: 父容器
            config: 元素配置
            manager: 配置管理器
        """
        self.parent = parent
        self.config = config
        self.manager = manager
        self.widget = None
        self.var = None
        self.create()

    def create(self):
        """创建UI元素 - 子类需要重写此方法"""
        pass

    def get_value(self) -> Any:
        """获取元素值"""
        if hasattr(self, 'var') and self.var:
            return self.var.get()
        return None

    def set_value(self, value: Any):
        """设置元素值"""
        if hasattr(self, 'var') and self.var:
            self.var.set(value)

    def save_to_config(self, var_name: str):
        """保存值到配置"""
        if var_name:
            value = self.get_value()
            self.manager.set(var_name, value)


class LabelElement(BaseUIElement):
    """标签元素"""

    def create(self):
        font_size = self.config.get('font_size', 12)
        font_weight = self.config.get('font_weight', 'normal')

        # 使用CustomTkinter的字体配置
        if font_weight == 'bold':
            self.widget = ctk.CTkLabel(
                self.parent,
                text=self.config.get('text', ''),
                font=ctk.CTkFont(family="Arial", size=font_size, weight="bold")
            )
        else:
            self.widget = ctk.CTkLabel(
                self.parent,
                text=self.config.get('text', ''),
                font=ctk.CTkFont(family="Arial", size=font_size)
            )
        self.widget.pack(anchor='w', pady=5)


class EntryElement(BaseUIElement):
    """输入框元素"""

    def create(self):
        # 创建标签
        if 'label' in self.config:
            label = ctk.CTkLabel(self.parent, text=self.config['label'])
            label.pack(anchor='w')

        # 创建输入框
        width = self.config.get('width', 30)
        self.widget = ctk.CTkEntry(
            self.parent,
            width=width * 8  # CustomTkinter的宽度单位不同
        )
        self.widget.pack(anchor='w', pady=2)

        # 设置变量
        var_name = self.config.get('var_name')
        if var_name:
            self.var = ctk.StringVar()
            self.widget.configure(textvariable=self.var)

            # 从配置加载默认值
            default_value = self.config.get('default', '')
            saved_value = self.manager.get(var_name, default_value)
            self.var.set(saved_value)

            # 绑定回车键保存
            self.widget.bind('<Return>', lambda e: self.save_to_config(var_name))


class ButtonElement(BaseUIElement):
    """按钮元素"""

    def create(self):
        width = self.config.get('width', 10)
        command = self.config.get('command', '')

        self.widget = ctk.CTkButton(
            self.parent,
            text=self.config.get('text', '按钮'),
            width=width * 8,  # CustomTkinter的宽度单位不同
            command=lambda: self._execute_command(command)
        )
        self.widget.pack(anchor='w', pady=5)

    def _execute_command(self, command: str):
        """执行命令"""
        # 其他自定义命令可以在这里扩展
        print(f"执行命令: {command}")


class CheckboxElement(BaseUIElement):
    """复选框元素"""

    def create(self):
        var_name = self.config.get('var_name')
        self.var = ctk.BooleanVar()

        self.widget = ctk.CTkCheckBox(
            self.parent,
            text=self.config.get('label', ''),
            variable=self.var
        )
        self.widget.pack(anchor='w', pady=2)

        # 设置默认值
        if var_name:
            default_value = self.config.get('default', False)
            saved_value = self.manager.get(var_name, default_value)
            self.var.set(saved_value)


class ComboboxElement(BaseUIElement):
    """下拉框元素"""

    def create(self):
        # 创建标签
        if 'label' in self.config:
            label = ctk.CTkLabel(self.parent, text=self.config['label'])
            label.pack(anchor='w')

        # 创建下拉框
        values = self.config.get('values', [])
        self.widget = ctk.CTkComboBox(
            self.parent,
            values=values,
            command=self._on_selection  # CustomTkinter使用command回调
        )
        self.widget.pack(anchor='w', pady=2)

        # 设置变量
        var_name = self.config.get('var_name')
        if var_name:
            self.var = ctk.StringVar()
            # CustomTkinter的ComboBox不直接使用textvariable，但可以手动设置
            # 设置默认值
            default_value = self.config.get('default', values[0] if values else '')
            saved_value = self.manager.get(var_name, default_value)
            if saved_value in values:
                self.widget.set(saved_value)
            else:
                self.widget.set(default_value)

    def _on_selection(self, value):
        """选择回调"""
        if hasattr(self, 'var') and self.var:
            self.var.set(value)


class ScaleElement(BaseUIElement):
    """滑块元素"""

    def create(self):
        # 创建标签
        if 'label' in self.config:
            label = ctk.CTkLabel(self.parent, text=self.config['label'])
            label.pack(anchor='w')

        # 创建滑块
        from_value = self.config.get('from', 0)
        to_value = self.config.get('to', 100)
        orient = self.config.get('orient', 'horizontal')

        self.widget = ctk.CTkSlider(
            self.parent,
            from_=from_value,
            to=to_value,
            width=200
        )
        self.widget.pack(anchor='w', pady=2)

        # 设置变量
        var_name = self.config.get('var_name')
        if var_name:
            self.var = ctk.IntVar()
            self.widget.configure(variable=self.var, command=self._on_slider_change)

            # 设置默认值
            default_value = self.config.get('default', (from_value + to_value) // 2)
            saved_value = self.manager.get(var_name, default_value)
            self.widget.set(saved_value)

    def _on_slider_change(self, value):
        """滑块值变化回调"""
        if hasattr(self, 'var') and self.var:
            self.var.set(int(value))


class TextElement(BaseUIElement):
    """多行文本框元素"""

    def create(self):
        # 创建标签
        if 'label' in self.config:
            label = ctk.CTkLabel(self.parent, text=self.config['label'])
            label.pack(anchor='w')

        # 创建文本框（CustomTkinter内置滚动条）
        height = self.config.get('height', 5)
        self.widget = ctk.CTkTextbox(
            self.parent,
            height=height * 20  # CustomTkinter的高度单位不同
        )
        self.widget.pack(anchor='w', pady=2, fill='x')

        # 设置内容
        var_name = self.config.get('var_name')
        if var_name:
            default_value = self.config.get('default', '')
            saved_value = self.manager.get(var_name, default_value)
            self.widget.insert('1.0', saved_value)


class ListboxElement(BaseUIElement):
    """列表框元素"""

    def create(self):
        # 创建标签
        if 'label' in self.config:
            label = ctk.CTkLabel(self.parent, text=self.config['label'])
            label.pack(anchor='w')

        # 创建可滚动框架作为Listbox的替代
        values = self.config.get('values', [])
        height = self.config.get('height', 5)

        # 使用CTkScrollableFrame模拟Listbox
        self.widget = ctk.CTkScrollableFrame(
            self.parent,
            height=height * 30
        )
        self.widget.pack(anchor='w', pady=2, fill='x')

        # 在可滚动框架中创建选项
        self.list_items = []
        for i, value in enumerate(values):
            item_frame = ctk.CTkFrame(self.widget)
            item_frame.pack(fill='x', pady=1, padx=2)

            item_button = ctk.CTkButton(
                item_frame,
                text=value,
                command=lambda idx=i, val=value: self._on_item_selected(idx, val),
                width=0,
                height=25,
                anchor='w',
                fg_color='transparent',
                hover_color='#404040'
            )
            item_button.pack(fill='x')
            self.list_items.append((item_button, value))

        # 设置变量
        var_name = self.config.get('var_name')
        if var_name:
            self.var = ctk.StringVar()
            self.selected_index = -1

    def _on_item_selected(self, index: int, value: str):
        """列表项选择回调"""
        self.selected_index = index
        if hasattr(self, 'var') and self.var:
            self.var.set(value)

        # 更新视觉状态
        for i, (button, _) in enumerate(self.list_items):
            if i == index:
                button.configure(fg_color='#0066cc')  # 选中状态
            else:
                button.configure(fg_color='transparent')  # 未选中状态

    def get_value(self) -> Any:
        """获取元素值"""
        if hasattr(self, 'var') and self.var:
            return self.var.get()
        return None

    def set_value(self, value: Any):
        """设置元素值"""
        if hasattr(self, 'var') and self.var:
            self.var.set(value)
            # 同步视觉状态
            for i, (_, val) in enumerate(self.list_items):
                if val == value:
                    self.selected_index = i
                    self._on_item_selected(i, val)
                    break


# UI元素工厂类
class UIElementFactory:
    """UI元素工厂"""

    _element_classes = {
        'label': LabelElement,
        'entry': EntryElement,
        'button': ButtonElement,
        'checkbox': CheckboxElement,
        'combobox': ComboboxElement,
        'scale': ScaleElement,
        'text': TextElement,
        'listbox': ListboxElement
    }

    @classmethod
    def create_element(cls, element_type: str, parent, config: Dict[str, Any], manager) -> BaseUIElement:
        """
        创建UI元素

        Args:
            element_type: 元素类型
            parent: 父容器
            config: 元素配置
            manager: 配置管理器

        Returns:
            UI元素实例
        """
        element_class = cls._element_classes.get(element_type, LabelElement)
        return element_class(parent, config, manager)

    @classmethod
    def register_element(cls, element_type: str, element_class):
        """注册新的UI元素类型"""
        cls._element_classes[element_type] = element_class