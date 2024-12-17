#!/bin/bash

# 确保log文件夹存在
mkdir -p log

# 查找端口对应PID
AGENT_PID=$(lsof -t -i:8808)
LIVEKIT_PID=$(lsof -t -i:7880)

# 如果找到进程则杀死AGENT_PID
if [ -n "$AGENT_PID" ]; then
    echo "杀死Agent进程 $AGENT_PID"
    kill -9 $AGENT_PID
else
    echo "没有进程在端口8808"
fi

# 如果找到进程则杀死LIVEKIT_PID
if [ -n "$LIVEKIT_PID" ]; then
    echo "杀死LiveKit进程 $LIVEKIT_PID"
    kill -9 $LIVEKIT_PID
else
    echo "没有进程在端口7880"
fi

echo "==============启动LIVEKIT服务"
livekit-server --bind 0.0.0.0 --dev &> log/livekit.log &
echo "==============启动AGENT服务+接口服务"
uvicorn server:app --reload --port 8808 &> log/server.log &
python agent.py start &> log/agent.log &


