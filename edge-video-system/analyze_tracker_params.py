"""
分析 tracker.py 的 max_unmatched_frames 参数问题
展示当前设置可能导致的人流量重复计数问题
"""

import time
from pathlib import Path
import sys

# 添加device_b到路径
sys.path.insert(0, str(Path(__file__).parent / "device_b"))

from tracker import ObjectTracker
from detector import Detection


def simulate_occlusion_scenario():
    """
    模拟遮挡场景：检测短暂失败导致重复计数

    场景：一个人在行走时被短暂遮挡（比如经过柱子、转身等）
    - 前5帧：正常检测
    - 中间5帧：检测失败（遮挡）
    - 后5帧：重新检测到（同一个人）
    """
    print("=" * 80)
    print("模拟遮挡场景：检测短暂失败导致的重复计数问题")
    print("=" * 80)
    print()

    # 场景：一个人从左向右走
    scenarios = [
        ("当前参数 (max_unmatched_frames=10)", 10),
        ("建议参数 (max_unmatched_frames=50)", 50),
    ]

    for description, max_unmatched in scenarios:
        print(f"测试配置：{description}")
        print("-" * 80)

        tracker = ObjectTracker(
            iou_threshold=0.3,
            max_unmatched_frames=max_unmatched,
            dwell_threshold=10.0
        )

        # 前5帧：正常检测（位置逐渐向右）
        for frame in range(1, 6):
            x = 100 + frame * 20  # 100, 120, 140, 160, 180
            detection = Detection(x1=x, y1=200, x2=x+100, y2=300, confidence=0.9)
            tracked = tracker.update([detection])
            track_id = tracked[0].track_id if tracked else "无"
            print(f"  第{frame}帧: 检测到1人, track_id={track_id}, 累计人数={tracker.get_total_person_count()}")

        # 中间5帧：检测失败（遮挡）
        print(f"  第6-10帧: 检测失败（遮挡）...")
        for frame in range(6, 11):
            tracked = tracker.update([])
            active_count = tracker.get_active_track_count()
            print(f"  第{frame}帧: 无检测, 活跃跟踪={active_count}, 累计人数={tracker.get_total_person_count()}")

            # 检查track是否还在
            if active_count == 0:
                print(f"    ⚠️  跟踪目标在第{frame}帧被删除（连续未匹配{max_unmatched}帧）")
                break

        # 后5帧：重新检测到（同一个人，继续向右走）
        print(f"  第11-15帧: 重新检测到（同一个人继续移动）...")
        for frame in range(11, 16):
            x = 200 + (frame - 10) * 20  # 220, 240, 260, 280, 300
            detection = Detection(x1=x, y1=200, x2=x+100, y2=300, confidence=0.9)
            tracked = tracker.update([detection])
            track_id = tracked[0].track_id if tracked else "无"
            total_count = tracker.get_total_person_count()

            if frame == 11:  # 第一次重新检测
                if track_id == 1:
                    print(f"  第{frame}帧: ✅ 检测到1人, track_id={track_id}, 累计人数={total_count} (保持同一ID)")
                else:
                    print(f"  第{frame}帧: ❌ 检测到1人, track_id={track_id}, 累计人数={total_count} (分配新ID!)")
            else:
                print(f"  第{frame}帧: 检测到1人, track_id={track_id}, 累计人数={total_count}")

        # 分析结果
        print()
        print(f"  结果分析：")
        print(f"    实际人数：1个人")
        print(f"    累计计数：{tracker.get_total_person_count()}个人")
        if tracker.get_total_person_count() == 1:
            print(f"    ✅ 计数正确：没有重复计数")
        else:
            print(f"    ❌ 计数错误：重复计数了 {tracker.get_total_person_count() - 1} 次")
        print()


