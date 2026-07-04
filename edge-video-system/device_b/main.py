"""
边缘侧设备B主程序入口。

职责：解析命令行参数，协调各模块完成接收、推理和输出。

命令行参数：
    --host: 绑定地址
    --port: 绑定端口
    --model-path: 模型文件路径
    --config-path: 模型配置文件路径
    --confidence: 检测置信度阈值
    --dwell-threshold: 异常停留时间阈值（秒）
    --output: 输出目录

设计决策：
- 使用argparse解析参数
- 主循环中处理接收、推理、跟踪、输出
- 提供详细的运行日志
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from receiver import FrameReceiver
from detector import FaceDetector
from tracker import ObjectTracker
from result_writer import ResultWriter


def parse_arguments():
    """
    解析命令行参数。

    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description="边缘侧设备B - 接收、检测、跟踪和输出"
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="绑定地址（默认：0.0.0.0）"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=6006,
        help="绑定端口（默认：6006）"
    )

    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="人脸检测模型文件路径"
    )

    parser.add_argument(
        "--config-path",
        type=str,
        default=None,
        help="模型配置文件路径（某些模型需要）"
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.5,
        help="检测置信度阈值 0.0-1.0（默认：0.5）"
    )

    parser.add_argument(
        "--dwell-threshold",
        type=float,
        default=10.0,
        help="异常停留时间阈值（秒，默认：10.0）"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output_frames",
        help="输出目录（默认：output_frames）"
    )

    return parser.parse_args()


def setup_logging(log_level: str = "INFO"):
    """
    设置日志系统。

    Args:
        log_level: 日志级别（DEBUG/INFO/WARNING/ERROR）
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def validate_model_files(model_path: str, config_path: str = None) -> bool:
    """
    验证模型文件存在性。

    Args:
        model_path: 模型文件路径
        config_path: 配置文件路径（可选）

    Returns:
        文件存在返回True，否则返回False
    """
    model_file = Path(model_path)
    if not model_file.exists():
        print(f"错误：模型文件不存在: {model_path}")
        return False

    if config_path is not None:
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"错误：配置文件不存在: {config_path}")
            return False

    return True


def create_output_directory(output_dir: str) -> bool:
    """
    创建输出目录。

    Args:
        output_dir: 输出目录路径

    Returns:
        创建成功返回True，失败返回False
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"错误：创建输出目录失败: {e}")
        return False


