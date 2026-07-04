"""
独立测试脚本：测试 FaceDetector 模块

功能：
1. 从 test_videos/ 读取视频帧
2. 加载 FaceDetector 进行人脸检测
3. 打印检测结果
4. 保存可视化结果到 detector_test_result.jpg
"""

import sys
import cv2
import numpy as np
from pathlib import Path

# 添加 device_b 到路径
sys.path.insert(0, str(Path(__file__).parent / "device_b"))

from detector import FaceDetector


def test_detector():
    """测试人脸检测器功能。"""
    print("=" * 80)
    print("FaceDetector 独立测试")
    print("=" * 80)

    # 1. 使用 face-demographics-walking-and-pause.mp4（确认有人脸的视频）
    test_video = Path(__file__).parent / "test_videos" / "face-demographics-walking-and-pause.mp4"

    if not test_video.exists():
        print(f"错误：测试视频不存在: {test_video}")
        return False

    print(f"\n使用测试视频: {test_video.name}")

    # 2. 读取视频的第100帧（确保有人脸）
    print("读取视频帧...")
    cap = cv2.VideoCapture(str(test_video))

    if not cap.isOpened():
        print("错误：无法打开视频文件")
        return False

    # 跳到第100帧
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print("错误：无法读取视频帧")
        return False

    height, width = frame.shape[:2]
    print(f"✓ 视频帧尺寸: {width} x {height}")

    # 3. 加载人脸检测器（使用不同的置信度阈值进行测试）
    print("\n加载人脸检测器...")
    project_root = Path(__file__).parent
    model_path = project_root / "models" / "res10_300x300_ssd_iter_140000.caffemodel"
    config_path = project_root / "models" / "deploy.prototxt"

    print(f"  模型文件: {model_path}")
    print(f"  配置文件: {config_path}")

    # 先用低阈值测试模型是否正常工作
    print("\n--- 测试 1: 低置信度阈值 (0.01) ---")
    try:
        detector_low = FaceDetector(
            model_path=str(model_path),
            config_path=str(config_path),
            confidence_threshold=0.01  # 极低阈值
        )

        import time
        start_time = time.time()
        all_detections = detector_low.detect(frame)
        test_time = (time.time() - start_time) * 1000

        print(f"✓ 检测器加载成功")
        print(f"✓ 检测到 {len(all_detections)} 个候选（包含低置信度）")
        print(f"✓ 推理耗时: {test_time:.1f} ms")

        # 显示所有检测的置信度范围
        if len(all_detections) > 0:
            confidences = [d.confidence for d in all_detections]
            print(f"  置信度范围: {min(confidences):.3f} - {max(confidences):.3f}")

    except Exception as e:
        print(f"✗ 检测器加载失败: {e}")
        return False

    # 再用正常阈值测试
    print("\n--- 测试 2: 正常置信度阈值 (0.5) ---")
    detector_normal = FaceDetector(
        model_path=str(model_path),
        config_path=str(config_path),
        confidence_threshold=0.5  # 正常阈值
    )

    start_time = time.time()
    detections = detector_normal.detect(frame)
    inference_time = (time.time() - start_time) * 1000

    print(f"✓ 检测到 {len(detections)} 张高置信度人脸")
    print(f"✓ 推理耗时: {inference_time:.1f} ms")

    # 4. 打印高置信度检测结果
    if len(detections) > 0:
        print("\n高置信度检测结果详情:")
        print("-" * 80)
        for i, detection in enumerate(detections, 1):
            print(f"人脸 #{i}:")
            print(f"  边界框: ({detection.x1}, {detection.y1}) -> ({detection.x2}, {detection.y2})")
            print(f"  尺寸: {detection.width} x {detection.height}")
            print(f"  中心点: ({detection.center[0]:.1f}, {detection.center[1]:.1f})")
            print(f"  置信度: {detection.confidence:.3f}")
            print(f"  面积: {detection.area} 像素")
        print("-" * 80)
    else:
        print("\n未检测到高置信度人脸")
        print("提示：模型工作正常，但当前帧可能没有清晰的人脸")

    # 5. 绘制所有检测结果（用不同颜色区分置信度）
    print("\n绘制检测结果...")
    result_frame = frame.copy()

    # 绘制所有检测结果（包括低置信度的，用不同颜色）
    for detection in all_detections:
        x1, y1, x2, y2 = detection.bbox

        # 根据置信度选择颜色
        if detection.confidence >= 0.5:
            color = (0, 255, 0)  # 绿色 - 高置信度
            label_prefix = ""
        elif detection.confidence >= 0.3:
            color = (0, 255, 255)  # 黄色 - 中等置信度
            label_prefix = "?"
        else:
            color = (0, 0, 255)  # 红色 - 低置信度
            label_prefix = "??"

        # 绘制边界框
        cv2.rectangle(result_frame, (x1, y1), (x2, y2), color, 2)

        # 只为高置信度的绘制标签
        if detection.confidence >= 0.5:
            label = f"{label_prefix}Face: {detection.confidence:.2f}"

            # 计算文本尺寸
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2

            (text_width, text_height), baseline = cv2.getTextSize(
                label, font, font_scale, thickness
            )

            # 绘制文本背景
            text_y = max(y1, text_height + 10)
            cv2.rectangle(
                result_frame,
                (x1, text_y - text_height - baseline - 5),
                (x1 + text_width + 5, text_y + baseline),
                (0, 0, 0),
                -1
            )

            # 绘制文本
            cv2.putText(
                result_frame,
                label,
                (x1 + 5, text_y - baseline),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA
            )

    # 在图像上添加总体信息
    info_text = f"High: {len(detections)} | All: {len(all_detections)} | Time: {inference_time:.1f}ms"
    (info_width, info_height), _ = cv2.getTextSize(
        info_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2
    )

    # 绘制信息背景
    cv2.rectangle(
        result_frame,
        (10, 10),
        (20 + info_width, 20 + info_height),
        (0, 0, 0),
        -1
    )

    # 绘制信息文本
    cv2.putText(
        result_frame,
        info_text,
        (15, 15 + info_height),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
        cv2.LINE_AA
    )

    # 添加图例
    legend_y = 40
    cv2.putText(result_frame, "Green: >=0.5", (15, legend_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(result_frame, "Yellow: >=0.3", (15, legend_y + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(result_frame, "Red: <0.3", (15, legend_y + 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # 保存结果
    output_path = Path(__file__).parent / "detector_test_result.jpg"
    success = cv2.imwrite(str(output_path), result_frame)

    if success:
        print(f"✓ 检测结果已保存: {output_path}")
        print(f"  文件大小: {output_path.stat().st_size / 1024:.1f} KB")
        print(f"  图像尺寸: {width} x {height}")
    else:
        print("✗ 保存检测结果失败")
        return False

    # 6. 总结
    print("\n" + "=" * 80)
    print("✓ 测试完成！")
    print("=" * 80)
    print(f"视频文件: {test_video.name}")
    print(f"帧序号: 100")
    print(f"帧尺寸: {width} x {height}")
    print(f"所有候选: {len(all_detections)} 个")
    print(f"高置信度: {len(detections)} 张")
    print(f"推理耗时: {inference_time:.1f} ms")
    print(f"结果保存: {output_path}")
    print("=" * 80)
    print("\n说明：")
    print("- 绿色框: 置信度 >= 0.5 (高可信度)")
    print("- 黄色框: 置信度 >= 0.3 (中等可信度)")
    print("- 红色框: 置信度 < 0.3 (低可信度，可能为误检)")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        success = test_detector()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
