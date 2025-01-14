import asyncio
import os
import threading
import uuid
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException

from awsome.models.v1.voice_agent import VoiceAgentInfo, VoiceAgentCreate
from awsome.utils.logger_util import logger_util
from awsome.settings import get_config
from livekit import api
from awsome.services.voice_agent import VoiceAgentService
from awsome.models.schemas.response import resp_200, resp_500

router = APIRouter(tags=["实时语音"])

LIVEKIT_API_KEY = get_config("api.livekit.livekit_api_key")
LIVEKIT_API_SECRET = get_config("api.livekit.livekit_api_secret")

# 全局任务字典
voice_agents_tasks: Dict[str, asyncio.Task] = {}


@router.get("/voice/get_token")
async def get_token(name: str, room: str, identity: str = "identity"):
    token = api.AccessToken(api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET) \
        .with_identity(f"{identity}") \
        .with_name(f"{name}") \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=f"{room}",
        ))
    # name 进入livekit room的名字
    # identity 用户的用户名、用户ID或者其他任何可以唯一标识用户身份的字符串
    # grants 所授予的进入livekit room的权限
    logger_util.debug(f"获取LiveKit Room Token: {token.to_jwt()}")
    return {"token": token.to_jwt()}


@router.post("/voice/create_agent")
async def create_agent(voice_agent_created: VoiceAgentCreate):
    try:
        # 只允许调用者进入使用
        room_uuid = str(uuid.uuid4())
        identity_uuid = str(uuid.uuid4())
        voice_agent_token = await get_token(name="李响", room=room_uuid, identity=identity_uuid)
        # 实例化voice_agent_service
        voice_agent_service = VoiceAgentService(agent_name=voice_agent_created.agent_name,
                                                prompt=voice_agent_created.prompt,
                                                welcome_words=voice_agent_created.welcome_words,
                                                participant_identity=identity_uuid)
        # 生成唯一的任务ID
        task_id = str(uuid.uuid4())
        # 后台任务运行voice_agent_service
        task = asyncio.create_task(voice_agent_service.run_voice_agent())
        # 用户对话 voice_agent token
        voice_agents_tasks[task_id] = task

        # 语言服务信息
        voice_info = VoiceAgentInfo(task_id=task_id, voice_agent_token=voice_agent_token.get("token"))
        return resp_200(data=voice_info)
    except Exception as e:
        logger_util.error(f"创建实时语音服务失败: {e}")
        return resp_500(message=str(e))


@router.post("/voice/cancel_agent/{task_id}")
async def cancel_agent(task_id: str):
    try:

        current_task = voice_agents_tasks.get(task_id)

        logger_util.debug(f"当前任务是否运行中:{not current_task.done()}")
        if not current_task or current_task.done() is True:
            raise HTTPException(status_code=404, detail="Task not found or already completed")

        # 如果任务正在运行，尝试取消它
        if current_task:
            current_task.cancel()  # 取消任务
            try:
                await current_task  # 等待任务处理取消
            except asyncio.CancelledError:
                pass

        # 从字典中删除任务
        del voice_agents_tasks[task_id]

        return resp_200(data={'task_id': f"{task_id}", 'message': 'Task stopped'})

    except Exception as e:
        logger_util.error(f"中断实时语音服务失败: {e}")
        return resp_500(message=str(e))
