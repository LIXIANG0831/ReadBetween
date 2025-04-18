from pydantic import BaseModel, Field


class VoiceAgentCreate(BaseModel):
    agent_name: str = Field("LIXIANG's 个人助理", examples=["LIXIANG's 个人助理"], description="语言助手名称")
    prompt: str = Field("You are a voice assistant created by 李响. Your interface with users will be voice.", examples=["You are a voice assistant created by 李响. Your interface with users will be voice."], description="语音助手角色系统提示词")
    welcome_words: str = Field("你好, 今天过的怎么样?", examples=["你好, 今天过的怎么样?"], description="语言助手开场欢迎词")


class VoiceAgentInfo(BaseModel):
    task_id: str = Field(..., examples=["abcdefghijklmn"], description="后台任务ID")
    voice_agent_token: str = Field(..., examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiMTExIiwidmlkZW8iOnsicm9vbUpvaW4iOnRydWUsInJvb20iOiIyM"], description="LiveKit Token")
