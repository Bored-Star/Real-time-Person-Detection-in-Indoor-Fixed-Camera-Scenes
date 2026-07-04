"""
独立单元测试：验证 tracker.py 的异常停留报警功能

功能：
1. 构造假数据模拟两种场景（停留 vs 移动）
2. 验证报警功能的正确性
3. 不依赖真实视频，使用模拟Detection对象

场景设计：
- 5 FPS视频，2秒停留阈值 = 约10帧触发报警
- 构造20帧假数据，验证报警行为
"""

import sys
import time
from pathlib import Path

# 添加device_b到路径
sys.path.insert(0, str(Path(__file__).parent / "device_b"))

from tracker import ObjectTracker, DwellAlert
from detector import Detection


def create_staying_detections():
    """
    创建停留场景的检测数据。

    场景：一个人在屏幕中央停留，位置有1-2像素微小抖动
    模拟真实检测误差，持续时间超过2秒

    Returns:
        Detection列表（20帧）
    """
    detections = []

    # 基准位置：屏幕中央
    base_x, base_y = 350, 250
    box_size = 100

    for frame in range(1, 21):  # 20帧
        # 添加1-2像素的随机抖动，模拟真实检测误差
        jitter_x = (frame % 3) - 1  # -1, 0, 1
        jitter_y = (frame % 2) - 1  # -1, 0

        x1 = base_x + jitter_x
        y1 = base_y + jitter_y
        x2 = x1 + box_size
        y2 = y1 + box_size

        # 置信度在0.85-0.95之间波动
        confidence = 0.85 + (frame % 10) * 0.01

        detection = Detection(
            x1=int(x1),
            y1=int(y1),
            x2=int(x2),
            y2=int(y2),
            confidence=confidence
        )

        detections.append(detection)

    return detections


def create_moving_detections():
    """
    创建移动场景的检测数据。

    场景：一个人持续从左向右移动
    每帧x坐标增加20像素，模拟行走
    不应该触发异常停留报警

    Returns:
        Detection列表（20帧）
    """
    detections = []

    # 起始位置：屏幕左侧
    start_x = 50
    y = 250
    box_size = 100
    step = 20  # 每帧移动20像素

    for frame in range(1, 21):  # 20帧
        x = start_x + frame * step
        x1 = x
        y1 = y
        x2 = x1 + box_size
        y2 = y1 + box_size

        # 置信度在0.85-0.95之间波动
        confidence = 0.85 + (frame % 10) * 0.01

        detection = Detection(
            x1=int(x1),
            y1=int(y1),
            x2=int(x2),
            y2=int(y2),
            confidence=confidence
        )

        detections.append(detection)

    return detections


def test_staying_scenario():
    """测试场景1：停留场景（应该触发报警）。"""
    print("=" * 80)
    print("场景1: 停留场景测试")
    print("=" * 80)
    print("描述: 一个人在屏幕中央停留，位置有微小抖动（1-2像素）")
    print(f"配置: 5 FPS, 2秒停留阈值 ≈ 10帧触发报警")
    print()

    # 创建跟踪器
    tracker = ObjectTracker(
        iou_threshold=0.3,
        max_unmatched_frames=10,
        dwell_threshold=2.0  # 2秒阈值
    )

    # 创建停留场景的检测数据
    detections = create_staying_detections()

    # 逐帧处理
    alert_triggered_frame = None
    alert_count = 0

    print("帧处理过程:")
    print("-" * 80)
    print(f"{'帧号':>4} | {'检测数':>4} | {'跟踪ID':>6} | {'活跃目标':>6} | {'累计人数':>6} | {'停留时长':>8} | {'报警':>6}")
    print("-" * 80)

    for frame_num, detection in enumerate(detections, 1):
        # 模拟5 FPS的时间间隔（0.2秒一帧）
        if frame_num > 1:
            time.sleep(0.2)  # 正确的5 FPS间隔

        # 更新跟踪器
        tracked_detections = tracker.update([detection])

        # 获取当前状态
        active_count = tracker.get_active_track_count()
        total_count = tracker.get_total_person_count()
        alerts = tracker.get_current_alerts()

        # 获取停留时长
        track_id = tracked_detections[0].track_id if tracked_detections else None
        dwell_duration = 0.0
        if track_id and track_id in tracker.tracks:
            dwell_duration = tracker.tracks[track_id].get_dwell_duration()

        # 检查是否触发报警
        alert_status = "否"
        if alerts:
            alert_status = "是"
            alert_count += 1
            if alert_triggered_frame is None:
                alert_triggered_frame = frame_num

            # 打印报警详情
            for alert in alerts:
                print(f"{'='*80}")
                print(f"⚠ 触发异常停留报警！")
                print(f"  帧号: {frame_num}")
                print(f"  跟踪ID: {alert.track_id}")
                print(f"  停留时长: {alert.dwell_duration:.2f} 秒")
                print(f"  停留位置: ({alert.center[0]:.1f}, {alert.center[1]:.1f})")
                print(f"  边界框: {alert.bbox}")
                print(f"{'='*80}")

        # 打印当前帧状态
        track_id_str = f"{track_id}" if track_id else "无"
        print(f"{frame_num:>4} | {len([detection]):>4} | {track_id_str:>6} | {active_count:>6} | {total_count:>6} | {dwell_duration:>8.2f} | {alert_status:>6}")

    print("-" * 80)
    print()
    print("场景1测试结果:")
    print(f"  总处理帧数: {len(detections)}")
    print(f"  报警触发帧: 第{alert_triggered_frame}帧" if alert_triggered_frame else "  报警触发帧: 未触发")
    print(f"  报警触发次数: {alert_count}")
    print(f"  预期触发帧: 第10-12帧（约2秒）")
    print()

    # 验证结果
    success = True
    issues = []

    if alert_triggered_frame is None:
        success = False
        issues.append("❌ 未触发报警（预期应该触发）")
    elif alert_triggered_frame < 10 or alert_triggered_frame > 12:
        success = False
        issues.append(f"⚠ 报警触发帧异常：第{alert_triggered_frame}帧（预期第10-12帧）")
    else:
        print(f"  ✅ 报警在正确时机触发：第{alert_triggered_frame}帧")

    if alert_count != 1:
        success = False
        issues.append(f"❌ 报警触发次数异常：{alert_count}次（预期1次）")
    else:
        print(f"  ✅ 报警只触发一次（符合预期）")

    if issues:
        for issue in issues:
            print(f"  {issue}")

    return success


