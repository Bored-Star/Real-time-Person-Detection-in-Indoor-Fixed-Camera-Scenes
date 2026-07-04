"""
端侧设备A主程序入口。

职责：解析命令行参数，协调各模块完成视频采集、处理和发送。

命令行参数：
    --video: 视频文件路径
    --host: 边缘设备B的地址
    --port: 边缘设备B的端口
    --fps: 目标发送帧率
    --size: 目标帧尺寸 (WIDTHxHEIGHT)
    --quality: JPEG压缩质量

设计决策：
- 使用argparse解析参数
- 主循环中处理异常和重连
- 提供详细的运行日志
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from capture import VideoCapture
from preprocess import FramePreprocessor
from sender import FrameSender


def parse_arguments():
    """
    解析命令行参数。

    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description="端侧设备A - 视频采集、处理和发送"
    )

    parser.add_argument(
        "--video",
        type=str,
        required=True,
        help="视频文件路径"
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="边缘设备B的地址（默认：127.0.0.1）"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=6006,
        help="边缘设备B的端口（默认：6006）"
    )

    parser.add_argument(
        "--fps",
        type=int,
        default=5,
        help="目标发送帧率（默认：5 FPS）"
    )

    parser.add_argument(
        "--size",
        type=str,
        default="640x480",
        help="目标帧尺寸 WIDTHxHEIGHT（默认：640x480）"
    )

    parser.add_argument(
        "--quality",
        type=int,
        default=80,
        help="JPEG压缩质量 0-100（默认：80）"
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


def validate_video_path(video_path: str) -> bool:
    """
    验证视频文件路径有效性。

    Args:
        video_path: 视频文件路径

    Returns:
        文件存在且可读返回True，否则返回False
    """
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"错误：视频文件不存在: {video_path}")
        return False

    if not video_file.is_file():
        print(f"错误：路径不是文件: {video_path}")
        return False

    return True


def parse_size_string(size_str: str) -> tuple[int, int]:
    """
    解析尺寸字符串（如"640x480"）。

    Args:
        size_str: 尺寸字符串

    Returns:
        (width, height) 元组
    """
    try:
        parts = size_str.lower().split('x')
        if len(parts) != 2:
            raise ValueError()

        width = int(parts[0])
        height = int(parts[1])

        if width <= 0 or height <= 0:
            raise ValueError()

        return (width, height)

    except Exception:
        print(f"错误：无效的尺寸格式: {size_str}")
        print("正确格式: WIDTHxHEIGHT (例如: 640x480)")
        sys.exit(1)


def main():
    """主函数：协调各模块完成端侧设备A的所有工作。"""
    # 解析参数
    args = parse_arguments()

    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("端侧设备A 启动")
    logger.info("=" * 60)
    logger.info(f"视频文件: {args.video}")
    logger.info(f"目标服务器: {args.host}:{args.port}")
    logger.info(f"目标帧率: {args.fps} FPS")
    logger.info(f"目标尺寸: {args.size}")
    logger.info(f"JPEG质量: {args.quality}")
    logger.info("=" * 60)

    # 验证视频文件
    if not validate_video_path(args.video):
        logger.error("视频文件验证失败")
        sys.exit(1)

    # 解析目标尺寸
    target_size = parse_size_string(args.size)

    # 创建预处理器
    preprocessor = FramePreprocessor(
        target_size=target_size,
        jpeg_quality=args.quality
    )

    # 创建发送器
    sender = FrameSender(
        server_host=args.host,
        server_port=args.port,
        reconnect_interval=5.0,
        timeout=10.0
    )

    # 连接服务器
    logger.info("连接到服务器...")
    if not sender.connect():
        logger.error(f"无法连接到服务器: {args.host}:{args.port}")
        sys.exit(1)

    logger.info(f"✓ 已连接到服务器: {args.host}:{args.port}")

    # 打开视频文件
    logger.info("打开视频文件...")
    try:
        with VideoCapture(args.video, target_fps=args.fps) as capture:
            original_fps = capture.get_original_fps()
            frame_size = capture.get_frame_size()

            logger.info(f"✓ 视频已打开")
            logger.info(f"  原始帧率: {original_fps:.2f} FPS")
            logger.info(f"  原始尺寸: {frame_size[0]} x {frame_size[1]}")
            logger.info(f"  帧间隔: {capture.frame_interval}")
            logger.info("")

            # 主循环：读取、处理、发送
            frame_count = 0
            start_time = time.time()

            logger.info("开始处理和发送视频...")
            logger.info("-" * 60)

            for frame in capture.frames_generator():
                frame_count += 1

                try:
                    # 预处理帧
                    jpeg_data = preprocessor.process(frame)

                    # 发送帧
                    success = sender.send_frame(jpeg_data)

                    if success:
                        # 计算实时帧率
                        elapsed = time.time() - start_time
                        current_fps = frame_count / elapsed if elapsed > 0 else 0

                        logger.info(
                            f"已发送第 {frame_count:4d} 帧 | "
                            f"大小: {len(jpeg_data):6,} 字节 | "
                            f"实时帧率: {current_fps:.2f} FPS"
                        )
                    else:
                        logger.error(f"发送第 {frame_count} 帧失败")
                        logger.error("连接中断，尝试重连...")

                        # 尝试重连
                        if sender.reconnect_loop(max_attempts=3):
                            logger.info("重连成功，重新发送当前帧...")
                            # 重新发送当前帧
                            if not sender.send_frame(jpeg_data):
                                logger.error("重连后发送失败，退出")
                                break
                        else:
                            logger.error("重连失败，退出")
                            break

                except Exception as e:
                    logger.error(f"处理帧时发生错误: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            logger.info("-" * 60)
            logger.info(f"视频处理完成")
            logger.info(f"总共发送 {frame_count} 帧")

            elapsed = time.time() - start_time
            if elapsed > 0:
                avg_fps = frame_count / elapsed
                logger.info(f"平均发送帧率: {avg_fps:.2f} FPS")
                logger.info(f"总耗时: {elapsed:.2f} 秒")

    except IOError as e:
        logger.error(f"打开视频文件失败: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"运行时错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 断开连接
        sender.disconnect()
        logger.info("连接已关闭")

    logger.info("=" * 60)
    logger.info("端侧设备A 正常退出")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
