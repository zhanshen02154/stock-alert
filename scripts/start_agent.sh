#!/bin/bash

# 库存这个也是有启动脚本

echo "Starting Stock Helper Agent..."

# 检查依赖
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install it first."
    exit 1
fi

# 安装依赖
echo "Installing dependencies..."
uv sync

# 启动服务
echo "Starting agent service..."
uv run python -m src.main
