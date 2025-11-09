"""
窗口截图模块
使用Win32 API实现对非活动窗口的截图
"""

import cv2
import numpy as np
import ctypes
import time
from ctypes import wintypes
from typing import Optional, Tuple, Union
from dataclasses import dataclass

# Windows API常量
SRCCOPY = 0x00CC0020

# Windows API函数
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# 尝试导入win32ui
try:
    import win32gui
    import win32ui
    import win32con
    WIN32UI_AVAILABLE = True
except ImportError:
    WIN32UI_AVAILABLE = False

@dataclass
class CaptureRegion:
    """截图区域定义"""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

class WindowCapture:
    """窗口截图类"""

    def __init__(self):
        self.user32 = user32
        self.gdi32 = gdi32

    def _get_client_rect(self, hwnd) -> Tuple[int, int, int, int]:
        """获取窗口客户区矩形坐标"""
        # 直接获取窗口完整矩形
        window_rect = wintypes.RECT()
        result = self.user32.GetWindowRect(hwnd, ctypes.byref(window_rect))
        if not result:
            raise RuntimeError(f"无法获取窗口矩形: {hwnd}")

        # 获取客户区矩形
        client_rect = wintypes.RECT()
        result = self.user32.GetClientRect(hwnd, ctypes.byref(client_rect))
        if not result:
            raise RuntimeError(f"无法获取客户区矩形: {hwnd}")

        # 计算客户区在屏幕上的位置
        client_width = client_rect.right - client_rect.left
        client_height = client_rect.bottom - client_rect.top

        return (window_rect.left, window_rect.top,
                window_rect.left + client_width, window_rect.top + client_height)

    def capture_window(self, hwnd, region: Optional[CaptureRegion] = None) -> Optional[np.ndarray]:
        """
        截取窗口客户区图像

        Args:
            hwnd: 窗口句柄
            region: 截取区域，None表示截取整个客户区

        Returns:
            OpenCV格式的numpy数组（BGR格式）
        """
        try:
            # 检查窗口是否有效
            if not self.user32.IsWindow(hwnd):
                raise ValueError(f"无效的窗口句柄: {hwnd}")

            # 获取窗口客户区大小和位置
            if region is None:
                x, y, right, bottom = self._get_client_rect(hwnd)
                width = right - x
                height = bottom - y
                capture_region = CaptureRegion(x, y, width, height)
            else:
                capture_region = region

            if capture_region.width <= 0 or capture_region.height <= 0:
                raise ValueError("无效的截取区域大小")

            # 优先使用win32ui方法（如果可用）
            if WIN32UI_AVAILABLE:
                return self._capture_with_win32ui(hwnd, capture_region)
            else:
                return self._capture_with_pure_ctypes(hwnd, capture_region)

        except Exception as e:
            print(f"窗口截图失败: {e}")
            return None

    def _capture_with_win32ui(self, hwnd, region: CaptureRegion) -> Optional[np.ndarray]:
        """使用win32ui库进行截图（参考实现）"""
        try:
            # 获取窗口的设备上下文
            hdc_window = win32gui.GetWindowDC(hwnd)
            hdc_mem = win32ui.CreateDCFromHandle(hdc_window)

            # 创建第一个内存设备上下文来渲染整个窗口
            mem_dc_full = hdc_mem.CreateCompatibleDC()

            # 获取客户区完整大小
            client_x, client_y, client_right, client_bottom = self._get_client_rect(hwnd)
            full_width = client_right - client_x
            full_height = client_bottom - client_y

            # 创建完整窗口大小的位图
            bmp_full = win32ui.CreateBitmap()
            bmp_full.CreateCompatibleBitmap(hdc_mem, full_width, full_height)
            mem_dc_full.SelectObject(bmp_full)

            # 先用PrintWindow渲染整个窗口
            # PW_RENDERFULLCONTENT = 3, 强制渲染完整内容
            print_result = user32.PrintWindow(hwnd, mem_dc_full.GetSafeHdc(), 3)

            # 获取完整图像数据
            bmp_info_full = bmp_full.GetInfo()
            bmp_str_full = bmp_full.GetBitmapBits(True)

            # 使用PIL处理完整图像
            try:
                from PIL import Image
                full_screenshot = Image.frombuffer(
                    'RGB',
                    (bmp_info_full['bmWidth'], bmp_info_full['bmHeight']),
                    bmp_str_full, 'raw', 'BGRX', 0, 1
                )
                full_screenshot = np.array(full_screenshot)
                # 转换为BGR格式
                full_screenshot = cv2.cvtColor(full_screenshot, cv2.COLOR_RGB2BGR)
            except ImportError:
                # 如果PIL不可用，使用numpy直接处理
                full_screenshot = np.frombuffer(bmp_str_full, dtype=np.uint8)
                full_screenshot = full_screenshot.reshape(bmp_info_full['bmHeight'], bmp_info_full['bmWidth'], 4)
                full_screenshot = full_screenshot[:, :, :3]

            # 从完整图像中提取目标区域
            target_x = region.x
            target_y = region.y
            target_w = region.width
            target_h = region.height

            # 检查区域是否在有效范围内
            if target_x + target_w > full_width or target_y + target_h > full_height:
                # 调整区域大小以适应完整图像
                target_w = min(target_w, full_width - target_x)
                target_h = min(target_h, full_height - target_y)
                if target_w <= 0 or target_h <= 0:
                    raise ValueError("截取区域超出窗口范围")

            # 提取子区域
            if target_w > 0 and target_h > 0:
                result_image = full_screenshot[target_y:target_y+target_h, target_x:target_x+target_w]
            else:
                result_image = full_screenshot

            # 清理资源
            mem_dc_full.DeleteDC()
            win32gui.DeleteObject(bmp_full.GetHandle())
            win32gui.ReleaseDC(hwnd, hdc_window)

            return result_image

        except Exception as e:
            # win32ui方法失败，返回None
            return None

    def capture_window_full(self, hwnd, region: Optional[CaptureRegion] = None) -> Optional[np.ndarray]:
        """
        截取完整窗口（包括非客户区）

        Args:
            hwnd: 窗口句柄
            region: 截取区域，None表示截取整个窗口

        Returns:
            OpenCV格式的numpy数组
        """
        try:
            if not self.user32.IsWindow(hwnd):
                raise ValueError(f"无效的窗口句柄: {hwnd}")

            # 获取窗口矩形
            rect = wintypes.RECT()
            result = self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            if not result:
                raise RuntimeError(f"无法获取窗口矩形: {hwnd}")

            if region is None:
                x, y, right, bottom = rect.left, rect.top, rect.right, rect.bottom
                width = right - x
                height = bottom - y
                capture_region = CaptureRegion(x, y, width, height)
            else:
                capture_region = region

            if capture_region.width <= 0 or capture_region.height <= 0:
                raise ValueError("无效的截取区域大小")

            # 使用相同的方法截取完整窗口
            return self.capture_window(hwnd, capture_region)

        except Exception as e:
            print(f"窗口全屏截图失败: {e}")
            return None

    def save_screenshot(self, image: np.ndarray, filename: str) -> bool:
        """
        保存截图到文件

        Args:
            image: OpenCV格式的图像数组
            filename: 保存的文件名

        Returns:
            是否保存成功
        """
        try:
            # 确保是BGR格式
            if len(image.shape) == 3 and image.shape[2] == 3:
                cv2.imwrite(filename, image)
                return True
            else:
                raise ValueError("无效的图像格式")
        except Exception as e:
            print(f"保存截图失败: {e}")
            return False

    def create_capture_region(self, x: int, y: int, width: int, height: int) -> CaptureRegion:
        """
        创建截取区域

        Args:
            x: 左上角x坐标
            y: 左上角y坐标
            width: 宽度
            height: 高度

        Returns:
            CaptureRegion对象
        """
        return CaptureRegion(x, y, width, height)

    def get_window_client_size(self, hwnd) -> Optional[Tuple[int, int]]:
        """
        获取窗口客户区大小

        Args:
            hwnd: 窗口句柄

        Returns:
            (width, height)元组，失败返回None
        """
        try:
            if not self.user32.IsWindow(hwnd):
                return None

            rect = wintypes.RECT()
            result = self.user32.GetClientRect(hwnd, ctypes.byref(rect))
            if not result:
                return None

            return rect.right - rect.left, rect.bottom - rect.top

        except Exception as e:
            print(f"获取窗口客户区大小失败: {e}")
            return None

    def get_window_size(self, hwnd) -> Optional[Tuple[int, int, int, int]]:
        """
        获取窗口完整大小

        Args:
            hwnd: 窗口句柄

        Returns:
            (left, top, right, bottom)元组，失败返回None
        """
        try:
            if not self.user32.IsWindow(hwnd):
                return None

            rect = wintypes.RECT()
            result = self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            if not result:
                return None

            return rect.left, rect.top, rect.right, rect.bottom

        except Exception as e:
            print(f"获取窗口大小失败: {e}")
            return None