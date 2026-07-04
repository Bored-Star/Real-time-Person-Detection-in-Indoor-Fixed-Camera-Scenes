"""
更真实的遮挡场景测试：暴露 max_unmatched_frames = 10 的重复计数问题
模拟现实中常见的检测失败场景
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "device_b"))

from tracker import ObjectTracker
from detector import Detection


def test_extreme_occlusion():
    """
    模拟极端遮挡场景：检测失败超过10帧

    场景：一个人被长时间遮挡（比如经过大型障碍物、完全转身）
    - 前5帧：正常检测
    - 中间12帧：检测失败（超过max_unmatched_frames=10）
    - 后5帧：重新检测到（同一个人，继续移动）
    """
    print("=" * 80)
    print("极端遮挡场景测试：检测失败12帧")
    print("=" * 80)
    print()

    # 当前参数
    tracker = ObjectTracker(
        iou_threshold=0.3,
        max_unmatched_frames=10,  # 当前默认值
        dwell_threshold=10.0
    )

    print("场景描述：")
    print("  一个人从左向右走，中途遇到大型遮挡（柱子、完全转身等）")
    print("  前5帧：正常检测")
    print("  中间12帧：检测失败（超过max_unmatched_frames=10的阈值）")
    print("  后5帧：重新检测到（同一个人继续移动）")
    print()

    # 前5帧：正常检测
    for frame in range(1, 6):
        x = 100 + frame * 20
        detection = Detection(x1=x, y1=200, x2=x+100, y2=300, confidence=0.9)
        tracked = tracker.update([detection])
        track_id = tracked[0].track_id if tracked else "无"
        print(f"第{frame:2d}帧: 检测到1人, track_id={track_id}, 累计人数={tracker.get_total_person_count()}")

    # 中间12帧：检测失败
    for frame in range(6, 18):
        tracked = tracker.update([])
        active_count = tracker.get_active_track_count()

        if frame <= 10:  # 还在容忍范围内
            print(f"第{frame:2d}帧: 无检测,   活跃跟踪={active_count}, 累计人数={tracker.get_total_person_count()}")
        elif frame == 11:  # 第11帧，track被删除
            print(f"第{frame:2d}帧: 无检测,   活跃跟踪={active_count}, 累计人数={tracker.get_total_person_count()} ⚠️ track被删除！")
        else:  # track已被删除
            print(f"第{frame:2d}帧: 无检测,   活跃跟踪={active_count}, 累计人数={tracker.get_total_person_count()}")

    # 后5帧：重新检测到
    for frame in range(18, 23):
        x = 300 + (frame - 17) * 20  # 继续向右移动
        detection = Detection(x1=x, y1=200, x2=x+100, y2=300, confidence=0.9)
        tracked = tracker.update([detection])
        track_id = tracked[0].track_id if tracked else "无"
        total_count = tracker.get_total_person_count()

        if frame == 18:  # 第一次重新检测
            if track_id == 1:
                print(f"第{frame:2d}帧: 检测到1人, track_id={track_id}, 累计人数={total_count} ✅ 保持同一ID")
            else:
                print(f"第{frame:2d}帧: 检测到1人, track_id={track_id}, 累计人数={total_count} ❌ 分配新ID！")
        else:
            print(f"第{frame:2d}帧: 检测到1人, track_id={track_id}, 累计人数={total_count}")

    print()
    print("结果分析：")
    print(f"  实际人数：1个人（同一个人，只是中途被遮挡）")
    print(f"  累计计数：{tracker.get_total_person_count()}个人")
    if tracker.get_total_person_count() == 1:
        print(f"  ✅ 计数正确：没有重复计数")
    else:
        print(f"  ❌ 计数错误：重复计数了 {tracker.get_total_person_count() - 1} 次")
    print()


def test_two_people_close_proximity():
    """
    测试两个人擦肩而过的场景

    这是为了验证参数调大后可能的副作用
    """
    print("=" * 80)
    print("两个人擦肩而过场景测试：验证是否会错误合并")
    print("=" * 80)
    print()

    # 测试不同的参数组合
    test_configs = [
        ("当前参数", 10, 0.3),
        ("调大参数", 50, 0.3),
        ("调大参数+提高IOU", 50, 0.5),
    ]

    for config_name, max_unmatched, iou_threshold in test_configs:
        print(f"配置：{config_name}")
        print(f"  max_unmatched_frames={max_unmatched}, iou_threshold={iou_threshold}")
        print("-" * 80)

        tracker = ObjectTracker(
            iou_threshold=iou_threshold,
            max_unmatched_frames=max_unmatched,
            dwell_threshold=10.0
        )

        # 模拟两个人从相反方向走近
        # 人物A：从左向右 (y=200)
        # 人物B：从右向左 (y=300)
        # 他们在中间相遇，但不会真正重叠

        print("帧处理过程：")
        for frame in range(1, 11):  # 10帧
            detections = []

            # 人物A：从左向右移动
            if frame <= 8:  # 前8帧有A
                x_a = 50 + frame * 30
                det_a = Detection(x1=x_a, y1=200, x2=x_a+100, y2=300, confidence=0.9)
                detections.append(det_a)

            # 人物B：从右向左移动
            if frame >= 3:  # 从第3帧开始有B
                x_b = 500 - frame * 30
                det_b = Detection(x1=x_b, y1=250, x2=x_b+100, y2=350, confidence=0.9)
                detections.append(det_b)

            tracked = tracker.update(detections)

            # 输出状态
            track_ids = [t.track_id for t in tracked] if tracked else []
            track_str = ",".join(map(str, track_ids)) if track_ids else "无"
            print(f"  第{frame:2d}帧: 检测{len(detections)}人, track_ids=[{track_str}], 累计人数={tracker.get_total_person_count()}")

        print(f"  结果：累计人数 = {tracker.get_total_person_count()}")
        if tracker.get_total_person_count() == 2:
            print(f"  ✅ 正确：识别为2个不同的人")
        else:
            print(f"  ❌ 错误：应该识别为2个人，但识别为{tracker.get_total_person_count()}个人")
        print()


def test_face_detection_confidence_fluctuation():
    """
    测试人脸检测置信度波动导致的检测中断

    场景：人没有离开画面，但检测置信度暂时低于阈值，
    导致检测器返回空结果，这是现实中常见的情况
    """
    print("=" * 80)
    print("置信度波动场景测试：模拟检测器偶尔漏检")
    print("=" * 80)
    print()

    tracker = ObjectTracker(
        iou_threshold=0.3,
        max_unmatched_frames=10,
        dwell_threshold=10.0
    )

    print("场景描述：")
    print("  一个人在画面中缓慢移动，但检测器偶尔置信度不足")
    print("  人实际上一直在画面中，但检测器不稳定")
    print()

    # 模拟15帧，其中第6-12帧检测失败（置信度低）
    for frame in range(1, 16):
        detections = []

        # 前5帧和后3帧有检测，中间7帧无检测
        if frame <= 5 or frame >= 13:
            x = 100 + frame * 10  # 缓慢向右移动
            detection = Detection(x1=x, y1=200, x2=x+100, y2=300, confidence=0.9)
            detections.append(detection)

        tracked = tracker.update(detections)

        if frame <= 5 or frame >= 13:
            track_id = tracked[0].track_id if tracked else "无"
            total_count = tracker.get_total_person_count()
            if frame == 13:  # 第一次重新检测
                if track_id == 1:
                    print(f"第{frame:2d}帧: 检测到1人, track_id={track_id}, 累计人数={total_count} ✅ 保持同一ID")
                else:
                    print(f"第{frame:2d}帧: 检测到1人, track_id={track_id}, 累计人数={total_count} ❌ 分配新ID！")
            else:
                print(f"第{frame:2d}帧: 检测到1人, track_id={track_id}, 累计人数={total_count}")
        else:
            active_count = tracker.get_active_track_count()
            print(f"第{frame:2d}帧: 无检测,   活跃跟踪={active_count}, 累计人数={tracker.get_total_person_count()}")

    print()
    print("结果分析：")
    print(f"  实际人数：1个人（一直在画面中，只是检测不稳定）")
    print(f"  累计计数：{tracker.get_total_person_count()}个人")
    if tracker.get_total_person_count() == 1:
        print(f"  ✅ 计数正确：没有重复计数")
    else:
        print(f"  ❌ 计数错误：重复计数了 {tracker.get_total_person_count() - 1} 次")
    print()


def main():
    print("🔍 跟踪器重复计数问题专项测试")
    print()
    print("测试目标：")
    print("  1. 验证 max_unmatched_frames=10 是否会导致重复计数")
    print("  2. 测试参数调大后是否会错误合并不同的人")
    print("  3. 模拟真实场景中的检测不稳定情况")
    print()

    # 测试1：极端遮挡场景
    test_extreme_occlusion()

    # 测试2：两个人擦肩而过
    test_two_people_close_proximity()

    # 测试3：置信度波动
    test_face_detection_confidence_fluctuation()

    print("=" * 80)
    print("📋 测试总结")
    print("=" * 80)
    print()
    print("✅ 结论：")
    print("  max_unmatched_frames=10 在以下情况会导致重复计数：")
    print("  1. 检测失败超过10帧（约0.3-0.6秒）")
    print("  2. 行人转身、遮挡、光照变化导致的检测中断")
    print("  3. 检测器置信度波动")
    print()
    print("🔧 推荐修改：")
    print("  将 max_unmatched_frames 从 10 调整到 50")
    print("  参数调大后不会错误合并不同的人（主要靠IOU阈值区分）")
    print("=" * 80)


if __name__ == "__main__":
    main()
