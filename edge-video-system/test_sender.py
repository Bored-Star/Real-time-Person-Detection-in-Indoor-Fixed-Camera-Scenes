"""
测试脚本：测试 FrameSender 模块

功能：
1. 生成或读取一张测试图片
2. 连接到指定服务器
3. 发送10帧（每帧间隔0.5秒）
4. 打印发送状态
"""

import sys
import time
import cv2
import numpy as np
from pathlib import Path

# 添加 device_a 到路径
sys.path.insert(0, str(Path(__file__).parent / "device_a"))

from sender import FrameSender
from preprocess import FramePreprocessor


def create_test_image(width: int = 640, height: int = 480) -> np.ndarray:
    """
    创建一个测试图像（带颜色渐变的测试图案）。

    Args:
        width: 图像宽度
        height: 图像高度

    Returns:
        BGR格式的测试图像
    """
    # 创建一个带有渐变的测试图像
    image = np.zeros((height, width, 3), dtype=np.uint8)

    # 创建颜色渐变
    for y in range(height):
        for x in range(width):
            # 红色通道：水平渐变
            image[y, x, 2] = int(255 * x / width)
            # 绿色通道：垂直渐变
            image[y, x, 1] = int(255 * y / height)
            # 蓝色通道：对角线渐变
            image[y, x, 0] = int(255 * (x + y) / (width + height))

    # 添加文字标识
    font = cv2.FONT_HERSHEY_SIMPLEX
    text = f"Test Frame {width}x{height}"
    cv2.putText(image, text, (50, 50), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

    # 添加帧号区域（后面会用）
    cv2.rectangle(image, (50, 80), (200, 130), (255, 255, 255), 2)

    return image


def test_sender(host: str, port: int, num_frames: int = 10):
    """
    测试发送器功能。

    Args:
        host: 服务器地址
        port: 服务器端口
        num_frames: 发送帧数
    """
    print("=" * 80)
    print("测试 FrameSender 模块")
    print("=" * 80)
    print(f"\n目标服务器: {host}:{port}")
    print(f"发送帧数: {num_frames}")
    print(f"发送间隔: 0.5 秒")

    # 创建测试图像
    print("\n创建测试图像...")
    test_image = create_test_image(640, 480)
    print(f"✓ 测试图像尺寸: {test_image.shape}")

    # 创建预处理器（压缩为JPEG）
    preprocessor = FramePreprocessor(
        target_size=(640, 480),
        jpeg_quality=85
    )

    # 压缩为JPEG
    jpeg_data = preprocessor.process(test_image)
    print(f"✓ JPEG压缩后大小: {len(jpeg_data)} 字节")

    # 创建发送器
    sender = FrameSender(
        server_host=host,
        server_port=port,
        timeout=10.0
    )

    print("\n开始发送...")
    print("-" * 80)

    try:
        # 连接服务器
        if not sender.connect():
            print(f"✗ 无法连接到服务器: {host}:{port}")
            return False

        print(f"✓ 已连接到服务器: {host}:{port}")
        print()

        # 发送多帧
        for i in range(1, num_frames + 1):
            # 在图像上标记帧号
            frame_image = test_image.copy()
            cv2.putText(
                frame_image,
                f"Frame #{i}",
                (60, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                2,
                cv2.LINE_AA
            )

            # 压缩为JPEG
            jpeg_bytes = preprocessor.process(frame_image)

            # 发送帧
            success = sender.send_frame(jpeg_bytes)

            if success:
                print(f"✓ 已发送第 {i:2d} 帧，大小 {len(jpeg_bytes):6,} 字节")
            else:
                print(f"✗ 发送第 {i:2d} 帧失败")
                break

            # 间隔
            if i < num_frames:
                time.sleep(0.5)

        print("-" * 80)
        print(f"\n✓ 测试完成！成功发送 {num_frames} 帧")
        return True

    except KeyboardInterrupt:
        print("\n\n用户中断")
        return False
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 断开连接
        sender.disconnect()
        print("连接已关闭")


def main():
    """主函数：解析命令行参数并运行测试。"""
    import argparse

    parser = argparse.ArgumentParser(description="测试 FrameSender 模块")
    parser.add_argument("--host", default="127.0.0.1", help="服务器地址（默认：127.0.0.1）")
    parser.add_argument("--port", type=int, default=6006, help="服务器端口（默认：6006）")
    parser.add_argument("--frames", type=int, default=10, help="发送帧数（默认：10）")

    args = parser.parse_args()

    # 运行测试
    success = test_sender(args.host, args.port, args.frames)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
