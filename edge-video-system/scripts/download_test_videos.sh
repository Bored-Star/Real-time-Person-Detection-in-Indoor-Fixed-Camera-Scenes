#!/bin/bash
# 下载Intel sample-videos测试视频脚本

set -e

echo "开始下载测试视频..."

# 创建test_videos目录
mkdir -p test_videos

# 下载Intel sample-videos（短小精悍的测试视频）
echo "下载测试视频1: sample-5s.mp4..."
if [ ! -f "test_videos/sample-5s.mp4" ]; then
    curl -L -o test_videos/sample-5s.mp4 \
        "https://github.com/intel-iot-devkit/sample-videos/raw/master/sample-video.mp4"
    echo "✓ sample-5s.mp4 下载完成"
else
    echo "✓ sample-5s.mp4 已存在，跳过下载"
fi

echo "下载测试视频2: crowd-video.mp4..."
if [ ! -f "test_videos/crowd-video.mp4" ]; then
    curl -L -o test_videos/crowd-video.mp4 \
        "https://github.com/intel-iot-devkit/sample-videos/raw/master/crowd-video.mp4"
    echo "✓ crowd-video.mp4 下载完成"
else
    echo "✓ crowd-video.mp4 已存在，跳过下载"
fi

echo "下载测试视频3: head-pose-face-detection.mp4..."
if [ ! -f "test_videos/head-pose-face-detection.mp4" ]; then
    curl -L -o test_videos/head-pose-face-detection.mp4 \
        "https://github.com/intel-iot-devkit/sample-videos/raw/master/head-pose-face-detection.mp4"
    echo "✓ head-pose-face-detection.mp4 下载完成"
else
    echo "✓ head-pose-face-detection.mp4 已存在，跳过下载"
fi

echo ""
echo "测试视频下载完成！"
echo "可用测试视频："
echo "  1. test_videos/sample-5s.mp4 - 基础测试视频"
echo "  2. test_videos/crowd-video.mp4 - 人群场景测试"
echo "  3. test_videos/head-pose-face-detection.mp4 - 人脸检测专用"
echo ""
echo "使用示例："
echo '  python -m device_a.main --video test_videos/sample-5s.mp4 --host 192.168.1.100 --port 5000'
