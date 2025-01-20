#!/bin/bash

# 打印一条消息，说明正在停止 Celery worker
echo "正在停止所有 Celery worker..."

# 查找所有 Celery worker 进程并发送 SIGTERM 信号
# 使用 pkill 来匹配包含 "celery worker" 的进程
pkill -f "celery worker"

# 等待 5 秒，确保大多数进程已经优雅退出
sleep 5

# 检查是否还有未退出的 Celery worker 进程
remaining_workers=$(pgrep -f "celery worker")

if [ -n "$remaining_workers" ]; then
    echo "仍有 Celery worker 未退出，正在强制终止..."
    # 强制终止剩余的 Celery worker 进程
    pkill -9 -f "celery worker"
else
    echo "所有 Celery worker 已成功停止。"
fi