#!/bin/bash
#
# 下载测试视频文件
#
# 下载Intel的sample-videos作为测试素材
#

set -e

VIDEOS_DIR="../test_videos"
mkdir -p "$VIDEOS_DIR"

echo "========================================"
echo "下载测试视频文件"
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
        wget --progress=bar:force -O "$output" "$url"
    else
        curl -L --progress-bar -o "$output" "$url"
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}下载完成: $(basename "$output")${NC}"
        echo -e "文件大小: $(du -h "$output" | cut -f1)"
    else
        echo -e "${RED}下载失败: $(basename "$output")${NC}"
        return 1
    fi
}

# 下载示例视频（质量较低，适合快速测试）
download_sample_videos() {
    echo -e "\n${YELLOW}=== 下载Intel sample-videos（测试用） ===${NC}"

    # 小视频文件用于快速测试
    local SMALL_MP4_URL="https://github.com/intel-iot-devkit/sample-videos/raw/master/head-pose-face-detection-female-and-male.mp4"
    local SMALL_MP4_OUTPUT="$VIDEOS_DIR/test-small.mp4"

    # 中等大小视频
    local MEDIUM_MP4_URL="https://github.com/intel-iot-devkit/sample-videos/raw/master/face-detector-0.mp4"
    local MEDIUM_MP4_OUTPUT="$VIDEOS_DIR/test-medium.mp4"

    download_file "$SMALL_MP4_URL" "$SMALL_MP4_OUTPUT"
    download_file "$MEDIUM_MP4_URL" "$MEDIUM_MP4_OUTPUT"
}

# 下载高分辨率测试视频（可选）
download_large_videos() {
    echo -e "\n${YELLOW}=== 下载大分辨率测试视频（耗时较长） ===${NC}"

    local LARGE_MP4_URL="https://github.com/intel-iot-devkit/sample-videos/raw/master/person-bicycle-car-detection.mp4"
    local LARGE_MP4_OUTPUT="$VIDEOS_DIR/test-large.mp4"

    download_file "$LARGE_MP4_URL" "$LARGE_MP4_OUTPUT"
}

# 创建自己的测试视频提示
create_custom_video_hint() {
    echo -e "\n${YELLOW}提示: 您也可以使用自己的视频文件进行测试${NC}"
    echo "支持格式: MP4, AVI, MOV 等"
    echo "建议参数:"
    echo "  - 分辨率: 640x480 或更低"
    echo "  - 编码: H.264"
    echo "  - 帧率: 15-30 FPS"
    echo ""
    echo "将您的视频文件复制到: $VIDEOS_DIR/"
}

# 主函数
main() {
    check_download_tool

    echo -e "\n${YELLOW}请选择要下载的视频:${NC}"
    echo "1) 小型测试视频（推荐，快速测试）"
    echo "2) 大型测试视频（完整测试，耗时较长）"
    echo "3) 全部下载"
    read -p "请输入选项 [1-3]: " choice

    case $choice in
        1)
            download_sample_videos
            ;;
        2)
            download_large_videos
            ;;
        3)
            download_sample_videos
            download_large_videos
            ;;
        *)
            echo -e "${RED}无效选项，退出。${NC}"
            exit 1
            ;;
    esac

    create_custom_video_hint

    echo -e "\n${GREEN}========================================"
    echo "视频下载完成！"
    echo "========================================${NC}"
}

main
