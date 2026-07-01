"""
TCP发送模块。

职责：建立TCP连接，将压缩后的帧数据发送给设备B，处理断线重连。

输入：
- host: 设备B的IP地址
- port: 设备B的监听端口
- frame_bytes: JPEG压缩后的帧字节数据

输出：
- 发送成功返回True，失败返回False

设计决策：
- 使用长度前缀协议：4字节大端无符号整数 + 数据体
- 支持断线自动重连（指数退避策略）
- 发送线程与主线程分离，避免阻塞
"""

import socket
import struct
import time


class FrameSender:
    """帧发送器类，负责TCP连接管理和数据发送。"""

    def __init__(self, host: str, port: int, max_retries: int = 5,
                 retry_delay: float = 1.0):
        """
        初始化发送器。

        Args:
            host: 目标主机IP
            port: 目标端口
            max_retries: 最大重连次数
            retry_delay: 初始重连延迟（秒）
        """
        pass

    def connect(self) -> bool:
        """
        建立TCP连接。

        Returns:
            bool: 连接成功返回True
        """
        pass

    def send_frame(self, frame_bytes: bytes) -> bool:
        """
        发送单帧数据。

        Args:
            frame_bytes: JPEG压缩的帧字节数据

        Returns:
            bool: 发送成功返回True
        """
        pass

    def _send_with_length_prefix(self, data: bytes) -> bool:
        """
        使用长度前缀协议发送数据。

        Args:
            data: 要发送的数据

        Returns:
            bool: 发送成功返回True
        """
        pass

    def reconnect(self) -> bool:
        """
        断线重连逻辑（指数退避）。

        Returns:
            bool: 重连成功返回True
        """
        pass

    def close(self):
        """关闭连接。"""
        pass
