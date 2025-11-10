"""
图像处理统一管理器
整合截图、OCR、模板匹配等功能
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass

from .window_capture import WindowCapture, CaptureRegion
from .ocr_recognition import OCRRecognition, OCRResult
from .template_matching import TemplateMatching, MatchResult

class ImageManager:
    """图像处理统一管理器"""

    def __init__(self, use_gpu: bool = False, ocr_lang: str = 'ch'):
        """
        初始化图像管理器

        Args:
            use_gpu: 是否使用GPU加速（OCR）
            ocr_lang: OCR识别语言
        """
        self.window_capture = WindowCapture()
        self.ocr_recognition = OCRRecognition(use_gpu=use_gpu, lang=ocr_lang)
        self.template_matching = TemplateMatching()
        self.use_gpu = use_gpu
        self.ocr_lang = ocr_lang

    def get_ocr_stats(self) -> dict:
        """
        获取OCR识别统计信息

        Returns:
            统计信息字典
        """
        return self.ocr_recognition.get_recognition_stats()

    def _get_hwnd(self, window=None) -> Optional[int]:
        """获取窗口句柄"""
        if window is not None:
            if hasattr(window, 'handle'):
                return window.handle
            if hasattr(window, 'hwnd'):
                return window.hwnd
            if isinstance(window, int):
                return window

        # 从全局状态获取
        try:
            from ..global_manager import get_global
            current_window = get_global('target_window')
            if current_window is None:
                return None

            if hasattr(current_window, 'handle'):
                return current_window.handle
            if hasattr(current_window, 'hwnd'):
                return current_window.hwnd
            if isinstance(current_window, int):
                return current_window
        except:
            pass

        return None

    def is_target_window_valid(self) -> bool:
        """检查目标窗口是否有效"""
        try:
            from ..global_manager import get_global
            window = get_global('target_window')
            if window is None:
                return False

            hwnd = self._get_hwnd(window)
            if hwnd is None:
                return False

            import ctypes
            user32 = ctypes.windll.user32
            return user32.IsWindow(hwnd)
        except:
            return False

    # ==================== 核心功能方法 ====================

    def capture_window_region(self, window=None, region: Optional[CaptureRegion] = None):
        """
        截取窗口指定区域

        Args:
            window: 窗口对象或句柄，None使用默认目标窗口
            region: 截取区域，None表示整个客户区

        Returns:
            图像数组或None
        """
        hwnd = self._get_hwnd(window)
        if hwnd is None:
            return None
        return self.window_capture.capture_window(hwnd, region)

    def capture_and_ocr(self, window=None, region: Optional[CaptureRegion] = None):
        """
        截取窗口并执行OCR识别

        Args:
            window: 窗口对象或句柄，None使用默认目标窗口
            region: 截取区域

        Returns:
            OCRResult列表
        """
        # 第一步：截图
        image = self.capture_window_region(window, region)
        if image is None:
            return []

        # 第二步：OCR识别
        return self.ocr_recognition.recognize_text(image)

    def capture_and_ocr_only(self, window=None, region: Optional[CaptureRegion] = None):
        """
        截取窗口并执行仅识别OCR（无检测，适用于单行文字）

        Args:
            window: 窗口对象或句柄，None使用默认目标窗口
            region: 截取区域

        Returns:
            OCRResult列表
        """
        # 第一步：截图
        image = self.capture_window_region(window, region)
        if image is None:
            return []

        # 第二步：仅OCR识别（无检测）
        return self.ocr_recognition.recognize_only(image)

    def capture_and_match(self, template: Union[np.ndarray, str], window=None,
                         region: Optional[CaptureRegion] = None, threshold: float = 0.8):
        """
        截取窗口并进行模板匹配

        Args:
            window: 窗口对象或句柄，None使用默认目标窗口
            template: 模板图像
            region: 截取区域
            threshold: 匹配阈值

        Returns:
            MatchResult或None
        """
        # 第一步：截图
        image = self.capture_window_region(window, region)
        if image is None:
            return None

        # 第二步：模板匹配
        return self.template_matching.find_template(template, image, threshold)

    # ==================== 便捷方法 ====================

    def capture_screenshot(self, region: Optional[CaptureRegion] = None):
        """
        快速截图（使用默认目标窗口）

        Args:
            region: 截取区域，None表示整个客户区

        Returns:
            图像数组或None
        """
        return self.capture_window_region(None, region)

    def ocr_capture(self, region: Optional[CaptureRegion] = None):
        """
        快速OCR识别（使用默认目标窗口）

        Args:
            region: 截取区域，None表示整个客户区

        Returns:
            OCRResult列表
        """
        return self.capture_and_ocr(None, region)

    def ocr_capture_only(self, region: Optional[CaptureRegion] = None):
        """
        快速OCR仅识别（使用默认目标窗口，适用于单行文字）

        Args:
            region: 截取区域，None表示整个客户区

        Returns:
            OCRResult列表
        """
        return self.capture_and_ocr_only(None, region)

    def find_text_in_window(self, text: str, region: Optional[CaptureRegion] = None):
        """
        快速查找文字位置

        Args:
            text: 要查找的文字
            region: 搜索区域，None表示整个窗口

        Returns:
            OCRResult或None
        """
        results = self.ocr_capture(region)
        for result in results:
            if text in result.text:
                return result
        return None

    def find_template_in_window(self, template: Union[np.ndarray, str],
                               region: Optional[CaptureRegion] = None, threshold: float = 0.8):
        """
        快速模板匹配

        Args:
            template: 模板图像
            region: 搜索区域，None表示整个窗口
            threshold: 匹配阈值

        Returns:
            MatchResult或None
        """
        return self.capture_and_match(template, None, region, threshold)

    def is_text_visible(self, text: str, region: Optional[CaptureRegion] = None):
        """
        检查文字是否可见

        Args:
            text: 要检查的文字
            region: 搜索区域，None表示整个窗口

        Returns:
            是否可见
        """
        return self.find_text_in_window(text, region) is not None

    def is_template_visible(self, template: Union[np.ndarray, str],
                           region: Optional[CaptureRegion] = None, threshold: float = 0.8):
        """
        检查模板是否可见

        Args:
            template: 模板图像
            region: 搜索区域，None表示整个窗口
            threshold: 匹配阈值

        Returns:
            是否可见
        """
        return self.find_template_in_window(template, region, threshold) is not None

    def wait_for_text(self, text: str, timeout: float = 10.0, check_interval: float = 0.5):
        """
        等待文字出现

        Args:
            text: 要等待的文字
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）

        Returns:
            找到的文字结果，超时返回None
        """
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.find_text_in_window(text)
            if result:
                return result
            time.sleep(check_interval)

        return None

    def wait_for_template(self, template: Union[np.ndarray, str], timeout: float = 10.0,
                         threshold: float = 0.8, check_interval: float = 0.5):
        """
        等待模板出现

        Args:
            template: 模板图像
            timeout: 超时时间（秒）
            threshold: 匹配阈值
            check_interval: 检查间隔（秒）

        Returns:
            找到的匹配结果，超时返回None
        """
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.find_template_in_window(template, threshold=threshold)
            if result:
                return result
            time.sleep(check_interval)

        return None