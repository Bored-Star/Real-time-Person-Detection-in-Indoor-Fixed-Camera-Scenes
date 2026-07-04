#!/bin/bash
#
# 下载OpenCV DNN人脸检测模型
#
# 支持的模型：
#   - YuNet (推荐，轻量级，精度高)
#   - ResNet SSD (精度更高，速度较慢)
#

set -e

MODELS_DIR="../models"
mkdir -p "$MODELS_DIR"

echo "========================================"
echo "下载人脸检测模型"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检测下载工具
check_download_tool() {
    if command -v wget >/dev/null 2>&1; then
        DOWNLOAD_TOOL="wget"
    elif command -v curl >/dev/null 2>&1; then
        DOWNLOAD_TOOL="curl"
    else
        echo -e "${RED}错误: 未找到 wget 或 curl，请先安装其中一个。${NC}"
        exit 1
    fi
    echo -e "${GREEN}使用下载工具: $DOWNLOAD_TOOL${NC}"
}

# 下载函数
download_file() {
    local url=$1
    local output=$2

    echo -e "${YELLOW}正在下载: $(basename "$output")${NC}"

    if [ "$DOWNLOAD_TOOL" = "wget" ]; then
        wget -O "$output" "$url"
    else
        curl -L -o "$output" "$url"
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}下载完成: $(basename "$output")${NC}"
    else
        echo -e "${RED}下载失败: $(basename "$output")${NC}"
        return 1
    fi
}

# 下载YuNet模型（推荐）
download_yunet() {
    echo -e "\n${YELLOW}=== 下载 YuNet 模型 ===${NC}"

    # YuNet 模型（OpenCV官方 Zoo 2023版本）
    local YUNET_URL="https://github.com/opencv/opencv_zoo/blob/master/models/face_detection_yunet/face_detection_yunet_2023mar.onnx?raw=true"
    local YUNET_OUTPUT="$MODELS_DIR/face_detection_yunet_2023mar.onnx"

    download_file "$YUNET_URL" "$YUNET_OUTPUT"

    echo -e "${GREEN}YuNet 模型下载完成！${NC}"
    echo -e "模型文件: $YUNET_OUTPUT"
    echo -e "模型大小: $(du -h "$YUNET_OUTPUT" | cut -f1)"
}

# 下载ResNet10 SSD模型
download_resnet_ssd() {
    echo -e "\n${YELLOW}=== 下载 ResNet10 SSD 模型 ===${NC}"

    # ResNet10 SSD 模型（OpenCV DNN示例模型）
    local RESNET_WEIGHTS_URL="https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
    local RESNET_PROTO_URL="https://github.com/opencv/opencv/raw/master/samples/dnn/face_detector/deploy.prototxt"

    local WEIGHTS_OUTPUT="$MODELS_DIR/res10_300x300_ssd_iter_140000.caffemodel"
    local PROTO_OUTPUT="$MODELS_DIR/deploy.prototxt"

    download_file "$RESNET_WEIGHTS_URL" "$WEIGHTS_OUTPUT"
    download_file "$RESNET_PROTO_URL" "$PROTO_OUTPUT"

    echo -e "${GREEN}ResNet10 SSD 模型下载完成！${NC}"
    echo -e "模型文件: $WEIGHTS_OUTPUT"
    echo -e "配置文件: $PROTO_OUTPUT"
}

# 主函数
main() {
    check_download_tool

    echo -e "\n${YELLOW}请选择要下载的模型:${NC}"
    echo "1) YuNet (推荐，轻量级，适合边缘设备)"
    echo "2) ResNet10 SSD (精度更高，速度较慢)"
    echo "3) 全部下载"
    read -p "请输入选项 [1-3]: " choice

    case $choice in
        1)
            download_yunet
            ;;
        2)
            download_resnet_ssd
            ;;
        3)
            download_yunet
            download_resnet_ssd
            ;;
        *)
            echo -e "${RED}无效选项，退出。${NC}"
            exit 1
            ;;
    esac

    echo -e "\n${GREEN}========================================"
    echo "模型下载完成！"
    echo "========================================${NC}"
}

main
