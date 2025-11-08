#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器

负责任务的配置、加载、执行管理
"""

import json
import os
import importlib.util
import threading
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import logging

from utils.global_manager import log_info, log_warning, log_error, set_global, get_global
from utils.config_manager import ConfigManager


class TaskStatus(Enum):
    """任务状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"


class TaskState(Enum):
    """任务状态（用于UI显示）"""
    DISABLED = "disabled"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class TaskInfo:
    """任务信息数据类"""
    task_id: str
    name: str
    description: str
    icon: str
    script_file: str
    category: str
    enabled: bool

    @property
    def script_path(self) -> str:
        """获取脚本文件完整路径"""
        return os.path.join("resource", "script", self.script_file)

    def is_available(self) -> bool:
        """检查任务是否可用"""
        return self.enabled and os.path.exists(self.script_path)

    def get_settings(self) -> Dict[str, Any]:
        """从ConfigManager获取任务设置"""
        config_manager = ConfigManager()

        # 优先查找Tasks命名空间下的设置
        settings = config_manager.get(f"Tasks.{self.task_id}", None)

        # 如果Tasks命名空间下没有，兼容旧格式直接使用任务ID
        if settings is None:
            settings = config_manager.get(self.task_id, {})

        if settings is None:
            return {}

        return settings

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'script_file': self.script_file,
            'category': self.category,
            'enabled': self.enabled,
            'available': self.is_available()
        }


class TaskRunner:
    """任务执行器"""

    def __init__(self, task_info: TaskInfo):
        """
        初始化任务执行器

        Args:
            task_info: 任务信息
        """
        self.task_info = task_info
        self.status = TaskStatus.STOPPED
        self.script_instance = None
        self.script_thread = None
        self._stop_event = threading.Event()

    def start(self) -> bool:
        """
        启动任务

        Returns:
            bool: 是否成功启动
        """
        try:
            if self.status == TaskStatus.RUNNING:
                log_warning(f"任务 {self.task_info.name} 已在运行")
                return False

            if not self.task_info.is_available():
                log_error(f"任务 {self.task_info.name} 不可用")
                return False

            # 加载脚本
            if not self._load_script():
                return False

            # 启动执行线程
            self._stop_event.clear()
            self.status = TaskStatus.RUNNING

            self.script_thread = threading.Thread(target=self._run_script, daemon=True)
            self.script_thread.start()

            # 更新全局状态
            set_global(f'task.{self.task_info.task_id}.status', 'running', notify=True)
            set_global(f'task.{self.task_info.task_id}.start_time', time.time(), notify=False)

            log_info(f"任务 {self.task_info.name} 已启动")
            return True

        except Exception as e:
            log_error(f"启动任务失败: {e}")
            self.status = TaskStatus.ERROR

            # 通知任务错误（如果可能的话）
            try:
                # 这里需要获取任务管理器实例来通知回调
                # 但TaskRunner没有直接引用任务管理器，所以暂时记录日志
                log_error(f"任务 {self.task_info.name} 启动时发生错误: {e}")
            except:
                pass

            return False

    def stop(self):
        """停止任务"""
        if self.status == TaskStatus.STOPPED:
            return

        log_info(f"正在停止任务 {self.task_info.name}...")

        # 停止信号
        self._stop_event.set()

        # 调用脚本的停止方法
        if self.script_instance and hasattr(self.script_instance, 'stop'):
            try:
                self.script_instance.stop()
            except Exception as e:
                log_error(f"停止脚本失败: {e}")

        # 等待线程结束，但避免join自己
        if self.script_thread and self.script_thread.is_alive():
            current_thread = threading.current_thread()
            if self.script_thread != current_thread:
                self.script_thread.join(timeout=5.0)
            else:
                # 当前线程就是脚本线程，不能join自己
                log_warning(f"任务 {self.task_info.name} 在自己的线程中停止")

        self.status = TaskStatus.STOPPED
        set_global(f'task.{self.task_info.task_id}.status', 'stopped', notify=True)

        log_info(f"任务 {self.task_info.name} 已停止")

    def _load_script(self) -> bool:
        """
        加载脚本文件

        Returns:
            bool: 是否成功加载
        """
        try:
            script_path = self.task_info.script_path
            spec = importlib.util.spec_from_file_location("task_script", script_path)

            if not spec or not spec.loader:
                log_error(f"无法加载脚本文件: {script_path}")
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找创建脚本的函数
            if hasattr(module, 'create_script'):
                create_func = getattr(module, 'create_script')
                settings = self.task_info.get_settings()
                self.script_instance = create_func(settings)
                return True
            else:
                log_error(f"脚本文件 {script_path} 缺少 create_script 函数")
                return False

        except Exception as e:
            log_error(f"加载脚本失败: {e}")
            return False

    def _run_script(self):
        """在独立线程中运行脚本"""
        try:
            if self.script_instance and hasattr(self.script_instance, 'start'):
                self.script_instance.start()

            # 脚本正常结束
            if self.status == TaskStatus.RUNNING:
                self.status = TaskStatus.STOPPED
                log_info(f"任务 {self.task_info.name} 正常结束")
                # 通知任务管理器任务已停止
                set_global(f'task.{self.task_info.task_id}.status', 'stopped', notify=True)

        except Exception as e:
            log_error(f"脚本执行出错: {e}")
            self.status = TaskStatus.ERROR
            set_global(f'task.{self.task_info.task_id}.status', 'error', notify=True)


