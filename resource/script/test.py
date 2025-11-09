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
from utils.global_manager import log_info, log_warning, log_error, log_debug, get_global
from utils.input import get_input_manager
from utils.image import get_image_manager
from utils.window import get_window_manager


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
        self.input_manager = get_input_manager()
        self.image_manager = get_image_manager()
        self.window_manager = get_window_manager()

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

        recharge_time = int(self.settings.get('重蓄时间', 5.0)) / 1000.0  # 转换为秒
        interval_time = int(self.settings.get('间隔时间', 2.0)) / 1000.0  # 转换为秒

        try:
            # 在这里实现你的主任务逻辑
            # 使用 while self.running: 控制主循环
            # 任务逻辑示例：
            while self.running:
                # 执行你的任务代码
                # 例如：模拟任务执行
                # time.sleep(interval_time)
                # log_info("任务运行中...")

                # 测试图像截取
                log_info("开始截图测试...")
                from utils.image.window_capture import CaptureRegion

                screenshot = self.image_manager.capture_screenshot(CaptureRegion(2152-1920,278,60,40))
                import cv2
                cv2.imshow("screenshot", screenshot)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                r = self.image_manager.ocr_recognition.recognize_text(screenshot)
                print(r)
                for item in r:
                    log_info(f"OCR识别到文字: {item.text} (置信度: {item.confidence:.2f})")
                    self.input_manager.click(item.center[0]+2152-1920, item.center[1]+278)


                break  # 测试完成，退出循环

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