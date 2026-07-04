"""
TCP接收模块。

职责：监听TCP连接，接收长度前缀分帧的帧数据。

输入：TCP网络流
输出：JPEG压缩的帧字节数据

设计决策：
- 使用长度前缀分帧协议（4字节大端无符号整数 + 数据）
- 支持多个客户端连接（可选）
- 处理接收超时和连接断开
"""

import socket
import struct
from typing import Generator, Optional


class FrameReceiver:
    """帧接收器类，负责监听和接收帧数据。"""

    def __init__(self,
                 bind_host: str = "0.0.0.0",
                 bind_port: int = 6006,
                 timeout: float = 30.0):
        """
        初始化帧接收器。

        Args:
            bind_host: 绑定地址，"0.0.0.0"表示所有接口
            bind_port: 绑定端口
            timeout: 接收超时时间（秒）
        """
        self.bind_host = bind_host
        self.bind_port = bind_port
        self.timeout = timeout
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False

    def start(self) -> None:
        """启动服务器，开始监听。"""
        try:
            # 创建socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # 绑定地址
            self.server_socket.bind((self.bind_host, self.bind_port))

            # 开始监听
            self.server_socket.listen(1)
            self.is_running = True

            print(f"服务器已启动: {self.bind_host}:{self.bind_port}")

        except Exception as e:
            raise RuntimeError(f"服务器启动失败: {e}")

    def stop(self) -> None:
        """停止服务器，关闭所有连接。"""
        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except Exception:
                pass
            finally:
                self.server_socket = None
                self.is_running = False

    def accept_client(self) -> Optional[socket.socket]:
        """
        接受一个客户端连接（阻塞）。

        Returns:
            客户端socket，失败返回None
        """
        if not self.is_running or self.server_socket is None:
            return None

        try:
            print(f"等待客户端连接到 {self.bind_host}:{self.bind_port}...")
            client_socket, client_address = self.server_socket.accept()
            print(f"客户端已连接: {client_address[0]}:{client_address[1]}")

            # 设置超时
            client_socket.settimeout(self.timeout)

            return client_socket

        except Exception as e:
            print(f"接受连接失败: {e}")
            return None

    def receive_frame(self, client_socket: socket.socket) -> Optional[bytes]:
        """
        从客户端接收一帧数据。

        Args:
            client_socket: 客户端socket

        Returns:
            帧字节数据，连接断开或出错返回None
        """
        if client_socket is None:
            return None

        try:
            # 先接收4字节长度前缀
            length_prefix = self._recv_exact(client_socket, 4)
            if length_prefix is None:
                return None

            # 解包长度
            frame_length = struct.unpack('>I', length_prefix)[0]

            # 验证长度（防止恶意数据）
            if frame_length == 0:
                print(f"收到空帧")
                return b''

            if frame_length > 10 * 1024 * 1024:  # 10MB限制
                print(f"帧长度过大: {frame_length} 字节")
                return None

            # 接收指定长度的帧数据
            frame_data = self._recv_exact(client_socket, frame_length)
            if frame_data is None:
                return None

            return frame_data

        except socket.timeout:
            print(f"接收超时")
            return None
        except Exception as e:
            print(f"接收帧失败: {e}")
            return None

    def _recv_exact(self, sock: socket.socket, length: int) -> Optional[bytes]:
        """
        精确接收指定长度的数据（处理不完整接收）。

        Args:
            sock: socket对象
            length: 要接收的字节数

        Returns:
            接收到的数据，连接中断或出错返回None
        """
        if length == 0:
            return b''

        data = b''
        remaining = length

        while remaining > 0:
            try:
                chunk = sock.recv(remaining)
                if not chunk:
                    # 连接中断
                    print(f"连接中断，已接收 {len(data)}/{length} 字节")
                    return None

                data += chunk
                remaining -= len(chunk)

            except socket.timeout:
                print(f"接收超时，已接收 {len(data)}/{length} 字节")
                return None
            except Exception as e:
                print(f"接收数据失败: {e}")
                return None

        return data

    def receive_frames_stream(self,
                              client_socket: socket.socket
                              ) -> Generator[bytes, None, None]:
        """
        生成器函数，持续接收帧直到连接断开。

        Args:
            client_socket: 客户端socket

        Yields:
            帧字节数据
        """
        if client_socket is None:
            return

        frame_count = 0
        while True:
            frame_data = self.receive_frame(client_socket)

            if frame_data is None:
                # 连接断开或出错
                print(f"接收流结束，共接收 {frame_count} 帧")
                break

            frame_count += 1
            yield frame_data

    def __enter__(self):
        """支持with语句的上下文管理入口。"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持with语句的上下文管理出口。"""
        self.stop()
        return False  # 不抑制异常
