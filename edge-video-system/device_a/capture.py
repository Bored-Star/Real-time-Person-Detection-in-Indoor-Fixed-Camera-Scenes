"""
视频采集模块。

职责：从视频文件中读取帧数据，支持帧采样控制（FPS控制）。

输入：
- video_path: 视频文件路径
- sample_fps: 采样帧率（如5表示每秒提取5帧）

输出：
- yield frames: 逐帧返回采样的图像数据（numpy数组）

设计决策：
- 使用OpenCV VideoCapture读取视频
- 支持帧采样以减少传输量和计算量
- 自动处理视频结束和读取错误
"""

import cv2
import numpy as np


def VideoCapture(video_path: str, sample_fps: int = 5):
    """
    视频采集器类。

    Args:
        video_path: 视频文件路径
        sample_fps: 采样帧率（默认5fps）

    Yields:
        numpy.ndarray: 采样的图像帧
    """
    pass


def sample_frames(cap, target_fps: int):
    """
    按目标FPS采样视频帧。

    Args:
        cap: cv2.VideoCapture对象
        target_fps: 目标采样帧率

    Yields:
        numpy.ndarray: 采样后的图像帧
    """
    pass
