"""
图像处理API模块
提供窗口截图、OCR识别、模板匹配等功能
"""

from .window_capture import WindowCapture
from .ocr_recognition import OCRRecognition
from .template_matching import TemplateMatching
from .image_manager import ImageManager

# 全局图像管理器实例
_image_manager = None

def get_image_manager():
    """获取全局图像管理器实例"""
    global _image_manager
    if _image_manager is None:
        _image_manager = ImageManager()
    return _image_manager

def capture_window(hwnd, region=None):
    """快速截图函数"""
    capture = WindowCapture()
    return capture.capture_window(hwnd, region)

def capture_window_by_title(title, partial_match=True, region=None):
    """根据窗口标题快速截图函数"""
    from ..window.window_manager import WindowManager
    manager = WindowManager()
    window_info = manager.find_window(title=title, partial_match=partial_match)
    if window_info and window_info.is_valid():
        return capture_window(window_info.hwnd, region)
    return None

def ocr_text(image):
    """快速OCR识别函数"""
    ocr = OCRRecognition()
    return ocr.recognize_text(image)

def ocr_text_only(image):
    """快速OCR仅识别函数（无检测，适用于单行文字）"""
    ocr = OCRRecognition()
    return ocr.recognize_only(image)

def ocr_contains_text(image, text):
    """检查图像中是否包含指定文字"""
    ocr = OCRRecognition()
    return ocr.contains_text(image, text)

def find_template(template, source, threshold=0.8):
    """快速模板匹配函数"""
    matcher = TemplateMatching()
    return matcher.find_template(template, source, threshold)

def find_all_templates(template, source, threshold=0.8):
    """快速模板匹配所有位置函数"""
    matcher = TemplateMatching()
    return matcher.find_all_templates(template, source, threshold)

# 基于目标窗口的便捷函数
def capture_screenshot(region=None):
    """截取目标窗口截图（使用默认目标窗口）"""
    manager = get_image_manager()
    return manager.capture_screenshot(region)

def ocr_capture(region=None):
    """对目标窗口截图并进行OCR识别"""
    manager = get_image_manager()
    return manager.ocr_capture(region)

def ocr_capture_only(region=None):
    """对目标窗口截图并进行仅识别OCR（适用于单行文字）"""
    manager = get_image_manager()
    return manager.ocr_capture_only(region)

def find_text_in_window(text, region=None):
    """在目标窗口中查找文字"""
    manager = get_image_manager()
    return manager.find_text_in_window(text, region)

def find_template_in_window(template, region=None, threshold=0.8):
    """在目标窗口中查找模板"""
    manager = get_image_manager()
    return manager.find_template_in_window(template, region, threshold)

def is_text_visible(text, region=None):
    """检查目标窗口中是否可见指定文字"""
    manager = get_image_manager()
    return manager.is_text_visible(text, region)

def is_template_visible(template, region=None, threshold=0.8):
    """检查目标窗口中是否可见指定模板"""
    manager = get_image_manager()
    return manager.is_template_visible(template, region, threshold)

def wait_for_text(text, timeout=10.0, check_interval=0.5):
    """等待目标窗口中出现指定文字"""
    manager = get_image_manager()
    return manager.wait_for_text(text, timeout, check_interval)

def wait_for_template(template, timeout=10.0, threshold=0.8, check_interval=0.5):
    """等待目标窗口中出现指定模板"""
    manager = get_image_manager()
    return manager.wait_for_template(template, timeout, threshold, check_interval)

# 导出所有主要类和函数
__all__ = [
    # 核心类
    'WindowCapture',
    'OCRRecognition',
    'TemplateMatching',
    'ImageManager',
    # 全局实例获取
    'get_image_manager',
    # 便捷函数
    'capture_window',
    'capture_window_by_title',
    'ocr_text',
    'ocr_text_only',
    'ocr_contains_text',
    'find_template',
    'find_all_templates',
    # 基于目标窗口的便捷函数
    'capture_screenshot',
    'ocr_capture',
    'ocr_capture_only',
    'find_text_in_window',
    'find_template_in_window',
    'is_text_visible',
    'is_template_visible',
    'wait_for_text',
    'wait_for_template',
]