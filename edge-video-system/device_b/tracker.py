"""
业务逻辑模块：跟踪和异常检测。

职责：帧间目标匹配、人流计数、异常停留报警。

输入：检测结果序列
输出：跟踪结果、统计信息、报警事件

设计决策：
- 使用IoU（交并比）进行帧间匹配
- 为每个跟踪目标分配唯一ID
- 检测异常停留（同一位置超过时间阈值）
"""

import time
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TrackedDetection:
    """跟踪检测类，包含检测结果和跟踪信息。"""
    detection: object  # Detection 对象
    track_id: int
    is_matched: bool = True


@dataclass
class DwellAlert:
    """异常停留报警类。"""
    track_id: int
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center: Tuple[float, float]  # (center_x, center_y)
    dwell_duration: float  # 停留时长（秒）
    alert_time: float  # 报警触发时间

    def __repr__(self):
        return (f"DwellAlert(track_id={self.track_id}, "
                f"center=({self.center[0]:.1f}, {self.center[1]:.1f}), "
                f"duration={self.dwell_duration:.1f}s)")


class Track:
    """跟踪目标类，存储单个目标的完整跟踪信息。"""

    def __init__(self, track_id: int, detection, start_time: float = None):
        """
        初始化跟踪目标。

        Args:
            track_id: 唯一跟踪ID
            detection: Detection 对象
            start_time: 首次出现时间（None则使用当前时间）
        """
        self.track_id = track_id
        self.bbox = detection.bbox  # (x1, y1, x2, y2)
        self.center = detection.center  # (center_x, center_y)
        self.first_seen_time = start_time if start_time else time.time()
        self.last_seen_time = self.first_seen_time
        self.last_match_time = self.first_seen_time

        # 统计信息
        self.unmatched_frames = 0  # 连续未匹配帧数
        self.total_frames = 1  # 总匹配帧数
        self.confidence_history = [detection.confidence]  # 置信度历史

        # 异常停留检测
        self.dwell_start_time = None  # 开始停留的时间
        self.dwell_position = None  # 停留位置 (center_x, center_y)
        self.has_alerted = False  # 是否已经触发过报警

    def update(self, detection):
        """
        更新跟踪目标。

        Args:
            detection: 新的 Detection 对象
        """
        new_center = detection.center
        current_time = time.time()

        self.bbox = detection.bbox
        self.last_seen_time = current_time
        self.last_match_time = current_time
        self.unmatched_frames = 0
        self.total_frames += 1
        self.confidence_history.append(detection.confidence)

        # 检查位置变化并更新停留状态
        if self.dwell_start_time is None:
            # 还没有开始停留计时
            if self.dwell_position is None:
                # 第一次，记录初始位置
                self.dwell_position = new_center
            else:
                # 已有初始位置，检查位置是否稳定
                pos_change = np.linalg.norm(
                    np.array(new_center) - np.array(self.dwell_position)
                )

                if pos_change <= 20:  # 位置稳定，开始计时
                    self.dwell_start_time = current_time
                else:
                    # 位置不稳定，更新初始位置
                    self.dwell_position = new_center
        else:
            # 已经在停留计时中
            pos_change = np.linalg.norm(
                np.array(new_center) - np.array(self.dwell_position)
            )

            if pos_change > 20:  # 位置变化超过20像素，认为移动了
                # 重置停留状态
                self.dwell_position = new_center
                self.dwell_start_time = current_time
                self.has_alerted = False  # 位置变了，可以重新报警
            # 如果位置变化小，保持原有的dwell_start_time不变（累计时间）

        # 更新center为新的位置
        self.center = new_center

    def mark_unmatched(self):
        """标记为未匹配（当前帧没有匹配到检测）。"""
        self.unmatched_frames += 1
        self.last_seen_time = time.time()

    def get_age(self) -> float:
        """获取跟踪目标的年龄（首次出现到现在的时间，秒）。"""
        return time.time() - self.first_seen_time

    def get_dwell_duration(self) -> float:
        """获取在当前位置的停留时长（秒）。"""
        if self.dwell_start_time is None:
            return 0.0
        return time.time() - self.dwell_start_time

    def is_stale(self, max_unmatched_frames: int = 50) -> bool:
        """判断是否应该删除（连续未匹配帧数过多）。"""
        return self.unmatched_frames >= max_unmatched_frames

    def get_average_confidence(self) -> float:
        """获取平均置信度。"""
        if not self.confidence_history:
            return 0.0
        return sum(self.confidence_history) / len(self.confidence_history)


