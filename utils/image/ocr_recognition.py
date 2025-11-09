"""
OCR文字识别模块
使用PaddleOCR实现图像中的文字识别
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
import paddleocr

@dataclass
class OCRResult:
    """OCR识别结果"""
    text: str  # 识别到的文字
    confidence: float  # 置信度 (0-1)
    bbox: List[List[int]]  # 文字区域坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    center: tuple  # 文字区域中心点 (x, y)

class OCRRecognition:
    """OCR文字识别类"""

    def __init__(self, use_gpu: bool = False, lang: str = 'ch'):
        """
        初始化OCR识别器

        Args:
            use_gpu: 是否使用GPU加速
            lang: 识别语言 ('ch'中文, 'en'英文, 'chinese_cht'繁体中文等)
        """
        self.use_gpu = use_gpu
        self.lang = lang
        self.ocr = None
        self.is_initialized = False

    def initialize(self):
        """
        手动初始化OCR模型（点击初始化时调用）

        Returns:
            bool: 初始化是否成功
        """
        if self.is_initialized:
            return True

        try:
            # 使用官方推荐的PaddleOCR初始化方式
            self.ocr = paddleocr.PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False
            )
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"OCR初始化失败: {e}")
            self.ocr = None
            self.is_initialized = False
            return False

    def _preprocess_image(self, image: Union[np.ndarray, str]) -> np.ndarray:
        """
        预处理图像

        Args:
            image: 图像（numpy数组或文件路径）

        Returns:
            预处理后的图像
        """
        if isinstance(image, str):
            # 从文件路径读取图像
            img = cv2.imread(image)
            if img is None:
                raise ValueError(f"无法读取图像文件: {image}")
        else:
            # 复制图像以避免修改原图
            img = image.copy()

        # 转换为RGB格式（PaddleOCR需要）
        if len(img.shape) == 3:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

        return img_rgb

    def recognize_text(self, image: Union[np.ndarray, str]) -> List[OCRResult]:
        """
        识别图像中的所有文字

        Args:
            image: 图像（numpy数组或文件路径）

        Returns:
            OCRResult列表，每个结果包含文字、置信度、坐标等信息
        """
        if not self.is_initialized or self.ocr is None:
            print("OCR识别器未正确初始化")
            return []

        try:
            # 预处理图像
            img_rgb = self._preprocess_image(image)

            # 使用新API进行OCR识别
            result = self.ocr.predict(img_rgb)

            if not result:
                return []

            ocr_results = []
            for res in result:
                # 解析识别结果
                rec_texts = res.get('rec_texts', [])
                rec_scores = res.get('rec_scores', [])
                rec_polys = res.get('rec_polys', [])

                for i, text in enumerate(rec_texts):
                    if i < len(rec_scores) and i < len(rec_polys):
                        confidence = float(rec_scores[i])
                        bbox_coords = rec_polys[i].tolist()

                        # 计算中心点
                        x_coords = [point[0] for point in bbox_coords]
                        y_coords = [point[1] for point in bbox_coords]
                        center_x = int(sum(x_coords) / len(x_coords))
                        center_y = int(sum(y_coords) / len(y_coords))

                        ocr_results.append(OCRResult(
                            text=text,
                            confidence=confidence,
                            bbox=bbox_coords,
                            center=(center_x, center_y)
                        ))

            return ocr_results

        except Exception as e:
            print(f"OCR识别失败: {e}")
            return []

    def extract_text_only(self, image: Union[np.ndarray, str]) -> str:
        """
        仅提取文字内容

        Args:
            image: 图像（numpy数组或文件路径）

        Returns:
            识别到的所有文字（空格分隔）
        """
        results = self.recognize_text(image)
        texts = [result.text for result in results if result.text.strip()]
        return ' '.join(texts)

    def contains_text(self, image: Union[np.ndarray, str], target_text: str,
                     confidence_threshold: float = 0.7) -> bool:
        """
        检查图像中是否包含指定文字

        Args:
            image: 图像（numpy数组或文件路径）
            target_text: 要查找的目标文字
            confidence_threshold: 置信度阈值

        Returns:
            是否包含目标文字
        """
        results = self.recognize_text(image)

        for result in results:
            if (result.confidence >= confidence_threshold and
                target_text.strip() in result.text.strip()):
                return True

        return False

    def find_text_location(self, image: Union[np.ndarray, str], target_text: str,
                          confidence_threshold: float = 0.7) -> Optional[OCRResult]:
        """
        查找指定文字的位置

        Args:
            image: 图像（numpy数组或文件路径）
            target_text: 要查找的目标文字
            confidence_threshold: 置信度阈值

        Returns:
            匹配文字的OCRResult，失败返回None
        """
        results = self.recognize_text(image)

        for result in results:
            if (result.confidence >= confidence_threshold and
                target_text.strip() in result.text.strip()):
                return result

        return None

    def find_all_text_locations(self, image: Union[np.ndarray, str],
                               confidence_threshold: float = 0.7) -> List[OCRResult]:
        """
        查找所有文字的位置

        Args:
            image: 图像（numpy数组或文件路径）
            confidence_threshold: 置信度阈值

        Returns:
            所有文字的OCRResult列表
        """
        results = self.recognize_text(image)
        return [result for result in results if result.confidence >= confidence_threshold]