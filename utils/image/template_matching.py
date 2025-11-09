"""
模板匹配模块
使用OpenCV实现图像之间的模板匹配
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Union, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class MatchMethod(Enum):
    """模板匹配方法"""
    SQDIFF = cv2.TM_SQDIFF  # 平方差匹配
    SQDIFF_NORMED = cv2.TM_SQDIFF_NORMED  # 归一化平方差匹配
    CCORR = cv2.TM_CCORR  # 相关匹配
    CCORR_NORMED = cv2.TM_CCOEFF_NORMED  # 归一化相关匹配
    CCOEFF = cv2.TM_CCOEFF  # 相关系数匹配
    CCOEFF_NORMED = cv2.TM_CCOEFF_NORMED  # 归一化相关系数匹配

@dataclass
class MatchResult:
    """模板匹配结果"""
    x: int  # 匹配位置的左上角x坐标
    y: int  # 匹配位置的左上角y坐标
    width: int  # 匹配区域的宽度
    height: int  # 匹配区域的高度
    confidence: float  # 匹配置信度
    center: Tuple[int, int]  # 匹配区域的中心点
    method: str  # 使用的匹配方法

class TemplateMatching:
    """模板匹配类"""

    def __init__(self):
        self.default_method = MatchMethod.CCOEFF_NORMED
        self.default_threshold = 0.8

    def _load_image(self, image: Union[np.ndarray, str]) -> np.ndarray:
        """加载图像"""
        if isinstance(image, str):
            img = cv2.imread(image)
            if img is None:
                raise ValueError(f"无法读取图像文件: {image}")
            return img
        else:
            return image.copy()

    def find_template(self, template: Union[np.ndarray, str],
                     source: Union[np.ndarray, str],
                     threshold: float = 0.8) -> Optional[MatchResult]:
        """在源图像中查找模板"""
        try:
            template_img = self._load_image(template)
            source_img = self._load_image(source)

            # 执行模板匹配
            result = cv2.matchTemplate(source_img, template_img, self.default_method.value)

            # 找到最佳匹配位置
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # CCOEFF_NORMED方法值越大越好
            if max_val >= threshold:
                template_height, template_width = template_img.shape[:2]
                return MatchResult(
                    x=max_loc[0],
                    y=max_loc[1],
                    width=template_width,
                    height=template_height,
                    confidence=float(max_val),
                    center=(max_loc[0] + template_width // 2, max_loc[1] + template_height // 2),
                    method=self.default_method.name
                )

            return None

        except Exception as e:
            print(f"模板匹配失败: {e}")
            return None

    def find_all_templates(self, template: Union[np.ndarray, str],
                          source: Union[np.ndarray, str],
                          threshold: float = 0.8) -> List[MatchResult]:
        """在源图像中查找所有匹配的模板"""
        try:
            template_img = self._load_image(template)
            source_img = self._load_image(source)

            # 执行模板匹配
            result = cv2.matchTemplate(source_img, template_img, self.default_method.value)

            # 创建掩码
            mask = result >= threshold

            # 查找所有匹配点
            locations = np.where(mask)
            matches = []

            template_height, template_width = template_img.shape[:2]

            for pt in zip(*locations[::-1]):
                confidence = float(result[pt[1], pt[0]])
                matches.append(MatchResult(
                    x=pt[0],
                    y=pt[1],
                    width=template_width,
                    height=template_height,
                    confidence=confidence,
                    center=(pt[0] + template_width // 2, pt[1] + template_height // 2),
                    method=self.default_method.name
                ))

            # 按置信度排序
            matches.sort(key=lambda x: x.confidence, reverse=True)

            return matches

        except Exception as e:
            print(f"多模板匹配失败: {e}")
            return []