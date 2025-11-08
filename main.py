#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏脚本控制面板 - 主程序入口

这个程序提供了一个基于JSON配置的UI框架，用于创建游戏脚本的参数设置界面。
支持多种游戏模式的可视化配置，包括RPG、FPS、竞速、手游等模式。
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from ui import MainInterface
    from utils.config_manager import ConfigManager
    from utils.global_manager import global_manager, set_global, get_global
    from utils.admin import is_admin, run_as_admin
except ImportError as e:
    import traceback
    traceback.print_exc()
    print(f"导入模块失败: {e}")
    print("请确保所有必要的文件都在正确的位置")
    sys.exit(1)


def main():
    """主函数"""
    try:
        print("正在启动游戏脚本控制面板...")
        # 检查管理员权限
        if not is_admin():
            print("当前未以管理员权限运行，尝试重新以管理员权限运行...")
            run_as_admin()

        # 创建并运行主界面
        app = MainInterface()
        app.run()

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()