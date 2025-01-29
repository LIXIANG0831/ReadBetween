from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


class Message(BaseModel):
    role: str = Field(..., description="角色，可以是 'user' 或 'assistant'")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="对话历史")
    stream: bool = Field(False, description="是否启用流式输出")
    temperature: float = Field(1.0, ge=0, le=2, description="控制生成文本的随机性")
    max_tokens: Optional[int] = Field(None, ge=1, description="生成的最大 token 数量")
    model: Optional[str] = Field("gpt-3.5-turbo", description="使用的模型名称")


class ChatCreate(BaseModel):
    # user_id: str = Field(..., description="用户 ID")
    title: Optional[str] = Field("新对话", description="对话标题")
    model: str = Field("gemini-2.0-flash-exp", description="使用的模型名称")  # 从默认系统配置模型进行获取
    system_prompt: str = Field("你是一个有用的助手", description="系统提示")
    temperature: float = Field(0.3, ge=0, le=2, description="控制生成文本的随机性")
    knowledge_base_ids: Optional[List[str]] = Field(default=[], description="绑定的知识库ID列表")

class ChatUpdate(BaseModel):
    conv_id: str = Field(..., description="对话 ID")
    title: Optional[str] = Field(None, description="对话标题")
    system_prompt: Optional[str] = Field(None, description="系统提示")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="控制生成文本的随机性")
    knowledge_base_ids: Optional[List[str]] = Field([], description="绑定的知识库ID列表")



class ChatMessageSend(BaseModel):
    conv_id: str = Field(..., description="对话 ID")
    message: str = Field(..., description="消息内容")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="控制生成文本的随机性")
    max_tokens: Optional[int] = Field(None, ge=1, description="生成的最大 token 数量")


class ConversationOut(BaseModel):
    id: str = Field(..., description="对话 ID")
    title: str = Field(..., description="对话标题")
    model: str = Field(..., description="使用的模型名称")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class MessageOut(BaseModel):
    role: str = Field(..., description="角色，可以是 'user' 或 'assistant'")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(..., description="消息时间戳")