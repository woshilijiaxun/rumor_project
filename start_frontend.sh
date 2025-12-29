#!/bin/bash

# 启动前端服务脚本

echo "=========================================="
echo "启动 Vue 前端服务"
echo "=========================================="

# 进入前端目录
cd frontend

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 启动开发服务器
echo "启动 Vite 开发服务器..."
echo "前端服务地址: http://localhost:5173"
echo "按 Ctrl+C 停止服务"
echo "=========================================="
npm run dev

