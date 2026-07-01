#!/bin/bash
# 下载OpenCV DNN人脸检测模型脚本

set -e

echo "开始下载OpenCV DNN人脸检测模型..."

# 创建models目录
mkdir -p models

# 下载OpenCV Yunet人脸检测模型（推荐，ONNX格式）
echo "下载Yunet模型..."
if [ ! -f "models/face_detection_yunet_2023mar.onnx" ]; then
    curl -L -o models/face_detection_yunet_2023mar.onnx \
        "https://github.com/opencv/opencv_zoo/raw/master/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
    echo "✓ Yunet模型下载完成"
else
    echo "✓ Yunet模型已存在，跳过下载"
fi

# 备选：下载OpenCV Caffe版本的ResNet10 SSD模型
echo "下载ResNet10 SSD模型..."
if [ ! -f "models/res10_300x300_ssd_iter_140000.caffemodel" ]; then
    curl -L -o models/res10_300x300_ssd_iter_140000.caffemodel \
        "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
    echo "✓ ResNet10模型下载完成"
else
    echo "✓ ResNet10模型已存在，跳过下载"
fi

if [ ! -f "models/deploy.prototxt" ]; then
    curl -L -o models/deploy.prototxt \
        "https://github.com/opencv/opencv/raw/master/samples/dnn/face_detector/deploy.prototxt"
    echo "✓ 模型配置文件下载完成"
else
    echo "✓ 模型配置文件已存在，跳过下载"
fi

echo ""
echo "模型下载完成！"
echo "可用模型："
echo "  1. Yunet (ONNX): models/face_detection_yunet_2023mar.onnx"
echo "  2. ResNet10 SSD (Caffe): models/res10_300x300_ssd_iter_140000.caffemodel"
echo "     配置文件: models/deploy.prototxt"
echo ""
echo "推荐使用Yunet模型，性能更好且支持更多关键点。"
