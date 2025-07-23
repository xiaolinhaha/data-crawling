#!/bin/bash

# 停止占用5005端口的进程
echo "正在检查并停止占用5005端口的进程..."
PORT=5005
PID=$(lsof -t -i:$PORT)

if [ -n "$PID" ]; then
    echo "发现占用$PORT端口的进程: $PID，正在停止..."
    kill -9 $PID
    echo "已停止进程: $PID"
else
    echo "没有进程占用$PORT端口"
fi

# 如果有旧的service.pid文件，也尝试停止其中记录的进程
if [ -f "service.pid" ]; then
    OLD_PID=$(cat service.pid)
    if [ -n "$OLD_PID" ]; then
        echo "尝试停止旧的服务进程: $OLD_PID"
        kill -9 $OLD_PID 2>/dev/null || echo "进程 $OLD_PID 已不存在"
    fi
fi

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export APP_HOST="0.0.0.0"
export APP_PORT=5005
export DEBUG_MODEL="True"

# 启动新进程
echo "正在启动新服务..."
nohup python app.py 2>&1 &
pid=$!
echo "${pid}" >service.pid
echo "服务已启动，进程ID: $pid"
