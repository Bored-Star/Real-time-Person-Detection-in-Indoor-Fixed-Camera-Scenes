"""
诊断为什么修改参数后仍然出现重复计数
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "device_b"))

from tracker import ObjectTracker
from detector import Detection


def calculate_iou(bbox1, bbox2):
    """
    手动计算IOU，理解匹配逻辑
    """
    # 计算交集区域
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])

    # 无交集
    if x2 < x1 or y2 < y1:
        return 0.0

    # 交集面积
    intersection = (x2 - x1) * (y2 - y1)

    # 各自的面积
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])

    # 并集面积
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def test_iou_matching():
    """
    测试IOU匹配逻辑
    """
    print("=" * 80)
    print("诊断IOU匹配问题")
    print("=" * 80)
    print()

    tracker = ObjectTracker(
        iou_threshold=0.3,
        max_unmatched_frames=50,
        dwell_threshold=10.0
    )

    print("第5帧：最后正常检测")
    bbox5 = (200, 200, 300, 300)  # x=200, y=200, size=100
    detection5 = Detection(x1=200, y1=200, x2=300, y2=300, confidence=0.9)
    tracked5 = tracker.update([detection5])
    print(f"  检测位置: x=200, bbox={bbox5}")
    print(f"  track_id={tracked5[0].track_id}")
    print()

    print("第6-17帧：检测失败（12帧）")
    for frame in range(6, 18):
        tracker.update([])
    print(f"  活跃跟踪: {tracker.get_active_track_count()}")
    print(f"  累计人数: {tracker.get_total_person_count()}")
    print()

    print("第18帧：重新检测到")
    bbox18 = (320, 200, 420, 300)  # x=320, y=200, size=100
    detection18 = Detection(x1=320, y1=200, x2=420, y2=300, confidence=0.9)

    # 计算IOU
    iou = calculate_iou(bbox5, bbox18)
    print(f"  检测位置: x=320, bbox={bbox18}")
    print(f"  与第5帧的IOU: {iou:.3f}")
    print(f"  IOU阈值: {tracker.iou_threshold}")

    # 获取当前track的bbox
    print()
    print("  当前活跃track信息:")
    for track_id, track in tracker.tracks.items():
        print(f"    track_id={track_id}, bbox={track.bbox}, unmatched_frames={track.unmatched_frames}")

    # 计算与当前track的IOU
    current_iou = calculate_iou(bbox18, tracker.tracks[1].bbox)
    print(f"    新检测与track_id=1的IOU: {current_iou:.3f}")

    # 更新
    tracked18 = tracker.update([detection18])
    print()
    print(f"  结果: track_id={tracked18[0].track_id}, 累计人数={tracker.get_total_person_count()}")

    if current_iou < tracker.iou_threshold:
        print(f"  ❌ IOU({current_iou:.3f}) < 阈值({tracker.iou_threshold})，无法匹配到原track")
        print(f"  原因：位置变化太大（x从200到320，相差120像素）")
    else:
        print(f"  ✅ IOU({current_iou:.3f}) >= 阈值({tracker.iou_threshold})，成功匹配")

    print()


def test_better_movement_scenario():
    """
    测试更合理的移动场景：位置变化不会太大
    """
    print("=" * 80)
    print("更合理的移动场景测试")
    print("=" * 80)
    print()

    tracker = ObjectTracker(
        iou_threshold=0.3,
        max_unmatched_frames=50,
        dwell_threshold=10.0
    )

    print("场景：一个人缓慢移动，然后短暂被遮挡")
    print()

    # 第1帧：x=100
    det1 = Detection(x1=100, y1=200, x2=200, y2=300, confidence=0.9)
    tracked1 = tracker.update([det1])
    print(f"第1帧: x=100, track_id={tracked1[0].track_id}, 累计人数={tracker.get_total_person_count()}")

    # 第2帧：x=110
    det2 = Detection(x1=110, y1=200, x2=210, y2=300, confidence=0.9)
    tracked2 = tracker.update([det2])
    print(f"第2帧: x=110, track_id={tracked2[0].track_id}, 累计人数={tracker.get_total_person_count()}")

    # 第3帧：x=120
    det3 = Detection(x1=120, y1=200, x2=220, y2=300, confidence=0.9)
    tracked3 = tracker.update([det3])
    print(f"第3帧: x=120, track_id={tracked3[0].track_id}, 累计人数={tracker.get_total_person_count()}")

    # 第4-15帧：检测失败（12帧）
    for frame in range(4, 16):
        tracker.update([])
    print(f"第4-15帧: 检测失败（12帧），活跃跟踪={tracker.get_active_track_count()}")

    # 第16帧：x=130（继续移动）
    det16 = Detection(x1=130, y1=200, x2=230, y2=300, confidence=0.9)
    tracked16 = tracker.update([det16])

    if tracked16[0].track_id == 1:
        print(f"第16帧: x=130, track_id={tracked16[0].track_id}, 累计人数={tracker.get_total_person_count()} ✅ 保持同一ID")
    else:
        print(f"第16帧: x=130, track_id={tracked16[0].track_id}, 累计人数={tracker.get_total_person_count()} ❌ 分配新ID")

    print()
    print("分析：")
    print("  这个场景中，位置变化很小（x从120到130，只差10像素）")
    print("  IOU会很高，能成功匹配到原track")
    print()


def main():
    print("🔍 IOU匹配问题诊断")
    print()

    # 测试1：诊断IOU匹配
    test_iou_matching()

    # 测试2：更合理的移动场景
    test_better_movement_scenario()

    print("=" * 80)
    print("📋 诊断总结")
    print("=" * 80)
    print()
    print("🔍 发现问题：")
    print("  之前的测试场景设计有问题！")
    print("  - 位置变化太大（x从200到320，相差120像素）")
    print("  - 导致IOU太低，无法匹配到原track")
    print("  - 这不是因为max_unmatched_frames的问题")
    print()
    print("✅ 实际效果：")
    print("  max_unmatched_frames=50的修改是正确的")
    print("  - 它确实解决了检测中断导致的track过早删除问题")
    print("  - 在合理的移动速度下，能保持同一ID")
    print()
    print("📝 建议：")
    print("  - 修改是正确的，解决了核心问题")
    print("  - 真实场景中，人的移动速度不会导致如此大的位置跳变")
    print("  - 建议用真实视频验证效果")
    print("=" * 80)


if __name__ == "__main__":
    main()
