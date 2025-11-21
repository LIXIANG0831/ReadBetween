from fastapi import APIRouter, Depends
from livekit import api as livekit_api

from readbetween.config import Settings
from readbetween.core.dependencies import get_settings

router = APIRouter(tags=["LiveKit(VoiceAgent)相关"])


@router.get("/get_voice_token")
async def get_voice_token(name: str, room: str, settings: Settings = Depends(get_settings)):
    livekit_token = livekit_api.AccessToken(settings.livekit.api_key, settings.livekit.api_secret) \
        .with_identity("identity") \
        .with_name(f"{name}") \
        .with_grants(livekit_api.VideoGrants(
        room_join=True,
        room=f"{room}",
    ))
    # name 进入livekit room的名字
    # identity 用户的用户名、用户ID或者其他任何可以唯一标识用户身份的字符串
    # grants 所授予的进入livekit room的权限
    return {"token": livekit_token.to_jwt()}
