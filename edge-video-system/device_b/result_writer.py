"""
结果输出模块。

职责：保存标注后的帧图像，打印统计日志，输出报警信息。

输入：
- annotated_frame: 标注后的图像
- tracked_objects: 跟踪对象列表
- alerts: 报警列表
- frame_id: 帧序号

输出：
- 保存图像文件到 output_frames/ 目录
- 打印统计信息到控制台

设计决策：
- 按帧序号命名保存的图像（frame_{id}.jpg）
- 定期输出统计摘要（如每10帧）
- 报警信息立即输出并高亮显示
- 支持日志级别控制
"""

import cv2
import os
from datetime import datetime


class ResultWriter:
    """结果输出器类。"""

    def __init__(self, output_dir: str = "output_frames", save_frames: bool = True,
                 log_interval: int = 10):
        """
        初始化输出器。

        Args:
            output_dir: 输出目录路径
            save_frames: 是否保存帧图像
            log_interval: 日志输出间隔（帧数）
        """
        pass

    def write_frame(self, frame: np.ndarray, frame_id: int):
        """
        保存标注后的帧。

        Args:
            frame: 标注后的图像
            frame_id: 帧序号
        """
        pass

    def log_statistics(self, frame_id: int, person_count: dict, detections_count: int):
        """
        打印统计日志。

        Args:
            frame_id: 当前帧序号
            person_count: 人流统计 {'entered', 'left', 'current'}
            detections_count: 当前帧检测数量
        """
        pass

    def log_alert(self, alert: dict, frame_id: int):
        """
        打印报警信息。

        Args:
            alert: 报警信息字典
            frame_id: 帧序号
        """
        pass

    def format_summary(self, person_count: dict) -> str:
        """
        格式化统计摘要。

        Args:
            person_count: 人流统计字典

        Returns:
            str: 格式化的摘要字符串
        """
        pass

    def close(self):
        """关闭输出器，打印最终统计。"""
        pass