def test_moving_scenario():
    """测试场景2：移动场景（不应该触发报警）。"""
    print()
    print("=" * 80)
    print("场景2: 移动场景测试")
    print("=" * 80)
    print("描述: 一个人持续从左向右移动，每帧x坐标增加20像素")
    print(f"配置: 5 FPS, 2秒停留阈值")
    print("预期: 不应该触发任何异常停留报警")
    print()

    # 创建跟踪器
    tracker = ObjectTracker(
        iou_threshold=0.3,
        max_unmatched_frames=10,
        dwell_threshold=2.0  # 2秒阈值
    )

    # 创建移动场景的检测数据
    detections = create_moving_detections()

    # 逐帧处理
    alert_count = 0

    print("帧处理过程:")
    print("-" * 80)
    print(f"{'帧号':>4} | {'检测数':>4} | {'跟踪ID':>6} | {'活跃目标':>6} | {'累计人数':>6} | {'X坐标':>6} | {'报警':>6}")
    print("-" * 80)

    for frame_num, detection in enumerate(detections, 1):
        # 模拟5 FPS的时间间隔（0.2秒一帧）
        if frame_num > 1:
            time.sleep(0.2)  # 正确的5 FPS间隔

        # 更新跟踪器
        tracked_detections = tracker.update([detection])

        # 获取当前状态
        active_count = tracker.get_active_track_count()
        total_count = tracker.get_total_person_count()
        alerts = tracker.get_current_alerts()

        # 获取x坐标
        x_coord = detection.x1

        # 检查是否触发报警
        alert_status = "否"
        if alerts:
            alert_status = "是"
            alert_count += 1

            # 打印报警详情
            for alert in alerts:
                print(f"{'='*80}")
                print(f"⚠ 异常：移动场景触发了报警！")
                print(f"  帧号: {frame_num}")
                print(f"  跟踪ID: {alert.track_id}")
                print(f"  停留时长: {alert.dwell_duration:.2f} 秒")
                print(f"  当前位置: ({alert.center[0]:.1f}, {alert.center[1]:.1f})")
                print(f"{'='*80}")

        # 打印当前帧状态
        track_id = tracked_detections[0].track_id if tracked_detections else None
        track_id_str = f"{track_id}" if track_id else "无"
        print(f"{frame_num:>4} | {len([detection]):>4} | {track_id_str:>6} | {active_count:>6} | {total_count:>6} | {x_coord:>6} | {alert_status:>6}")

    print("-" * 80)
    print()
    print("场景2测试结果:")
    print(f"  总处理帧数: {len(detections)}")
    print(f"  报警触发次数: {alert_count}")
    print(f"  预期: 0次（移动场景不应触发报警）")
    print()

    # 验证结果
    success = True
    if alert_count > 0:
        success = False
        print(f"  ❌ 移动场景错误地触发了{alert_count}次报警")
    else:
        print(f"  ✅ 移动场景正确地未触发报警")

    return success


def main():
    """主函数：运行所有测试场景。"""
    print("🔍 Tracker 异常停留报警功能单元测试")
    print()
    print("测试目标:")
    print("  1. 验证停留场景能正确触发报警")
    print("  2. 验证移动场景不会错误触发报警")
    print("  3. 验证报警只触发一次")
    print("  4. 验证报警信息完整性")
    print()

    # 运行两个场景测试
    scenario1_success = test_staying_scenario()
    scenario2_success = test_moving_scenario()

    # 总结
    print()
    print("=" * 80)
    print("🏁 最终测试总结")
    print("=" * 80)
    print(f"场景1（停留）: {'✅ 通过' if scenario1_success else '❌ 失败'}")
    print(f"场景2（移动）: {'✅ 通过' if scenario2_success else '❌ 失败'}")
    print()

    if scenario1_success and scenario2_success:
        print("🎉 所有测试通过！异常停留报警功能符合预期。")
        print()
        print("✅ 验证通过的功能点:")
        print("  ✓ 停留场景在预期时机触发报警（约第10-12帧）")
        print("  ✓ 报警只触发一次，不重复报警")
        print("  ✓ 报警信息完整（track_id、停留时长、位置）")
        print("  ✓ 移动场景不会错误触发报警")
        return 0
    else:
        print("⚠ 部分测试失败，请检查tracker.py的停留检测逻辑。")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
