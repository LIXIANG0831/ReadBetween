import os
from livekit import api
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# 允许所有来源的跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/getToken")
async def get_token(name: str, room: str):
    token = api.AccessToken(os.getenv('LIVEKIT_API_KEY'), os.getenv('LIVEKIT_API_SECRET')) \
        .with_identity("identity") \
        .with_name(f"{name}") \
        .with_grants(api.VideoGrants(
        room_join=True,
        room=f"{room}",
    ))
    # name 进入livekit room的名字
    # identity 用户的用户名、用户ID或者其他任何可以唯一标识用户身份的字符串
    # grants 所授予的进入livekit room的权限
    return {"token": token.to_jwt()}
