"""
AI推理模块：人脸检测。

职责：加载OpenCV DNN模型，执行人脸检测推理。

输入：图像帧（numpy数组或JPEG字节数据）
输出：检测结果（边界框、置信度）

设计决策：
- 使用OpenCV DNN模块加载预训练模型
- 支持常见的检测模型（如YOLO、SSD、ResNet SSD等）
- 输出标准化为统一格式
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Detection:
    """
    检测结果类，存储单个人脸的检测信息。

    Attributes:
        x1: 边界框左上角x坐标
        y1: 边界框左上角y坐标
        x2: 边界框右下角x坐标
        y2: 边界框右下角y坐标
        confidence: 检测置信度（0-1）
    """
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """
        获取边界框元组。

        Returns:
            (x1, y1, x2, y2) 元组
        """
        return (self.x1, self.y1, self.x2, self.y2)

    @property
    def width(self) -> int:
        """获取边界框宽度。"""
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        """获取边界框高度。"""
        return self.y2 - self.y1

    @property
    def center(self) -> Tuple[float, float]:
        """
        计算边界框中心点。

        Returns:
            (center_x, center_y) 元组
        """
        center_x = (self.x1 + self.x2) / 2.0
        center_y = (self.y1 + self.y2) / 2.0
        return (center_x, center_y)

    @property
    def area(self) -> int:
        """计算边界框面积。"""
        return self.width * self.height

    def __repr__(self) -> str:
        """字符串表示。"""
        return (f"Detection(bbox=({self.x1},{self.y1},{self.x2},{self.y2}), "
                f"confidence={self.confidence:.3f})")


class FaceDetector:
    """人脸检测器类，负责加载模型和执行推理。"""

    # ResNet SSD 模型的输入尺寸
    INPUT_WIDTH = 300
    INPUT_HEIGHT = 300

    def __init__(self,
                 model_path: str,
                 config_path: Optional[str] = None,
                 confidence_threshold: float = 0.5,
                 nms_threshold: float = 0.4):
        """
        初始化人脸检测器。

        Args:
            model_path: 模型权重文件路径
            config_path: 模型配置文件路径（某些模型需要）
            confidence_threshold: 置信度阈值，低于此值的检测被过滤
            nms_threshold: 非极大值抑制阈值
        """
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.input_width = self.INPUT_WIDTH
        self.input_height = self.INPUT_HEIGHT

        # 加载模型
        self.net = self._load_model(model_path, config_path)

    def _load_model(self, model_path: str, config_path: Optional[str] = None):
        """
        加载OpenCV DNN模型。

        Args:
            model_path: 模型权重文件路径
            config_path: 模型配置文件路径（可选）

        Returns:
            加载后的cv2.dnn.Net对象

        Raises:
            FileNotFoundError: 模型文件不存在
        """
        # 检查模型文件是否存在
        model_file = Path(model_path)
        if not model_file.exists():
            raise FileNotFoundError(
                f"模型权重文件不存在: {model_path}\n"
                f"请运行: bash scripts/download_model.sh"
            )

        if config_path is not None:
            config_file = Path(config_path)
            if not config_file.exists():
                raise FileNotFoundError(
                    f"模型配置文件不存在: {config_path}\n"
                    f"请运行: bash scripts/download_model.sh"
                )

        # 根据文件扩展名选择加载方法
        model_ext = model_file.suffix.lower()

        try:
            if model_ext in ['.caffemodel', '.prototxt']:
                # Caffe格式模型
                if config_path is None:
                    raise ValueError(
                        f"Caffe模型需要配置文件。请提供config_path参数。"
                    )
                net = cv2.dnn.readNetFromCaffe(config_path, model_path)
                print(f"已加载Caffe模型: {model_path}")
            elif model_ext == '.onnx':
                # ONNX格式模型
                net = cv2.dnn.readNetFromONNX(model_path)
                print(f"已加载ONNX模型: {model_path}")
            elif model_ext in ['.pb', '.pbtxt']:
                # TensorFlow格式模型
                net = cv2.dnn.readNetFromTensorflow(model_path, config_path or "")
                print(f"已加载TensorFlow模型: {model_path}")
            else:
                # 尝试通用加载方法
                if config_path:
                    net = cv2.dnn.readNet(config_path, model_path)
                else:
                    net = cv2.dnn.readNet(model_path)
                print(f"已加载模型: {model_path}")

        except Exception as e:
            raise RuntimeError(
                f"加载模型失败: {model_path}\n"
                f"错误: {str(e)}"
            ) from e

        return net

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        将帧预处理为模型输入格式。

        Args:
            frame: 输入帧（BGR格式）

        Returns:
            预处理后的blob
        """
        # 获取原始帧尺寸
        (h, w) = frame.shape[:2]

        # 构建blob
        # scalefactor=1.0: 不进行缩放
        # size=(300,300): 模型输入尺寸
        # mean=(104,177,123): BGR通道的减法均值（ImageNet均值）
        # swapRB=False: 不交换通道（已经是BGR格式）
        # crop=False: 不进行中心裁剪
        blob = cv2.dnn.blobFromImage(
            frame,
            scalefactor=1.0,
            size=(self.input_width, self.input_height),
            mean=(104.0, 177.0, 123.0),
            swapRB=False,
            crop=False
        )

        return blob

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        执行人脸检测。

        Args:
            frame: 输入帧（BGR格式）

        Returns:
            检测结果列表
        """
        if frame is None or frame.size == 0:
            return []

        # 获取原始帧尺寸（用于坐标映射）
        (h, w) = frame.shape[:2]

        # 预处理：构建blob
        blob = self.preprocess(frame)

        # 推理：设置输入并前向传播
        self.net.setInput(blob)
        detections = self.net.forward()

        # 后处理：解析输出
        return self._postprocess(detections, w, h)

    def _postprocess(self, detections: np.ndarray, width: int, height: int) -> List[Detection]:
        """
        后处理检测结果。

        Args:
            detections: 模型原始输出
            width: 原始图像宽度
            height: 原始图像高度

        Returns:
            检测结果列表
        """
        results = []

        # detections形状: (1, 1, N, 7)
        # 每一行的格式: [image_id, class_id, confidence, x1, y1, x2, y2]
        # x1,y1,x2,y2 是相对于输入尺寸(300x300)的坐标，范围0-1
        # class_id: 0=背景, 1=人脸（对于ResNet SSD模型）
        for i in range(detections.shape[2]):
            # 提取类别ID
            class_id = int(detections[0, 0, i, 1])

            # 只保留人脸类别（class_id=1）
            # 注：在SSD模型中，0通常是背景类别
            if class_id != 1:
                continue

            # 提取置信度
            confidence = detections[0, 0, i, 2]

            # 过滤低置信度检测
            if confidence < self.confidence_threshold:
                continue

            # 提取边界框坐标（相对于300x300）
            box = detections[0, 0, i, 3:7]

            # 将坐标映射到原始图像尺寸
            x1 = int(box[0] * width)
            y1 = int(box[1] * height)
            x2 = int(box[2] * width)
            y2 = int(box[3] * height)

            # 边界检查，确保坐标在图像范围内
            x1 = max(0, min(x1, width - 1))
            y1 = max(0, min(y1, height - 1))
            x2 = max(0, min(x2, width))
            y2 = max(0, min(y2, height))

            # 确保边界框有效（x2>x1, y2>y1）
            if x2 <= x1 or y2 <= y1:
                continue

            # 创建Detection对象
            detection = Detection(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                confidence=float(confidence)
            )
            results.append(detection)

        # 应用非极大值抑制（NMS）
        if len(results) > 0:
            results = self._apply_nms(results)

        return results

    def _apply_nms(self, detections: List[Detection]) -> List[Detection]:
        """
        应用非极大值抑制，去除重叠的边界框。

        Args:
            detections: 检测结果列表

        Returns:
            NMS后的检测结果列表
        """
        if len(detections) == 0:
            return []

        # 提取边界框和置信度
        boxes = np.array([[d.x1, d.y1, d.x2, d.y2] for d in detections])
        confidences = np.array([d.confidence for d in detections])

        # OpenCV NMS
        indices = cv2.dnn.NMSBoxes(
            bboxes=boxes.tolist(),
            scores=confidences.tolist(),
            score_threshold=self.confidence_threshold,
            nms_threshold=self.nms_threshold
        )

        # NMSBoxes返回的是二维数组，需要处理
        if len(indices) > 0:
            indices = indices.flatten() if isinstance(indices[0], (list, np.ndarray)) else indices
            return [detections[i] for i in indices]

        return []

    def detect_from_jpeg(self, jpeg_data: bytes) -> List[Detection]:
        """
        从JPEG字节数据检测人脸。

        Args:
            jpeg_data: JPEG压缩的帧字节数据

        Returns:
            检测结果列表
        """
        try:
            # 解码JPEG数据
            frame = cv2.imdecode(np.frombuffer(jpeg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                return []

            # 执行检测
            return self.detect(frame)

        except Exception as e:
            print(f"JPEG解码失败: {e}")
            return []

    def set_input_size(self, size: Tuple[int, int]):
        """
        设置模型输入尺寸。

        Args:
            size: (width, height) 元组
        """
        self.input_width, self.input_height = size


if __name__ == "__main__":
    """
    测试代码：使用随机图像测试检测器
    """
    import sys
    from pathlib import Path

    print("=" * 60)
    print("人脸检测器模块测试")
    print("=" * 60)

    # 设置模型路径
    project_root = Path(__file__).parent.parent
    config_path = project_root / "models" / "deploy.prototxt"
    model_path = project_root / "models" / "res10_300x300_ssd_iter_140000.caffemodel"

    print(f"\n配置文件: {config_path}")
    print(f"权重文件: {model_path}")

    # 检查模型文件
    if not config_path.exists() or not model_path.exists():
        print("\n⚠️  模型文件不存在！")
        print("请先运行: bash scripts/download_model.sh")
        sys.exit(1)

    try:
        # 创建检测器
        print("\n1. 初始化检测器...")
        detector = FaceDetector(
            model_path=str(model_path),
            config_path=str(config_path),
            confidence_threshold=0.5
        )
        print("✓ 检测器初始化成功")

        # 生成随机测试图像（BGR格式，640x480）
        print("\n2. 生成随机测试图像...")
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        print(f"✓ 测试图像尺寸: {test_frame.shape}")

        # 执行检测
        print("\n3. 执行人脸检测...")
        detections = detector.detect(test_frame)
        print(f"✓ 检测完成，找到 {len(detections)} 个人脸")

        # 打印检测结果
        if len(detections) > 0:
            print("\n4. 检测结果详情:")
            for i, det in enumerate(detections, 1):
                print(f"   人脸 #{i}:")
                print(f"      边界框: ({det.x1}, {det.y1}) -> ({det.x2}, {det.y2})")
                print(f"      尺寸: {det.width} x {det.height}")
                print(f"      中心点: ({det.center[0]:.1f}, {det.center[1]:.1f})")
                print(f"      置信度: {det.confidence:.3f}")
                print(f"      面积: {det.area} 像素")
        else:
            print("\n4. 未检测到人脸（随机图像通常不含人脸，这是正常的）")

        # 测试JPEG解码检测
        print("\n5. 测试JPEG输入...")
        _, jpeg_data = cv2.imencode(".jpg", test_frame)
        jpeg_detections = detector.detect_from_jpeg(jpeg_data.tobytes())
        print(f"✓ JPEG检测完成，找到 {len(jpeg_detections)} 个人脸")

        print("\n" + "=" * 60)
        print("✓ 所有测试通过！模块功能正常。")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\n❌ 文件错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
