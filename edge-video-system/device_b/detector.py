"""
AI推理模块。

职责：加载OpenCV DNN人脸检测模型，对输入帧进行人脸检测推理。

输入：
- frame_bytes: JPEG压缩的帧字节数据
- model_path: DNN模型文件路径
- config_path: 模型配置文件路径

输出：
- detections: 检测结果列表，每个检测包含 {bbox, confidence}
- decoded_frame: 解码后的图像（用于后续可视化）

设计决策：
- 使用OpenCV DNN模块加载预训练模型
- 支持Caffe和ONNX格式模型
- 后处理NMS（非极大值抑制）去除重复检测
- 推理在CPU上运行（边缘侧通常有足够算力）
"""

import cv2
import numpy as np


class FaceDetector:
    """人脸检测器类，封装OpenCV DNN推理逻辑。"""

    def __init__(self, model_path: str, config_path: str, confidence_threshold: float = 0.5,
                 nms_threshold: float = 0.4):
        """
        初始化检测器并加载模型。

        Args:
            model_path: 模型权重文件路径
            config_path: 模型配置文件路径
            confidence_threshold: 置信度阈值
            nms_threshold: NMS阈值
        """
        pass

    def load_model(self, model_path: str, config_path: str):
        """
        加载OpenCV DNN模型。

        Args:
            model_path: 模型权重文件
            config_path: 模型配置文件
        """
        pass

    def decode_frame(self, frame_bytes: bytes) -> np.ndarray:
        """
        解码JPEG字节数据为图像。

        Args:
            frame_bytes: JPEG压缩数据

        Returns:
            numpy.ndarray: 解码后的图像（BGR格式）
        """
        pass

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        预处理图像以适应模型输入。

        Args:
            frame: 输入图像

        Returns:
            numpy.ndarray: 预处理后的blob
        """
        pass

    def detect(self, frame_bytes: bytes) -> tuple:
        """
        执行人脸检测推理。

        Args:
            frame_bytes: JPEG压缩的帧数据

        Returns:
            tuple: (detections, decoded_frame)
                  - detections: 检测结果列表 [{'bbox': (x, y, w, h), 'confidence': float}, ...]
                  - decoded_frame: 解码后的图像
        """
        pass

    def postprocess(self, detections, frame_width: int, frame_height: int) -> list:
        """
        后处理：过滤置信度 + NMS。

        Args:
            detections: 原始检测结果
            frame_width: 图像宽度
            frame_height: 图像高度

        Returns:
            list: 后处理后的检测列表
        """
        pass

    def draw_detections(self, frame: np.ndarray, detections: list) -> np.ndarray:
        """
        在图像上绘制检测结果。

        Args:
            frame: 输入图像
            detections: 检测结果列表

        Returns:
            numpy.ndarray: 绘制后的图像
        """
        pass
