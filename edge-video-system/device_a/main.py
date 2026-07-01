"""
设备A主程序入口。

职责：解析命令行参数，协调视频采集、预处理和网络发送模块。

命令行参数：
- --video: 视频文件路径
- --host: 设备B的IP地址
- --port: 设备B的监听端口
- --fps: 采样帧率
- --size: 目标图像尺寸 (如: 640x480)
- --quality: JPEG压缩质量

工作流程：
1. 解析命令行参数
2. 初始化视频采集器
3. 初始化TCP发送器并连接设备B
4. 逐帧采集 -> 预处理 -> 发送
5. 处理异常和优雅退出
"""

import argparse
from .capture import VideoCapture
from .preprocess import preprocess_frame
from .sender import FrameSender


def parse_args():
    """
    解析命令行参数。

    Returns:
        argparse.Namespace: 解析后的参数对象
    """
    pass


def main():
    """主函数：协调各模块完成端侧任务。"""
    pass


if __name__ == "__main__":
    main()