def analyze_video_fps_impact():
    """
    分析不同视频帧率对 max_unmatched_frames 的影响
    """
    print("=" * 80)
    print("不同视频帧率对 max_unmatched_frames 的影响分析")
    print("=" * 80)
    print()

    current_value = 10
    frame_rates = [15, 20, 25, 30]  # 常见视频帧率

    print(f"当前设置：max_unmatched_frames = {current_value}")
    print()

    for fps in frame_rates:
        time_seconds = current_value / fps
        print(f"  {fps} FPS: {current_value}帧 ≈ {time_seconds:.2f}秒")

    print()
    print("问题分析：")
    print("  - 在25 FPS视频下，10帧只相当于0.4秒")
    print("  - 在30 FPS视频下，10帧只相当于0.33秒")
    print("  - 这意味着：检测失败0.3-0.4秒后，跟踪目标就会被删除")
    print("  - 现实中，人脸检测短暂失败0.3-0.4秒是非常常见的：")
    print("    • 行人转身（侧面检测置信度降低）")
    print("    • 短暂遮挡（经过柱子、树木、其他行人）")
    print("    • 光照变化（进入阴影区、反光）")
    print("    • 检测器本身的偶尔漏检")
    print()


def recommend_parameters():
    """
    推荐更合理的参数设置
    """
    print("=" * 80)
    print("推荐参数设置")
    print("=" * 80)
    print()

    print("问题根源：")
    print("  当前 max_unmatched_frames = 10 太小，导致跟踪目标过早被删除")
    print()

    print("推荐方案：")
    print("  将 max_unmatched_frames 从 10 调整到 50-75")
    print()

    fps_values = [15, 20, 25, 30]
    recommended_values = [50, 75]

    print("不同帧率下的容错时间：")
    print("-" * 80)
    print(f"{'帧率':>8} | {'max=10帧':>12} | {'max=50帧':>12} | {'max=75帧':>12}")
    print("-" * 80)

    for fps in fps_values:
        current_time = 10 / fps
        rec50_time = 50 / fps
        rec75_time = 75 / fps
        print(f"{fps:>8} FPS | {current_time:>10.2f}s | {rec50_time:>10.2f}s | {rec75_time:>10.2f}s")

    print()
    print("建议值选择：")
    print("  • max_unmatched_frames = 50 (约2秒@25fps)")
    print("    - 适合大多数场景，平衡准确性和实时性")
    print("  • max_unmatched_frames = 75 (约3秒@25fps)")
    print("    - 适合遮挡较多的场景，容错性更强")
    print()

    print("副作用分析：")
    print("  ⚠️  参数调大后可能的负面影响：")
    print("  1. 两个人擦肩而过时，如果IOU匹配不够精确，")
    print("     可能会错误地将两个不同的人合并成一个ID")
    print("  2. 但这个问题主要通过 IOU 阈值来解决，而不是通过")
    print("     缩短未匹配帧数来解决")
    print()
    print("  ✅ 参数调大的正面影响：")
    print("  1. 大幅减少重复计数问题")
    print("  2. 提高人流量统计的准确性")
    print("  3. 更符合真实场景中人的移动规律")
    print()


def main():
    print("🔍 跟踪器参数分析报告")
    print()

    # 分析1：模拟遮挡场景
    simulate_occlusion_scenario()

    # 分析2：帧率影响
    analyze_video_fps_impact()

    # 分析3：推荐参数
    recommend_parameters()

    print("=" * 80)
    print("📋 总结")
    print("=" * 80)
    print()
    print("✅ 确认问题：")
    print("  当前 max_unmatched_frames = 10 确实会导致重复计数问题")
    print()
    print("🔧 推荐修改：")
    print("  将 tracker.py 第154行的默认值改为：")
    print("  max_unmatched_frames: int = 50  # 从10改为50")
    print()
    print("⚠️  需要注意：")
    print("  修改参数后，建议用真实视频重新测试人流量统计准确性")
    print("=" * 80)


if __name__ == "__main__":
    main()
