#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
窗口操作API包

提供窗口查找、操作、管理等功能
"""

from .window_manager import WindowManager, WindowInfo, WindowNotFoundError, find_window, get_window_info, get_window_manager

__all__ = ['WindowManager', 'WindowInfo', 'WindowNotFoundError', 'find_window', 'get_window_info', 'get_window_manager']