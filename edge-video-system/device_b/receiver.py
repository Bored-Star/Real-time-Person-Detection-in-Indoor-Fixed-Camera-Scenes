"""
TCP接收模块。

职责：监听TCP端口，接收设备A发送的帧数据，解析长度前缀协议。

输入：
- host: 监听IP地址（通常为0.0.0.0）
- port: 监听端口

输出：
- yield frame_bytes: 逐帧返回JPEG字节数据

设计决策：
- 使用长度前缀协议解析帧边界
- 支持多客户端连接（可选）
- 处理接收超时和连接断开
"""

import socket
import struct


class FrameReceiver:
    """帧接收器类，负责TCP监听和数据接收。"""

    def __init__(self, host: str, port: int, timeout: float = 30.0):
        """
        初始化接收器。

        Args:
            host: 监听地址
            port: 监听端口
            timeout: 接收超时时间（秒）
        """
        pass

    def start(self) -> socket.socket:
        """
        启动监听并等待客户端连接。

        Returns:
            socket.socket: 客户端连接socket
        """
        pass

    def receive_frame(self, client_socket: socket.socket) -> bytes:
        """
        接收单帧数据（长度前缀协议）。

        Args:
            client_socket: 客户端socket

        Returns:
            bytes: JPEG帧字节数据，连接断开时返回None
        """
        pass

    def _recv_exact(self, sock: socket.socket, size: int) -> bytes:
        """
        精确接收指定字节数。

        Args:
            sock: socket对象
            size: 要接收的字节数

        Returns:
            bytes: 接收到的数据
        """
        pass

    def close(self):
        """关闭监听socket。"""
        pass
