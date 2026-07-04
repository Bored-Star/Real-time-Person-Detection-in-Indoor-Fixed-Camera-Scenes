"""
帧预处理模块。

职责：对原始帧进行采样、缩放和JPEG压缩。

输入：原始帧（numpy数组）
输出：JPEG压缩后的字节数据

设计决策：
- 支持调整分辨率以减少传输数据量
- 使用JPEG压缩平衡质量和带宽
- 可配置压缩质量参数
"""

import cv2
import numpy as np
from typing import Tuple, Optional


class FramePreprocessor:
    """帧预处理器类，负责帧的缩放和压缩。"""

    def __init__(self,
                 target_size: Optional[Tuple[int, int]] = (640, 480),
                 jpeg_quality: int = 85):
        """
        初始化帧预处理器。

        Args:
            target_size: 目标尺寸 (width, height)，None表示保持原尺寸
            jpeg_quality: JPEG压缩质量（0-100），越高质量越好但文件越大
        """
        self.target_size = target_size
        self.jpeg_quality = jpeg_quality

        # 验证参数
        if jpeg_quality < 0 or jpeg_quality > 100:
            raise ValueError(f"JPEG质量必须在0-100之间，当前值: {jpeg_quality}")

    def resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        调整帧尺寸。

        Args:
            frame: 原始帧（BGR格式）

        Returns:
            调整尺寸后的帧
        """
        if frame is None or frame.size == 0:
            raise ValueError("输入帧为空")

        # 如果目标尺寸为None，保持原尺寸
        if self.target_size is None:
            return frame

        target_width, target_height = self.target_size
        original_height, original_width = frame.shape[:2]

        # 如果已经是目标尺寸，直接返回
        if original_width == target_width and original_height == target_height:
            return frame

        # 计算缩放比例，保持宽高比
        width_ratio = target_width / original_width
        height_ratio = target_height / original_height
        scale = min(width_ratio, height_ratio)

        # 计算新的尺寸
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        # 调整尺寸
        resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

        # 如果需要，添加padding以达到目标尺寸（letterbox）
        if new_width != target_width or new_height != target_height:
            canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            # 计算padding位置（居中）
            y_offset = (target_height - new_height) // 2
            x_offset = (target_width - new_width) // 2
            canvas[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized
            return canvas

        return resized

    def compress_to_jpeg(self, frame: np.ndarray) -> bytes:
        """
        将帧压缩为JPEG格式。

        Args:
            frame: 输入帧（BGR格式）

        Returns:
            JPEG编码后的字节数据
        """
        if frame is None or frame.size == 0:
            raise ValueError("输入帧为空")

        # 使用cv2.imencode进行JPEG压缩
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        success, encoded = cv2.imencode('.jpg', frame, encode_param)

        if not success:
            raise RuntimeError("JPEG编码失败")

        return encoded.tobytes()

    def process(self, frame: np.ndarray) -> bytes:
        """
        完整的预处理流程：调整尺寸 + JPEG压缩。

        Args:
            frame: 原始帧

        Returns:
            压缩后的字节数据
        """
        # 先调整尺寸
        resized = self.resize_frame(frame)
        # 再压缩为JPEG
        return self.compress_to_jpeg(resized)
