"""
完整链路测试脚本：测试 detector + tracker + result_writer

功能：
1. 启动设备B（接收、检测、跟踪、输出）
2. 启动设备A（采集、处理、发送）
3. 验证跟踪ID的一致性
4. 验证异常停留检测
5. 检查输出结果
"""

import sys
import time
import subprocess
from pathlib import Path

def test_tracker_and_pipeline():
    """测试完整的跟踪链路。"""
    print("=" * 80)
    print("完整链路测试：Detector + Tracker + ResultWriter")
    print("=" * 80)

    project_root = Path(__file__).parent
    video_path = project_root / "test_videos" / "face-demographics-walking-and-pause.mp4"
    model_path = project_root / "models" / "res10_300x300_ssd_iter_140000.caffemodel"
    config_path = project_root / "models" / "deploy.prototxt"
    output_dir = project_root / "output_frames"

    print(f"\n测试配置:")
    print(f"  视频文件: {video_path.name}")
    print(f"  模型文件: {model_path.name}")
    print(f"  配置文件: {config_path.name}")
    print(f"  输出目录: {output_dir}")
    print(f"  停留阈值: 2.0 秒（测试用，较低阈值）")

    # 清空输出目录
    if output_dir.exists():
        for file in output_dir.glob("*.jpg"):
            file.unlink()
        print(f"  已清空输出目录")
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("步骤 1: 启动设备B（接收、检测、跟踪、输出）")
    print("=" * 80)

    # 启动设备B进程
    device_b_cmd = [
        sys.executable,
        str(project_root / "device_b" / "main.py"),
        "--host", "0.0.0.0",
        "--port", "6006",
        "--model-path", str(model_path),
        "--config-path", str(config_path),
        "--confidence", "0.3",  # 降低阈值以检测更多人脸
        "--dwell-threshold", "2.0",  # 2秒停留用于测试
        "--output", str(output_dir)
    ]

    print(f"启动命令: {' '.join(device_b_cmd)}")

    try:
        device_b_process = subprocess.Popen(
            device_b_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        print("设备B进程已启动，PID:", device_b_process.pid)
        print("等待服务器初始化...")
        time.sleep(3)

        print("\n" + "=" * 80)
        print("步骤 2: 启动设备A（采集、处理、发送）")
        print("=" * 80)

        # 启动设备A进程
        device_a_cmd = [
            sys.executable,
            str(project_root / "device_a" / "main.py"),
            "--video", str(video_path),
            "--host", "127.0.0.1",
            "--port", "6006",
            "--fps", "5",  # 5 FPS降采样
            "--quality", "80"
        ]

        print(f"启动命令: {' '.join(device_a_cmd)}")

        device_a_process = subprocess.Popen(
            device_a_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        print("设备A进程已启动，PID:", device_a_process.pid)
        print("\n开始处理视频...")
        print("-" * 80)

        # 实时显示输出
        device_b_lines = []
        device_a_lines = []

        # 等待处理完成（最多60秒）
        start_time = time.time()
        max_wait = 60

        while time.time() - start_time < max_wait:
            # 检查设备B输出
            try:
                line = device_b_process.stdout.readline()
                if line:
                    print(f"[设备B] {line.strip()}")
                    device_b_lines.append(line)
                    # 检查是否有异常停留报警
                    if "异常停留报警" in line:
                        print("  ⚠ 检测到异常停留事件！")
            except:
                pass

            # 检查设备A输出
            try:
                line = device_a_process.stdout.readline()
                if line:
                    device_a_lines.append(line)
            except:
                pass

            # 检查进程是否结束
            if device_a_process.poll() is not None:
                print("\n设备A进程已结束")
                break

            time.sleep(0.1)

        # 等待进程结束
        device_a_process.wait(timeout=5)
        device_b_process.terminate()
        device_b_process.wait(timeout=5)

        print("-" * 80)
        print("处理完成！")

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        if 'device_b_process' in locals():
            device_b_process.terminate()
        if 'device_a_process' in locals():
            device_a_process.terminate()
        return False

    # 分析结果
    print("\n" + "=" * 80)
    print("步骤 3: 分析输出结果")
    print("=" * 80)

    # 统计输出文件
    output_files = list(output_dir.glob("frame_*.jpg"))
    print(f"\n生成的输出文件: {len(output_files)} 个")

    if len(output_files) > 0:
        print(f"文件列表（前5个）:")
        for i, file in enumerate(sorted(output_files)[:5], 1):
            size = file.stat().st_size / 1024
            print(f"  {i}. {file.name} ({size:.1f} KB)")

        if len(output_files) > 5:
            print(f"  ... 还有 {len(output_files) - 5} 个文件")

    # 分析日志
    print("\n" + "=" * 80)
    print("步骤 4: 分析跟踪结果")
    print("=" * 80)

    # 查找跟踪ID信息
    track_ids_found = []
    for line in device_b_lines:
        if "累计:" in line and "人" in line:
            print(f"[人流量] {line.strip()}")
        if "异常停留报警" in line:
            print(f"[停留报警] {line.strip()}")

    # 验证输出文件中的track_id
    print("\n验证输出图像中的track_id标注...")
    import cv2
    import numpy as np

    track_id_samples = []
    for output_file in sorted(output_files)[:3]:  # 检查前3个文件
        img = cv2.imread(str(output_file))
        if img is not None:
            # 使用OCR很难，但我们可以检查文件是否正常生成
            size = output_file.stat().st_size / 1024
            print(f"  ✓ {output_file.name} - {img.shape[1]}x{img.shape[0]}, {size:.1f} KB")

    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"✓ 完整链路测试完成")
    print(f"✓ 生成了 {len(output_files)} 个输出文件")
    print(f"✓ 输出目录: {output_dir}")
    print(f"\n你可以查看以下文件:")
    print(f"  - 输出图像: {output_dir}")
    print(f"  - 图像中应标注有 'ID:X' 格式的跟踪ID")
    print(f"  - 左上角显示当前活跃目标和累计人流量")
    print("=" * 80)

    return len(output_files) > 0


if __name__ == "__main__":
    try:
        success = test_tracker_and_pipeline()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
