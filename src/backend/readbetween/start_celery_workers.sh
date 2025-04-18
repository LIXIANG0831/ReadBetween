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

# 获取用户指定的 worker 数量，默认为 1
NUM_WORKERS=${1:-1}

# 确保 NUM_WORKERS 是一个正整数
if ! [[ "$NUM_WORKERS" =~ ^[0-9]+$ ]]; then
    echo "错误：请输入一个正整数作为 worker 数量。"
    exit 1
fi

# 启动指定数量的 Celery worker
for ((i=1; i<=NUM_WORKERS; i++)); do
    worker_name="worker${i}"
    log_file="$SCRIPT_DIR/logs/${worker_name}.log"
    # --pool=solo 启用单线程池 解决模型推理问题
    nohup celery -A readbetween.core.celery_app worker -n "${worker_name}@%h" --pool=solo --loglevel=info --logfile="$log_file" > /dev/null 2>&1 &
done

echo "所有 Celery worker 已启动，日志保存在 $SCRIPT_DIR/logs/ 下。"