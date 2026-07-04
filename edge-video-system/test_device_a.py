"""
测试脚本：验证 device_a 的 capture 和 preprocess 模块

功能：
1. 使用 VideoCapture 读取视频文件
2. 使用 FramePreprocessor 处理帧
3. 读取10帧并打印每帧的信息
4. 验证模块功能正常
"""

import sys
from pathlib import Path

# 添加 device_a 到路径
sys.path.insert(0, str(Path(__file__).parent / "device_a"))

from capture import VideoCapture
from preprocess import FramePreprocessor


def test_capture_and_preprocess(video_path: str, target_fps: int = None):
    """
    测试视频采集和预处理功能。

    Args:
        video_path: 视频文件路径
        target_fps: 目标帧率（可选）
    """
    print("=" * 80)
    print("测试视频采集和预处理模块")
    print("=" * 80)
    print(f"\n视频文件: {video_path}")
    print(f"目标帧率: {target_fps if target_fps else '使用原始帧率'}")

    # 创建预处理器
    preprocessor = FramePreprocessor(
        target_size=(640, 480),
        jpeg_quality=85
    )

    print(f"\n预处理器配置:")
    print(f"  目标尺寸: {preprocessor.target_size}")
    print(f"  JPEG质量: {preprocessor.jpeg_quality}")

    # 使用 with 语句测试资源管理
    print("\n开始读取视频...")
    print("-" * 80)

    try:
        with VideoCapture(video_path, target_fps=target_fps) as capture:
            # 获取视频信息
            original_fps = capture.get_original_fps()
            frame_size = capture.get_frame_size()

            print(f"✓ 视频已打开")
            print(f"  原始帧率: {original_fps:.2f} FPS")
            print(f"  原始尺寸: {frame_size[0]} x {frame_size[1]}")
            print(f"  帧间隔: {capture.frame_interval}")
            print()

            # 读取10帧
            frame_count = 0
            target_frames = 10

            print(f"读取 {target_frames} 帧并处理...")
            print("-" * 80)
            print(f"{'帧号':>6} | {'原始尺寸':>15} | {'处理后尺寸':>15} | {'JPEG大小':>12} | {'压缩比':>10}")
            print("-" * 80)

            for frame in capture.frames_generator():
                if frame_count >= target_frames:
                    break

                frame_count += 1

                # 获取原始帧信息
                orig_h, orig_w = frame.shape[:2]
                original_bytes = orig_h * orig_w * 3  # BGR格式，3字节每像素

                # 预处理
                try:
                    jpeg_data = preprocessor.process(frame)
                    jpeg_size = len(jpeg_data)

                    # 计算压缩比
                    compression_ratio = (jpeg_size / original_bytes) * 100

                    # 获取处理后尺寸
                    processed_h, processed_w = preprocessor.resize_frame(frame).shape[:2]

                    # 打印帧信息
                    print(f"{frame_count:>6} | {orig_w:4d} x {orig_h:<4d} | {processed_w:4d} x {processed_h:<4d} | {jpeg_size:>10,} B | {compression_ratio:>8.1f}%")

                except Exception as e:
                    print(f"{frame_count:>6} | 处理失败: {e}")
                    break

            print("-" * 80)
            print(f"✓ 成功读取和处理 {frame_count} 帧")

            # 测试结果
            if frame_count == target_frames:
                print(f"\n✓ 测试通过！成功读取 {target_frames} 帧")
                print(f"✓ VideoCapture 模块工作正常")
                print(f"✓ FramePreprocessor 模块工作正常")
                print(f"✓ with 语句资源管理正常")
                return True
            else:
                print(f"\n⚠  警告：只读取了 {frame_count}/{target_frames} 帧")
                print(f"   （视频可能较短，这是正常的）")
                return frame_count > 0

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数：测试所有可用的视频文件。"""
    project_root = Path(__file__).parent
    test_videos_dir = project_root / "test_videos"

    # 检查测试视频目录
    if not test_videos_dir.exists():
        print(f"错误：测试视频目录不存在: {test_videos_dir}")
        return 1

    # 查找所有视频文件
    video_files = list(test_videos_dir.glob("*.mp4")) + list(test_videos_dir.glob("*.avi"))

    if not video_files:
        print(f"错误：在 {test_videos_dir} 中未找到视频文件")
        print("请将测试视频文件放在该目录中")
        return 1

    print(f"找到 {len(video_files)} 个测试视频文件\n")

    # 测试每个视频文件
    all_passed = True
    for i, video_file in enumerate(video_files, 1):
        print(f"\n{'=' * 80}")
        print(f"测试视频 {i}/{len(video_files)}: {video_file.name}")
        print(f"{'=' * 80}")

        # 测试不同配置
        test_configs = [
            {"target_fps": None, "desc": "原始帧率"},
            {"target_fps": 5, "desc": "5 FPS 降采样"},
        ]

        for config in test_configs:
            print(f"\n配置: {config['desc']}")
            passed = test_capture_and_preprocess(
                str(video_file),
                target_fps=config["target_fps"]
            )

            if not passed:
                all_passed = False
                print(f"\n✗ 测试失败: {video_file.name}")
                break

        print()

    # 最终结果
    print("=" * 80)
    if all_passed:
        print("✓ 所有测试通过！")
        print("=" * 80)
        return 0
    else:
        print("✗ 部分测试失败")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
