#!/bin/bash
# 抖音分析工具启动脚本

set -e

# 切换到脚本所在目录
cd "$(dirname "$0")"

echo "================================"
echo "抖音分析工具"
echo "================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

echo "✓ Python 版本: $(python3 --version)"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo ""
echo "检查并安装依赖..."
pip install -q -r requirements.txt

# 检查配置文件
if [ ! -f "config.yaml" ]; then
    echo ""
    echo "错误：未找到 config.yaml 配置文件"
    exit 1
fi

# 检查 API Key
echo ""
echo "检查配置..."
if grep -q "your_tikhub_api_key_here" config.yaml; then
    echo "⚠ 警告：请先在 config.yaml 中配置 TikHub API Key"
    echo "获取地址：https://tikhub.io"
fi

if grep -q "your_openclaw_token_here" config.yaml; then
    echo "⚠ 警告：请先在 config.yaml 中配置 OpenClaw API Token"
fi

# 运行分析
echo ""
echo "================================"
echo "开始分析..."
echo "================================"
echo ""

# 如果有参数，使用参数作为关键词，否则使用配置文件中的默认值
python3 douyin-analyzer.py "$@"
