"""
测试脚本：测试 FrameReceiver 模块

功能：
1. 启动TCP服务器监听
2. 接受客户端连接
3. 接收多帧JPEG数据
4. 保存每帧为独立的JPEG文件
5. 打印接收状态
"""

import sys
import cv2
import numpy as np
from pathlib import Path

# 添加 device_b 到路径
sys.path.insert(0, str(Path(__file__).parent / "device_b"))

from receiver import FrameReceiver


def test_receiver(host: str, port: int, max_frames: int = 0):
    """
    测试接收器功能。

    Args:
        host: 绑定地址
        port: 绑定端口
        max_frames: 最大接收帧数，0表示无限接收
    """
    print("=" * 80)
    print("测试 FrameReceiver 模块")
    print("=" * 80)
    print(f"\n绑定地址: {host}:{port}")
    print(f"最大接收帧数: {max_frames if max_frames > 0 else '无限制'}")

    # 创建输出目录
    output_dir = Path(__file__).parent / "received_frames"
    output_dir.mkdir(exist_ok=True)
    print(f"输出目录: {output_dir}")

    # 清空输出目录
    for file in output_dir.glob("received_frame_*.jpg"):
        file.unlink()
    print("已清空输出目录")

    print("\n启动服务器...")
    print("-" * 80)

    try:
        # 创建接收器并启动服务器
        with FrameReceiver(bind_host=host, bind_port=port) as receiver:
            print(f"✓ 服务器已启动，监听 {host}:{port}")

            # 等待客户端连接
            client_socket = receiver.accept_client()
            if client_socket is None:
                print("✗ 无法接受客户端连接")
                return False

            print()

            # 接收帧流
            frame_count = 0
            for frame_data in receiver.receive_frames_stream(client_socket):
                frame_count += 1

                # 打印接收信息
                print(f"✓ 收到第 {frame_count:2d} 帧，大小 {len(frame_data):6,} 字节")

                # 保存为JPEG文件
                output_path = output_dir / f"received_frame_{frame_count:03d}.jpg"

                try:
                    # 直接保存JPEG字节
                    with open(output_path, 'wb') as f:
                        f.write(frame_data)

                    print(f"  已保存: {output_path.name}")

                    # 验证JPEG数据并获取图像信息
                    frame_array = cv2.imdecode(
                        np.frombuffer(frame_data, dtype=np.uint8),
                        cv2.IMREAD_COLOR
                    )

                    # 显示帧信息
                    if frame_array is not None:
                        h, w = frame_array.shape[:2]
                        print(f"  图像尺寸: {w} x {h}")
                    else:
                        print(f"  警告: JPEG解码失败，但已保存原始字节")

                except Exception as e:
                    print(f"  ✗ 保存失败: {e}")

                # 检查是否达到最大帧数
                if max_frames > 0 and frame_count >= max_frames:
                    print(f"\n已达到最大帧数限制 ({max_frames})")
                    break

            print("-" * 80)
            print(f"\n✓ 测试完成！共接收 {frame_count} 帧")
            print(f"✓ 所有帧已保存到: {output_dir}")

            return frame_count > 0

    except KeyboardInterrupt:
        print("\n\n用户中断")
        return False
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数：解析命令行参数并运行测试。"""
    import argparse

    parser = argparse.ArgumentParser(description="测试 FrameReceiver 模块")
    parser.add_argument("--host", default="0.0.0.0", help="绑定地址（默认：0.0.0.0）")
    parser.add_argument("--port", type=int, default=6006, help="绑定端口（默认：6006）")
    parser.add_argument("--max-frames", type=int, default=0, help="最大接收帧数（默认：0=无限制）")

    args = parser.parse_args()

    # 运行测试
    success = test_receiver(args.host, args.port, args.max_frames)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