def main():
    """主函数：协调各模块完成边缘侧设备B的所有工作。"""
    # 解析参数
    args = parse_arguments()

    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("边缘侧设备B 启动")
    logger.info("=" * 60)
    logger.info(f"绑定地址: {args.host}:{args.port}")
    logger.info(f"模型文件: {args.model_path}")
    if args.config_path:
        logger.info(f"配置文件: {args.config_path}")
    logger.info(f"置信度阈值: {args.confidence}")
    logger.info(f"停留阈值: {args.dwell_threshold} 秒")
    logger.info(f"输出目录: {args.output}")
    logger.info("=" * 60)

    # 验证模型文件
    if not validate_model_files(args.model_path, args.config_path):
        logger.error("模型文件验证失败")
        sys.exit(1)

    # 创建输出目录
    if not create_output_directory(args.output):
        logger.error("创建输出目录失败")
        sys.exit(1)

    # 创建人脸检测器
    logger.info("初始化人脸检测器...")
    try:
        detector = FaceDetector(
            model_path=args.model_path,
            config_path=args.config_path,
            confidence_threshold=args.confidence
        )
        logger.info("✓ 检测器初始化成功")
    except Exception as e:
        logger.error(f"检测器初始化失败: {e}")
        sys.exit(1)

    # 创建目标跟踪器
    logger.info("初始化目标跟踪器...")
    try:
        tracker = ObjectTracker(
            iou_threshold=0.3,
            max_unmatched_frames=50,  # 使用新的默认值
            dwell_threshold=args.dwell_threshold
        )
        logger.info("✓ 跟踪器初始化成功")
    except Exception as e:
        logger.error(f"跟踪器初始化失败: {e}")
        sys.exit(1)

    # 创建结果写入器
    result_writer = ResultWriter(output_dir=args.output)

    # 创建接收器并启动服务器
    logger.info("启动TCP服务器...")
    try:
        with FrameReceiver(bind_host=args.host, bind_port=args.port) as receiver:
            logger.info(f"✓ 服务器已启动，监听 {args.host}:{args.port}")

            # 等待客户端连接
            logger.info("等待客户端连接...")
            client_socket = receiver.accept_client()

            if client_socket is None:
                logger.error("无法接受客户端连接")
                sys.exit(1)

            logger.info(f"✓ 客户端已连接")
            logger.info("")
            logger.info("开始接收和处理帧...")
            logger.info("-" * 60)

            # 主循环：接收、检测、跟踪、输出
            frame_count = 0
            start_time = time.time()

            # 🔍 调试模式：只处理特定帧范围
            DEBUG_START_FRAME = 515
            DEBUG_END_FRAME = 516
            debug_mode = False  # 关闭调试模式，处理整个视频

            for jpeg_data in receiver.receive_frames_stream(client_socket):
                frame_count += 1

                # 🔍 调试模式：只处理指定帧范围
                if debug_mode and (frame_count < DEBUG_START_FRAME or frame_count > DEBUG_END_FRAME):
                    continue

                # 🔍 调试模式：帧范围开始标记
                if debug_mode and frame_count == DEBUG_START_FRAME:
                    print(f"\n{'='*80}")
                    print(f"🔍 调试模式：开始处理第 {DEBUG_START_FRAME}-{DEBUG_END_FRAME} 帧")
                    print(f"{'='*80}\n")

                try:
                    # 解码JPEG数据
                    import cv2
                    import numpy as np
                    frame = cv2.imdecode(
                        np.frombuffer(jpeg_data, dtype=np.uint8),
                        cv2.IMREAD_COLOR
                    )

                    if frame is None:
                        logger.warning(f"第 {frame_count} 帧：JPEG解码失败")
                        continue

                    # 人脸检测
                    inference_start = time.time()
                    detections = detector.detect(frame)
                    inference_time = (time.time() - inference_start) * 1000  # 毫秒

                    # 目标跟踪
                    tracked_detections = tracker.update(detections)

                    # 获取统计信息
                    active_count = tracker.get_active_track_count()
                    total_count = tracker.get_total_person_count()
                    alerts = tracker.get_current_alerts()

                    # 打印结果
                    logger.info(
                        f"第 {frame_count:4d} 帧 | "
                        f"检测: {len(detections)} 人 | "
                        f"跟踪: {active_count} 目标 | "
                        f"累计: {total_count} 人 | "
                        f"推理: {inference_time:.1f} ms"
                    )

                    # 处理报警
                    if alerts:
                        for alert in alerts:
                            logger.warning(
                                f"  ⚠ 异常停留报警 | "
                                f"ID: {alert.track_id} | "
                                f"位置: ({alert.center[0]:.0f}, {alert.center[1]:.0f}) | "
                                f"停留: {alert.dwell_duration:.1f} 秒"
                            )

                    # 绘制并保存
                    output_path = result_writer.process_and_save(
                        frame,
                        tracked_detections,
                        frame_number=frame_count,
                        total_count=total_count,
                        active_count=active_count
                    )

                    logger.debug(f"已保存: {output_path.name}")

                except Exception as e:
                    logger.error(f"处理第 {frame_count} 帧时发生错误: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            logger.info("-" * 60)
            logger.info(f"客户端连接断开")
            logger.info(f"总共处理 {frame_count} 帧")

            elapsed = time.time() - start_time
            if elapsed > 0:
                avg_fps = frame_count / elapsed
                logger.info(f"平均处理帧率: {avg_fps:.2f} FPS")
                logger.info(f"总耗时: {elapsed:.2f} 秒")

            # 最终统计
            logger.info("")
            logger.info("=" * 60)
            logger.info("最终统计")
            logger.info("=" * 60)
            logger.info(f"总处理帧数: {frame_count}")
            logger.info(f"累计人流量: {tracker.get_total_person_count()} 人")
            logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.info("\n用户中断")
    except Exception as e:
        logger.error(f"运行时错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("边缘侧设备B 正常退出")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
