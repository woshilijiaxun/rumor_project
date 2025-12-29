#!/bin/bash

# 启动后端服务脚本

echo "=========================================="
echo "启动 Flask 后端服务"
echo "=========================================="

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ 虚拟环境已激活"
else
    echo "✗ 未找到虚拟环境，请先创建虚拟环境"
    exit 1
fi

# 进入后端目录
cd backend

# 检查依赖
echo "检查 Python 依赖..."
pip install -q -r requirements.txt

# 运行 Flask 应用
echo "启动 Flask 服务器..."
echo "后端服务地址: http://localhost:5001"
echo "按 Ctrl+C 停止服务"
echo "=========================================="
python app.py

