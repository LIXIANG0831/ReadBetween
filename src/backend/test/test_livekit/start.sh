#!/bin/bash
cd ./voice_agent_backend
python agent.py dev &

cd ../voice_agent_frontend
pnpm dev &