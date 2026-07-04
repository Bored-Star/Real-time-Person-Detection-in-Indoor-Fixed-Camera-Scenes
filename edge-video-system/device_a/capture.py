"""
视频采集模块。

职责：从视频文件中读取帧，支持帧率控制。

输入：视频文件路径
输出：原始帧（numpy数组）

设计决策：
- 使用OpenCV VideoCapture读取视频
- 支持按原始帧率或降采样读取
- 处理视频结束和读取异常情况
"""

import cv2
import numpy as np
from typing import Generator, Optional


class VideoCapture:
    """视频采集器类，负责从视频文件读取帧。"""

    def __init__(self, video_path: str, target_fps: Optional[int] = None):
        """
        初始化视频采集器。

        Args:
            video_path: 视频文件路径
            target_fps: 目标帧率，None表示使用原始帧率
        """
        self.video_path = video_path
        self.target_fps = target_fps
        self.cap = None
        self.original_fps = None
        self.frame_size = None
        self.frame_interval = None  # 跳帧间隔

    def __enter__(self):
        """支持with语句的上下文管理入口。"""
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise IOError(f"无法打开视频文件: {self.video_path}")

        # 获取原始视频属性
        self.original_fps = self.cap.get(cv2.CAP_PROP_FPS)
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_size = (width, height)

        # 计算跳帧间隔
        if self.target_fps is not None and self.original_fps > 0:
            self.frame_interval = int(round(self.original_fps / self.target_fps))
            if self.frame_interval < 1:
                self.frame_interval = 1
        else:
            self.frame_interval = 1

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持with语句的上下文管理出口，释放资源。"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        return False  # 不抑制异常

    def read_frame(self) -> Optional[np.ndarray]:
        """
        读取下一帧。

        Returns:
            帧数据（BGR格式），读取失败或结束时返回None
        """
        if self.cap is None or not self.cap.isOpened():
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        return frame

    def get_original_fps(self) -> float:
        """
        获取视频原始帧率。

        Returns:
            原始帧率（FPS）
        """
        return self.original_fps if self.original_fps is not None else 0.0

    def get_frame_size(self) -> tuple[int, int]:
        """
        获取视频帧尺寸。

        Returns:
            (width, height) 元组
        """
        return self.frame_size if self.frame_size is not None else (0, 0)

    def frames_generator(self) -> Generator[np.ndarray, None, None]:
        """
        生成器函数，持续产生帧直到视频结束。

        Yields:
            帧数据（BGR格式）
        """
        if self.cap is None or not self.cap.isOpened():
            return

        frame_count = 0
        while True:
            ret, frame = self.cap.read()
            if not ret:
                # 视频结束或读取失败
                break

            # 根据帧间隔跳帧
            if self.frame_interval > 1:
                frame_count += 1
                if frame_count % self.frame_interval != 0:
                    continue

            yield frame
