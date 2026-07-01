# 端云协同视频流人脸检测系统

基于TCP通信的端云协同架构，实现实时视频流人脸检测、人流统计和异常停留报警。

## 系统架构

```
设备A（端侧）                          设备B（边缘侧）
─────────────────────────────────────────────────────────────
视频采集 → 帧采样 → JPEG压缩 → TCP发送 ━━┳→ TCP接收 → 解码
                                         ┃                ↓
                                         ┃            人脸检测推理
                                         ┃                ↓
                                         ┃            目标跟踪
                                         ┃                ↓
                                         ┃            结果输出/报警
                                         ┃
                                    ━━━━━━━━━━━━━━━━━━━━━━
```

### 设备A（端侧，能力较弱）
- **功能**：读取视频文件，进行帧采样和JPEG压缩，通过TCP发送给设备B
- **模块**：
  - `capture.py`：视频采集与帧采样
  - `preprocess.py`：图像缩放与JPEG压缩
  - `sender.py`：TCP发送与断线重连

### 设备B（边缘侧，能力较强）
- **功能**：接收帧数据，执行OpenCV DNN人脸检测推理，输出检测结果和报警
- **模块**：
  - `receiver.py`：TCP接收与帧解析
  - `detector.py`：人脸检测推理
  - `tracker.py`：目标跟踪与异常停留检测
  - `result_writer.py`：结果可视化与日志输出

### 通信协议
- **传输层**：TCP socket
- **分帧协议**：长度前缀（4字节大端无符号整数 + 帧数据）

## 部署步骤

### 前置要求
- Python 3.8+
- 两台设备或同一台设备的两个终端

### 1. 克隆项目
```bash
git clone <repository-url>
cd edge-video-system
```

### 2. 创建虚拟环境并安装依赖
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3. 下载模型文件
```bash
bash scripts/download_model.sh
```

模型文件将保存到 `models/` 目录。

### 4. 下载测试视频（可选）
```bash
bash scripts/download_test_videos.sh
```

测试视频将保存到 `test_videos/` 目录。

## 启动命令

### 设备B（边缘侧，先启动）
```bash
python -m device_b.main \
  --host 0.0.0.0 \
  --port 5000 \
  --model models/face_detection_yunet_2023mar.onnx \
  --config models/face_detection_yunet_2023mar.config \
  --output output_frames \
  --confidence 0.5 \
  --max-stay-time 10.0
```

参数说明：
- `--host`：监听IP地址（0.0.0.0表示所有接口）
- `--port`：监听端口
- `--model`：DNN模型文件路径
- `--config`：模型配置文件路径（如不需要可省略）
- `--output`：标注帧输出目录
- `--confidence`：检测置信度阈值（0-1）
- `--max-stay-time`：异常停留时间阈值（秒）

### 设备A（端侧）
```bash
python -m device_a.main \
  --video test_videos/sample-video.mp4 \
  --host <设备B的IP地址> \
  --port 5000 \
  --fps 5 \
  --size 640x480 \
  --quality 75
```

参数说明：
- `--video`：输入视频文件路径
- `--host`：设备B的IP地址
- `--port`：设备B的监听端口
- `--fps`：采样帧率（每秒提取的帧数）
- `--size`：目标图像尺寸（宽x高）
- `--quality`：JPEG压缩质量（1-100）

## 输出结果

### 实时日志
- 帧处理统计
- 人流计数（进入/离开/当前人数）
- 检测到的目标数量
- 异常停留报警

### 标注帧图像
保存到 `output_frames/` 目录，包含：
- 人脸边界框
- 目标ID和置信度
- 停留时间标注
- 报警高亮显示

## 性能优化建议

### 设备A（端侧）
- 降低采样帧率（`--fps 3`）
- 提高JPEG压缩（`--quality 60`）
- 减小目标尺寸（`--size 480x360`）

### 设备B（边缘侧）
- 提高检测置信度阈值（减少误检）
- 使用GPU版本的OpenCV（如有GPU）
- 调整IoU阈值和NMS参数

## 故障排查

### 连接失败
- 检查设备B是否先启动
- 确认IP地址和端口正确
- 检查防火墙设置

### 模型加载失败
- 确认模型文件路径正确
- 检查模型文件完整性
- 尝试重新下载模型

### 内存不足
- 减小目标图像尺寸
- 降低采样帧率
- 释放未使用的跟踪对象

## 系统要求

### 设备A（端侧）
- CPU：双核及以上
- 内存：2GB+
- 网络：局域网或稳定的互联网连接

### 设备B（边缘侧）
- CPU：四核及以上（推荐）
- 内存：4GB+
- 存储：2GB+（模型文件 + 输出帧）

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request。

## 联系方式

如有问题，请提交Issue或联系项目维护者。
