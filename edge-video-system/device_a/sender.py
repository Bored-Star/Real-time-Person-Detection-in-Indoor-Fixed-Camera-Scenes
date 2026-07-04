"""
TCP发送模块。

职责：建立TCP连接，发送压缩后的帧数据，处理断线重连。

输入：JPEG压缩的帧字节数据
输出：无（发送到网络）

设计决策：
- 使用长度前缀分帧协议（4字节大端无符号整数 + 数据）
- 实现断线自动重连机制
- 支持发送队列和流控
"""

import socket
import struct
import time
from typing import Optional


class FrameSender:
    """帧发送器类，负责TCP连接管理和数据发送。"""

    def __init__(self,
                 server_host: str,
                 server_port: int = 6006,
                 reconnect_interval: float = 5.0,
                 timeout: float = 10.0):
        """
        初始化帧发送器。

        Args:
            server_host: 服务器主机地址
            server_port: 服务器端口
            reconnect_interval: 重连间隔（秒）
            timeout: socket超时时间（秒）
        """
        self.server_host = server_host
        self.server_port = server_port
        self.reconnect_interval = reconnect_interval
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.is_connected_flag = False

    def connect(self) -> bool:
        """
        建立TCP连接。

        Returns:
            连接成功返回True，失败返回False
        """
        try:
            # 创建socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.socket.settimeout(self.timeout)

            # 连接服务器
            self.socket.connect((self.server_host, self.server_port))
            self.is_connected_flag = True
            return True

        except Exception as e:
            print(f"连接失败: {self.server_host}:{self.server_port} - {e}")
            self.is_connected_flag = False
            if self.socket is not None:
                self.socket.close()
                self.socket = None
            return False

    def disconnect(self):
        """断开连接并清理资源。"""
        if self.socket is not None:
            try:
                self.socket.close()
            except Exception:
                pass
            finally:
                self.socket = None
                self.is_connected_flag = False

    def send_frame(self, frame_data: bytes) -> bool:
        """
        发送一帧数据（长度前缀 + 数据）。

        Args:
            frame_data: JPEG压缩后的帧字节数据

        Returns:
            发送成功返回True，失败返回False
        """
        if not self.is_connected():
            return False

        try:
            # 打包4字节大端长度前缀
            length_prefix = struct.pack('>I', len(frame_data))

            # 发送长度前缀 + 数据
            self.socket.sendall(length_prefix + frame_data)
            return True

        except Exception as e:
            print(f"发送失败: {e}")
            self.is_connected_flag = False
            return False

    def is_connected(self) -> bool:
        """
        检查连接状态。

        Returns:
            已连接返回True，否则返回False
        """
        return self.is_connected_flag and self.socket is not None

    def reconnect_loop(self, max_attempts: int = 0) -> bool:
        """
        重连循环，直到成功或达到最大尝试次数。
        使用指数退避策略。

        Args:
            max_attempts: 最大尝试次数，0表示无限重试

        Returns:
            连接成功返回True，放弃重连返回False
        """
        attempt = 0
        # 指数退避：从1秒开始，最多5次，每次间隔翻倍
        backoff_intervals = [1.0, 2.0, 4.0, 8.0, 16.0]

        while True:
            attempt += 1

            # 检查是否超过最大尝试次数
            if max_attempts > 0 and attempt > max_attempts:
                print(f"重连失败：已达到最大尝试次数 {max_attempts}")
                return False

            # 计算退避时间
            if attempt <= len(backoff_intervals):
                wait_time = backoff_intervals[attempt - 1]
            else:
                wait_time = backoff_intervals[-1]  # 使用最大值

            print(f"重连尝试 {attempt}（等待 {wait_time} 秒）...")

            # 等待
            time.sleep(wait_time)

            # 尝试连接
            if self.connect():
                print(f"重连成功！")
                return True

    def __enter__(self):
        """支持with语句的上下文管理入口。"""
        if not self.connect():
            raise ConnectionError(f"无法连接到服务器: {self.server_host}:{self.server_port}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持with语句的上下文管理出口。"""
        self.disconnect()
        return False  # 不抑制异常
