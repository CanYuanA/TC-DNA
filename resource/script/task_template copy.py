#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务脚本模板

使用方法：
1. 复制此文件并重命名为你的任务名称
2. 修改 TaskScript 类名为你的任务类名
3. 在 start() 方法中实现你的任务逻辑
4. 配置 config/tasks.json 添加你的任务定义
"""

import time
from typing import Dict, Any
from utils.global_manager import log_info, log_warning, log_error, get_global


class TaskScript:
    """任务脚本模板类"""

    def __init__(self, settings: Dict[str, Any]):
        """
        初始化脚本

        Args:
            settings: 任务设置参数，从配置系统读取
        """
        self.settings = settings
        self.running = False

        # 从 settings 中获取用户配置参数
        # 例如：self.param_name = settings.get('param_name', default_value)

        log_info("任务脚本初始化完成")

    def start(self) -> bool:
        """
        启动脚本

        Returns:
            bool: 是否成功启动
        """
        if self.running:
            log_warning("脚本已在运行")
            return False

        self.running = True
        log_info("任务开始执行")

        try:
            # 在这里实现你的主任务逻辑
            # 使用 while self.running: 控制主循环
            # 任务逻辑示例：
            while self.running:
                # 执行你的任务代码
                # 例如：模拟任务执行
                time.sleep(1.0)
                log_info("任务运行中...")

            return True

        except Exception as e:
            log_error(f"执行错误: {e}")
            return False
        finally:
            self.stop()

    def stop(self):
        """停止脚本"""
        if not self.running:
            return
        self.running = False
        log_info("任务已停止")


# 脚本入口函数 - 必须存在且命名正确
def create_script(settings: Dict[str, Any]):
    """
    创建脚本实例

    Args:
        settings: 脚本设置，从配置系统获取

    Returns:
        TaskScript: 脚本实例
    """
    return TaskScript(settings)


# 可选：测试代码（开发和调试用）
if __name__ == "__main__":
    # 模拟测试设置
    test_settings = {
        # 'param_name': 'default_value'
    }

    script = create_script(test_settings)
    try:
        script.start()
    except KeyboardInterrupt:
        script.stop()
        log_info("测试已中断")