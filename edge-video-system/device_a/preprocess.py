"""
帧预处理模块。

职责：对采集的视频帧进行缩放和JPEG压缩，减少传输数据量。

输入：
- frame: 原始图像帧（numpy数组）
- target_size: 目标尺寸（宽x高），如(640, 480)
- jpeg_quality: JPEG压缩质量（1-100）

输出：
- jpeg_bytes: 压缩后的JPEG字节数据

设计决策：
- 统一缩放到固定尺寸，便于B端推理
- 使用JPEG压缩减少网络传输量
- 在压缩前保持适当的宽高比
"""

import cv2
import numpy as np


def resize_frame(frame: np.ndarray, target_size: tuple) -> np.ndarray:
    """
    调整图像尺寸。

    Args:
        frame: 输入图像帧
        target_size: 目标尺寸 (width, height)

    Returns:
        numpy.ndarray: 调整尺寸后的图像
    """
    pass


def compress_to_jpeg(frame: np.ndarray, quality: int = 75) -> bytes:
    """
    将图像压缩为JPEG字节数据。

    Args:
        frame: 输入图像帧
        quality: JPEG压缩质量（1-100）

    Returns:
        bytes: JPEG压缩后的字节数据
    """
    pass


def preprocess_frame(frame: np.ndarray, target_size: tuple = (640, 480),
                     jpeg_quality: int = 75) -> bytes:
    """
    完整的预处理流程：缩放 + JPEG压缩。

    Args:
        frame: 输入图像帧
        target_size: 目标尺寸 (width, height)
        jpeg_quality: JPEG压缩质量

    Returns:
        bytes: 预处理后的JPEG字节数据
    """
    pass
