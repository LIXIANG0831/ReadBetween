#!/bin/bash

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