class ObjectTracker:
    """目标跟踪器类，负责多目标跟踪和业务逻辑。"""

    def __init__(self,
                 iou_threshold: float = 0.3,
                 max_unmatched_frames: int = 50,
                 dwell_threshold: float = 10.0,
                 iou_auxiliary_threshold: float = 0.1,
                 center_distance_threshold: float = 100.0):
        """
        初始化目标跟踪器。

        Args:
            iou_threshold: IoU匹配主阈值（默认0.3）
            max_unmatched_frames: 最大连续未匹配帧数（默认50，约2秒@25fps）
            dwell_threshold: 异常停留时间阈值（秒，默认10秒）
            iou_auxiliary_threshold: IoU辅助匹配阈值（默认0.1，用于中心点距离匹配）
            center_distance_threshold: 中心点距离阈值（像素，默认100.0）
        """
        self.iou_threshold = iou_threshold
        self.max_unmatched_frames = max_unmatched_frames
        self.dwell_threshold = dwell_threshold
        self.iou_auxiliary_threshold = iou_auxiliary_threshold
        self.center_distance_threshold = center_distance_threshold

        # 跟踪状态
        self.tracks: Dict[int, Track] = {}  # {track_id: Track}
        self.next_track_id = 1  # 下一个分配的track_id
        self.total_person_count = 0  # 累计人流量（历史出现过的track_id总数）

        # 当前帧的报警事件
        self.current_alerts: List[DwellAlert] = []

    def calculate_iou(self, bbox1: Tuple[int, int, int, int],
                     bbox2: Tuple[int, int, int, int]) -> float:
        """
        计算两个边界框的IoU（交并比）。

        Args:
            bbox1: 边界框1 (x1, y1, x2, y2)
            bbox2: 边界框2 (x1, y1, x2, y2)

        Returns:
            IoU值（0-1）
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

    def calculate_center_distance(self, center1: Tuple[float, float],
                                 center2: Tuple[float, float]) -> float:
        """
        计算两个中心点之间的欧氏距离。

        Args:
            center1: 中心点1 (x, y)
            center2: 中心点2 (x, y)

        Returns:
            欧氏距离（像素）
        """
        return ((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)**0.5

    def update(self, detections: List) -> List[TrackedDetection]:
        """
        更新跟踪器状态。

        Args:
            detections: 当前帧的检测结果（Detection对象列表）

        Returns:
            带track_id的检测结果列表
        """
        # 清空当前帧报警
        self.current_alerts = []

        # 如果没有检测结果，标记所有跟踪目标为未匹配
        if not detections:
            for track in self.tracks.values():
                track.mark_unmatched()
            self._cleanup_stale_tracks()
            return []

        # 匹配检测到跟踪目标
        matched_track_ids = set()
        tracked_detections = []

        for detection in detections:
            best_match_id = None
            best_iou = self.iou_threshold
            best_center_dist = float('inf')
            match_method = None  # 'iou' 或 'center_distance'

            # 寻找最佳匹配
            for track_id, track in self.tracks.items():
                iou = self.calculate_iou(detection.bbox, track.bbox)
                center_dist = self.calculate_center_distance(detection.center, track.center)

                # 主匹配策略：IoU > 主阈值
                if iou > self.iou_threshold and iou > best_iou:
                    best_iou = iou
                    best_match_id = track_id
                    best_center_dist = center_dist
                    match_method = 'iou'

                # 辅助匹配策略：IoU > 辅助阈值 AND 中心距 < 阈值
                elif (iou > self.iou_auxiliary_threshold and
                      center_dist < self.center_distance_threshold):
                    # 如果这是目前找到的最好匹配
                    if best_match_id is None or iou > best_iou:
                        best_iou = iou
                        best_match_id = track_id
                        best_center_dist = center_dist
                        match_method = 'center_distance'

            if best_match_id is not None:
                # 更新现有跟踪目标
                self.tracks[best_match_id].update(detection)
                matched_track_ids.add(best_match_id)

                tracked_detections.append(TrackedDetection(
                    detection=detection,
                    track_id=best_match_id,
                    is_matched=True
                ))
            else:
                # 创建新的跟踪目标
                new_track_id = self.next_track_id
                self.next_track_id += 1
                self.total_person_count += 1

                new_track = Track(new_track_id, detection)
                self.tracks[new_track_id] = new_track

                tracked_detections.append(TrackedDetection(
                    detection=detection,
                    track_id=new_track_id,
                    is_matched=True
                ))

        # 标记未匹配的跟踪目标
        for track_id in list(self.tracks.keys()):
            if track_id not in matched_track_ids:
                self.tracks[track_id].mark_unmatched()

        # 清理过期跟踪目标
        self._cleanup_stale_tracks()

        # 检查异常停留
        self._check_dwell_alerts()

        return tracked_detections

    def _cleanup_stale_tracks(self):
        """清理过期的跟踪目标（连续未匹配帧数过多）。"""
        stale_track_ids = [
            track_id for track_id, track in self.tracks.items()
            if track.is_stale(self.max_unmatched_frames)
        ]

        for track_id in stale_track_ids:
            del self.tracks[track_id]

    def _check_dwell_alerts(self):
        """检查异常停留并生成报警。"""
        for track in self.tracks.values():
            # 检查是否触发异常停留
            dwell_duration = track.get_dwell_duration()

            if (dwell_duration >= self.dwell_threshold and
                not track.has_alerted and
                track.total_frames >= 5):  # 至少跟踪5帧才报警（避免误报）

                # 创建报警
                alert = DwellAlert(
                    track_id=track.track_id,
                    bbox=track.bbox,
                    center=track.center,
                    dwell_duration=dwell_duration,
                    alert_time=time.time()
                )

                self.current_alerts.append(alert)
                track.has_alerted = True  # 标记已报警，避免重复

    def get_active_track_count(self) -> int:
        """获取当前活跃的跟踪目标数量。"""
        return len(self.tracks)

    def get_total_person_count(self) -> int:
        """获取累计人流量（历史出现过的track_id总数）。"""
        return self.total_person_count

    def get_current_alerts(self) -> List[DwellAlert]:
        """获取当前帧的报警事件列表。"""
        return self.current_alerts

    def get_track_info(self, track_id: int) -> Optional[Track]:
        """获取指定跟踪目标的信息。"""
        return self.tracks.get(track_id)


if __name__ == "__main__":
    """
    测试代码：测试跟踪器的基本功能
    """
    print("=" * 60)
    print("ObjectTracker 模块测试")
    print("=" * 60)

    from detector import Detection

    # 创建跟踪器
    tracker = ObjectTracker(
        iou_threshold=0.3,
        max_unmatched_frames=50,
        dwell_threshold=2.0  # 2秒停留用于测试
    )

    print("\n测试 1: 创建新跟踪目标")
    print("-" * 40)

    # 模拟第一帧检测
    detections1 = [
        Detection(x1=100, y1=100, x2=200, y2=200, confidence=0.9),
    ]

    tracked1 = tracker.update(detections1)
    print(f"检测结果: {len(detections1)} 个")
    print(f"跟踪目标: {len(tracked1)} 个")
    print(f"活跃跟踪数: {tracker.get_active_track_count()}")
    print(f"累计人流量: {tracker.get_total_person_count()}")

    if tracked1:
        print(f"分配的track_id: {tracked1[0].track_id}")

    print("\n测试 2: 更新现有跟踪目标")
    print("-" * 40)

    # 模拟第二帧检测（位置略有变化）
    detections2 = [
        Detection(x1=105, y1=105, x2=205, y2=205, confidence=0.88),
    ]

    tracked2 = tracker.update(detections2)
    print(f"检测结果: {len(detections2)} 个")
    print(f"跟踪目标: {len(tracked2)} 个")
    print(f"活跃跟踪数: {tracker.get_active_track_count()}")
    print(f"累计人流量: {tracker.get_total_person_count()}")

    if tracked2:
        print(f"匹配的track_id: {tracked2[0].track_id}")

    # 验证是同一个ID
    if tracked1 and tracked2:
        if tracked1[0].track_id == tracked2[0].track_id:
            print("✓ 同一个目标保持了相同的track_id")
        else:
            print("✗ track_id发生了变化")

    print("\n测试 3: 添加新的跟踪目标")
    print("-" * 40)

    # 模拟第三帧检测（两个目标）
    detections3 = [
        Detection(x1=105, y1=105, x2=205, y2=205, confidence=0.85),  # 目标1
        Detection(x1=300, y1=150, x2=400, y2=250, confidence=0.92),  # 目标2
    ]

    tracked3 = tracker.update(detections3)
    print(f"检测结果: {len(detections3)} 个")
    print(f"跟踪目标: {len(tracked3)} 个")
    print(f"活跃跟踪数: {tracker.get_active_track_count()}")
    print(f"累计人流量: {tracker.get_total_person_count()}")

    for td in tracked3:
        print(f"  track_id={td.track_id}, center={td.detection.center}")

    print("\n测试 4: 目标消失（未匹配）")
    print("-" * 40)

    # 模拟目标消失
    for i in range(52):  # 超过max_unmatched_frames=50
        detections_empty = []
        tracker.update(detections_empty)

    print(f"活跃跟踪数: {tracker.get_active_track_count()}")
    print(f"累计人流量: {tracker.get_total_person_count()}")
    print("✓ 过期跟踪目标已被清理")

    print("\n" + "=" * 60)
    print("✓ 所有测试完成！")
    print("=" * 60)
