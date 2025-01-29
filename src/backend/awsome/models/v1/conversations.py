from datetime import datetime
from typing import List
from pydantic import BaseModel, Field
from awsome.models.v1.chat import Message


class ConversationCreate(BaseModel):
    model: str = Field("gpt-3.5-turbo", description="使用的模型")
    system_prompt: str = Field("你是一个有用的助手", description="系统提示语")
    temperature: float = Field(0.7, ge=0, le=2, description="生成温度")


class ConversationResponse(BaseModel):
    id: str = Field(..., description="会话ID")
    created_at: datetime = Field(..., description="创建时间")
    model: str = Field(..., description="使用的模型")
    messages: List[Message] = Field(..., description="消息列表")
