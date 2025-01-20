#!/bin/bash

# 激活虚拟环境
source /opt/homebrew/Caskroom/miniconda/base/bin/activate aw

# 获取当前脚本所在的目录（awsome 目录）
SCRIPT_DIR=$(dirname "$(realpath "$0")")

# 获取项目的根目录（awsome 的父目录）
PROJECT_DIR=$(dirname "$SCRIPT_DIR")

# 动态添加项目根目录到 PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$PROJECT_DIR

# 创建 logs/ 目录（如果不存在）
mkdir -p "$SCRIPT_DIR/logs"

# 启动多个 Celery worker
for i in {1..3}; do
    worker_name="worker${i}"
    log_file="$SCRIPT_DIR/logs/${worker_name}.log"
    celery -A awsome.core.celery_app worker -n "${worker_name}@%h" --loglevel=info --logfile="$log_file" &
done

echo "所有 Celery worker 已启动，日志保存在 $SCRIPT_DIR/logs/ 下。"