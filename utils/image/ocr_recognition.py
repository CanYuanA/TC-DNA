"""
OCR文字识别模块
使用PaddleOCR实现图像中的文字识别
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
from rapidocr import RapidOCR, EngineType, LangDet, LangRec, ModelType, OCRVersion

@dataclass
class OCRResult:
    """OCR识别结果"""
    text: str  # 识别到的文字
    confidence: float  # 置信度 (0-1)
    bbox: List[List[int]]  # 文字区域坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    center: tuple  # 文字区域中心点 (x, y)

class OCRRecognition:
    """OCR文字识别类"""

    def __init__(self):
        """
        初始化OCR识别器
        """
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
            self.ocr = RapidOCR(params={
                "Det.engine_type": EngineType.ONNXRUNTIME,
                "Det.lang_type": LangDet.CH,
                "Det.model_type": ModelType.MOBILE,
                "Det.ocr_version": OCRVersion.PPOCRV5,
                "Rec.engine_type": EngineType.ONNXRUNTIME,
                "Rec.lang_type": LangRec.CH,
                "Rec.model_type": ModelType.MOBILE,
                "Rec.ocr_version": OCRVersion.PPOCRV5,})
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

    def recognize_text(self, image: Union[np.ndarray, str], mode: str = "detect_recognize") -> List[OCRResult]:
        """
        识别图像中的所有文字

        Args:
            image: 图像（numpy数组或文件路径）
            mode: 识别模式
                - "detect_recognize": 检测+识别（use_det=True, use_cls=True, use_rec=True）
                - "recognize_only": 仅识别（use_det=False, use_cls=False, use_rec=True）

        Returns:
            OCRResult列表，每个结果包含文字、置信度、坐标等信息
        """
        if not self.is_initialized or self.ocr is None:
            print("OCR识别器未正确初始化")
            return []

        try:
            # 预处理图像
            img = self._preprocess_image(image)

            # 根据模式选择参数
            if mode == "recognize_only":
                use_det, use_cls, use_rec = False, False, True
            else:  # detect_recognize
                use_det, use_cls, use_rec = True, True, True

            # 使用RapidOCR进行识别
            result = self.ocr(img, use_det=use_det, use_cls=use_cls, use_rec=use_rec)

            if not result:
                return []

            # 解析RapidOCR结果
            ocr_results = []

            # RapidOCR返回类型判断
            if hasattr(result, 'txts') and result.txts:  # RapidOCROutput类型
                boxes = getattr(result, 'boxes', [])
                txts = result.txts
                scores = getattr(result, 'scores', [1.0] * len(txts))
                elapse = getattr(result, 'elapse', 0.0)

                for i, (text, score, box) in enumerate(zip(txts, scores, boxes)):
                    if not text.strip():
                        continue

                    # 计算中心点
                    if len(box) >= 4:
                        x_coords = [point[0] for point in box]
                        y_coords = [point[1] for point in box]
                        center_x = int(sum(x_coords) / len(x_coords))
                        center_y = int(sum(y_coords) / len(y_coords))
                        center = (center_x, center_y)

                        # 确保bbox是列表格式
                        bbox_coords = [point.tolist() if hasattr(point, 'tolist') else list(point) for point in box]
                    else:
                        center = (0, 0)
                        bbox_coords = [[0, 0], [0, 0], [0, 0], [0, 0]]

                    ocr_results.append(OCRResult(
                        text=text,
                        confidence=float(score),
                        bbox=bbox_coords,
                        center=center,
                        rec_time=elapse
                    ))

            elif isinstance(result, list) and len(result) > 0:  # 兼容旧格式
                for res in result:
                    if isinstance(res, dict):
                        rec_texts = res.get('rec_texts', [])
                        rec_scores = res.get('rec_scores', [])
                        rec_polys = res.get('rec_polys', [])

                        for i, text in enumerate(rec_texts):
                            if i < len(rec_scores) and i < len(rec_polys):
                                confidence = float(rec_scores[i])
                                bbox_coords = rec_polys[i].tolist() if hasattr(rec_polys[i], 'tolist') else rec_polys[i]

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

    def recognize_only(self, image: Union[np.ndarray, str]) -> List[OCRResult]:
        """
        仅识别模式（无检测，适用于单行文字）

        Args:
            image: 图像（numpy数组或文件路径）

        Returns:
            OCRResult列表
        """
        return self.recognize_text(image, mode="recognize_only")

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

    def batch_ocr(self, images: List[Union[np.ndarray, str]]) -> List[List[OCRResult]]:
        """
        批量OCR识别

        Args:
            images: 图像列表

        Returns:
            每张图像的OCR结果列表
        """
        results = []
        for img in images:
            ocr_results = self.recognize_text(img)
            results.append(ocr_results)
        return results

    def get_text_with_coords(self, image: Union[np.ndarray, str],
                           min_confidence: float = 0.7) -> List[tuple]:
        """
        获取文字和坐标对

        Args:
            image: 图像（numpy数组或文件路径）
            min_confidence: 最小置信度

        Returns:
            [(文字, 坐标), ...] 列表
        """
        results = self.recognize_text(image)
        text_coords = []

        for result in results:
            if result.confidence >= min_confidence:
                text_coords.append((result.text, result.center))

        return text_coords

    def wait_for_text(self, image_getter, target_text: str, timeout: float = 5.0,
                     check_interval: float = 0.5, confidence_threshold: float = 0.7) -> Optional[OCRResult]:
        """
        等待文字出现

        Args:
            image_getter: 获取图像的函数（每次检查时调用）
            target_text: 要等待的文字
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
            confidence_threshold: 置信度阈值

        Returns:
            找到的文字结果，超时返回None
        """
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            image = image_getter()
            if image is not None:
                result = self.find_text_location(image, target_text, confidence_threshold)
                if result:
                    return result
            time.sleep(check_interval)

        return None

    def recognize_specific_area(self, image: Union[np.ndarray, str],
                               region: tuple) -> List[OCRResult]:
        """
        识别图像特定区域的文字

        Args:
            image: 原始图像
            region: 区域坐标 (x, y, width, height)

        Returns:
            指定区域的OCR结果
        """
        x, y, w, h = region
        cropped = self._preprocess_image(image)[y:y+h, x:x+w]
        return self.recognize_text(cropped)