class TaskManager:
    """任务管理器"""

    def __init__(self, config_path: str = "config/tasks.json"):
        """
        初始化任务管理器

        Args:
            config_path: 任务配置文件路径
        """
        self.config_path = config_path
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_runners: Dict[str, TaskRunner] = {}
        self.task_callbacks: List[Callable] = []
        self.load_tasks()

    def load_tasks(self) -> bool:
        """
        加载任务配置

        Returns:
            bool: 是否成功加载
        """
        try:
            if not os.path.exists(self.config_path):
                log_error(f"任务配置文件不存在: {self.config_path}")
                return False

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 加载任务
            self.tasks.clear()
            tasks_data = config_data.get('tasks', {})

            for task_id, task_data in tasks_data.items():
                try:
                    task_info = TaskInfo(
                        task_id=task_id,
                        name=task_data.get('name', task_id),
                        description=task_data.get('description', ''),
                        icon=task_data.get('icon', '📋'),
                        script_file=task_data.get('script_file', ''),
                        category=task_data.get('category', '其他'),
                        enabled=task_data.get('enabled', True)
                    )
                    self.tasks[task_id] = task_info
                    log_info(f"已加载任务: {task_info.name} (分类: {task_info.category})")
                except Exception as e:
                    log_error(f"加载任务 {task_id} 失败: {e}")

            # 保存配置的分类顺序
            self.categories = config_data.get('categories', [])

            log_info(f"任务加载完成，共 {len(self.tasks)} 个任务")
            for task_id, task in self.tasks.items():
                log_info(f"  - {task_id}: 分类='{task.category}'")
            return True

        except Exception as e:
            log_error(f"加载任务配置失败: {e}")
            return False

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            TaskInfo: 任务信息，如果不存在则返回None
        """
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[TaskInfo]:
        """
        获取所有任务

        Returns:
            List[TaskInfo]: 任务信息列表
        """
        return list(self.tasks.values())

    def get_tasks_by_category(self, category: str) -> List[TaskInfo]:
        """
        按分类获取任务

        Args:
            category: 任务分类

        Returns:
            List[TaskInfo]: 任务信息列表
        """
        return [task for task in self.tasks.values() if task.category == category]

    def get_available_tasks(self) -> List[TaskInfo]:
        """
        获取所有可用的任务

        Returns:
            List[TaskInfo]: 可用任务列表
        """
        return [task for task in self.tasks.values() if task.is_available()]

    def start_task(self, task_id: str) -> bool:
        """
        启动任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功启动
        """
        task_info = self.get_task(task_id)
        if not task_info:
            log_error(f"任务不存在: {task_id}")
            return False

        if task_id in self.task_runners:
            runner = self.task_runners[task_id]
            if runner.status == TaskStatus.RUNNING:
                log_warning(f"任务 {task_info.name} 已在运行")
                return False

        # 创建任务执行器
        runner = TaskRunner(task_info)
        success = runner.start()

        if success:
            self.task_runners[task_id] = runner
            self._notify_callbacks('task_started', task_info)

        return success

    def stop_task(self, task_id: str):
        """
        停止任务

        Args:
            task_id: 任务ID
        """
        if task_id in self.task_runners:
            runner = self.task_runners[task_id]
            runner.stop()
            del self.task_runners[task_id]
            task = self.get_task(task_id)
            if task:
                self._notify_callbacks('task_stopped', task)

    def stop_all_tasks(self):
        """停止所有任务"""
        for task_id in list(self.task_runners.keys()):
            self.stop_task(task_id)

    def get_task_status(self, task_id: str) -> TaskState:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            TaskState: 任务状态
        """
        task_info = self.get_task(task_id)
        if not task_info or not task_info.enabled:
            return TaskState.DISABLED

        if task_id in self.task_runners:
            runner = self.task_runners[task_id]
            if runner.status == TaskStatus.RUNNING:
                return TaskState.RUNNING
            elif runner.status == TaskStatus.ERROR:
                return TaskState.ERROR

        return TaskState.READY

    def add_task_callback(self, callback: Callable):
        """
        添加任务状态变化回调

        Args:
            callback: 回调函数，参数为 (event_type, task_info)
        """
        self.task_callbacks.append(callback)

    def remove_task_callback(self, callback: Callable):
        """移除任务状态变化回调"""
        if callback in self.task_callbacks:
            self.task_callbacks.remove(callback)

    def _notify_callbacks(self, event_type: str, task_info: TaskInfo):
        """通知所有回调函数"""
        for callback in self.task_callbacks:
            try:
                callback(event_type, task_info)
            except Exception as e:
                log_error(f"任务回调函数执行失败: {e}")

    def get_task_categories(self) -> List[str]:
        """
        获取所有任务分类

        Returns:
            List[str]: 分类列表（保持配置文件中定义的顺序）
        """
        # 优先使用配置文件中定义的分类顺序
        if hasattr(self, 'categories') and self.categories:
            # 确保配置中的分类在当前任务中存在
            existing_categories = set(task.category for task in self.tasks.values())
            ordered_categories = [cat for cat in self.categories if cat in existing_categories]

            # 添加可能遗漏的动态分类（但这些分类不包含在原配置中）
            for task in self.tasks.values():
                if task.category not in ordered_categories:
                    ordered_categories.append(task.category)

            return ordered_categories
        else:
            # 如果没有配置顺序，则使用默认行为（按字母排序）
            categories = set()
            for task in self.tasks.values():
                categories.add(task.category)
            return sorted(list(categories))


# 全局任务管理器实例
_task_manager = None


def get_task_manager() -> TaskManager:
    """获取全局任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager