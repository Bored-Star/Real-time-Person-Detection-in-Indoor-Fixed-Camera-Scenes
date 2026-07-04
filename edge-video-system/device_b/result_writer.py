"""
结果可视化模块。

职责：在图像上绘制检测结果，保存标注后的图像。

输入：图像帧 + 检测结果列表
输出：标注后的图像文件

设计决策：
- 使用OpenCV绘制边界框和文本
- 支持自定义颜色和样式
- 文件名包含时间戳或帧序号
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional
from datetime import datetime


class ResultWriter:
    """结果写入器类，负责绘制检测结果并保存图像。"""

    # 颜色定义 (BGR格式)
    BOX_COLOR = (0, 255, 0)  # 绿色
    TEXT_COLOR = (255, 255, 255)  # 白色
    TEXT_BG_COLOR = (0, 0, 0)  # 黑色背景

    def __init__(self,
                 output_dir: str = "output_frames",
                 box_color: tuple = None,
                 text_color: tuple = None,
                 line_thickness: int = 2):
        """
        初始化结果写入器。

        Args:
            output_dir: 输出目录路径
            box_color: 边界框颜色 (B, G, R)
            text_color: 文本颜色 (B, G, R)
            line_thickness: 线条粗细
        """
        self.output_dir = Path(output_dir)
        self.box_color = box_color if box_color is not None else self.BOX_COLOR
        self.text_color = text_color if text_color is not None else self.TEXT_COLOR
        self.line_thickness = line_thickness

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def draw_detections(self,
                       frame: np.ndarray,
                       tracked_detections: List,
                       frame_number: int = 0,
                       total_count: int = 0,
                       active_count: int = 0) -> np.ndarray:
        """
        在图像上绘制检测结果（包含track_id）。

        Args:
            frame: 输入图像（BGR格式）
            tracked_detections: 跟踪检测结果列表（TrackedDetection对象）
            frame_number: 帧序号（用于绘制）
            total_count: 累计人流量
            active_count: 当前活跃跟踪目标数

        Returns:
            标注后的图像
        """
        if frame is None or frame.size == 0:
            raise ValueError("输入帧为空")

        # 复制图像（避免修改原图）
        annotated = frame.copy()

        # 绘制每个跟踪检测结果
        for tracked_det in tracked_detections:
            detection = tracked_det.detection
            track_id = tracked_det.track_id

            # 获取边界框坐标
            x1, y1, x2, y2 = detection.bbox

            # 绘制边界框
            cv2.rectangle(
                annotated,
                (x1, y1),
                (x2, y2),
                self.box_color,
                self.line_thickness
            )

            # 准备标签文本（包含track_id和置信度）
            label = f"ID:{track_id} {detection.confidence:.2f}"

            # 计算文本尺寸
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_thickness = 1

            (text_width, text_height), baseline = cv2.getTextSize(
                label,
                font,
                font_scale,
                font_thickness
            )

            # 绘制文本背景
            text_y = max(y1, text_height + 10)
            cv2.rectangle(
                annotated,
                (x1, text_y - text_height - baseline - 5),
                (x1 + text_width + 5, text_y + baseline),
                self.TEXT_BG_COLOR,
                -1  # 填充
            )

            # 绘制文本
            cv2.putText(
                annotated,
                label,
                (x1 + 5, text_y - baseline),
                font,
                font_scale,
                self.text_color,
                font_thickness,
                cv2.LINE_AA
            )

        # 在左上角绘制统计信息
        info_text = f"Frame: {frame_number} | Active: {active_count} | Total: {total_count}"
        (info_width, info_height), _ = cv2.getTextSize(
            info_text,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            2
        )

        # 绘制信息背景
        cv2.rectangle(
            annotated,
            (10, 10),
            (20 + info_width, 20 + info_height),
            (0, 0, 0),
            -1
        )

        # 绘制信息文本
        cv2.putText(
            annotated,
            info_text,
            (15, 15 + info_height),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )

        return annotated

    def save_frame(self,
                  frame: np.ndarray,
                  frame_number: int = 0,
                  use_timestamp: bool = False) -> Path:
        """
        保存图像帧。

        Args:
            frame: 图像帧（BGR格式）
            frame_number: 帧序号
            use_timestamp: 是否使用时间戳而非帧序号

        Returns:
            保存的文件路径
        """
        if frame is None or frame.size == 0:
            raise ValueError("输入帧为空")

        # 生成文件名
        if use_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"frame_{timestamp}.jpg"
        else:
            filename = f"frame_{frame_number:06d}.jpg"

        output_path = self.output_dir / filename

        # 保存图像
        success = cv2.imwrite(str(output_path), frame)
        if not success:
            raise RuntimeError(f"保存图像失败: {output_path}")

        return output_path

    def process_and_save(self,
                       frame: np.ndarray,
                       tracked_detections: List,
                       frame_number: int = 0,
                       total_count: int = 0,
                       active_count: int = 0,
                       use_timestamp: bool = False) -> Path:
        """
        处理图像并保存（绘制 + 保存）。

        Args:
            frame: 原始图像帧
            tracked_detections: 跟踪检测结果列表（TrackedDetection对象）
            frame_number: 帧序号
            total_count: 累计人流量
            active_count: 当前活跃跟踪目标数
            use_timestamp: 是否使用时间戳

        Returns:
            保存的文件路径
        """
        # 绘制检测结果
        annotated_frame = self.draw_detections(
            frame, tracked_detections, frame_number, total_count, active_count
        )

        # 保存图像
        output_path = self.save_frame(annotated_frame, frame_number, use_timestamp)

        return output_path

    def log_detections(self, detections: List, frame_number: int):
        """
        打印检测结果日志。

        Args:
            detections: 检测结果列表
            frame_number: 帧序号
        """
        num_faces = len(detections)
        print(f"Frame {frame_number:06d}: 检测到 {num_faces} 张人脸")

        if num_faces > 0:
            for i, detection in enumerate(detections):
                print(f"  人脸 #{i+1}: bbox={detection.bbox}, 置信度={detection.confidence:.3f}")


if __name__ == "__main__":
    """
    测试代码：使用随机图像测试ResultWriter
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from device_b.detector import Detection, FaceDetector

    print("=" * 60)
    print("ResultWriter 模块测试")
    print("=" * 60)

    # 创建测试图像
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    print(f"✓ 创建测试图像: {test_frame.shape}")

    # 创建模拟检测结果
    detections = [
        Detection(x1=100, y1=100, x2=200, y2=200, confidence=0.95),
        Detection(x1=300, y1=150, x2=400, y2=250, confidence=0.87),
        Detection(x1=500, y1=80, x2=600, y2=180, confidence=0.76),
    ]
    print(f"✓ 创建 {len(detections)} 个模拟检测结果")

    # 创建ResultWriter
    writer = ResultWriter(output_dir="test_output")
    print(f"✓ 创建ResultWriter，输出目录: test_output")

    # 处理并保存
    output_path = writer.process_and_save(test_frame, detections, frame_number=1)
    print(f"✓ 已保存标注图像: {output_path}")

    # 打印日志
    writer.log_detections(detections, frame_number=1)

    print("\n" + "=" * 60)
    print("✓ 测试完成！")
    print("=" * 60)
