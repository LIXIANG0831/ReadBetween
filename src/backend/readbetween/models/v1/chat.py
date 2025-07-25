from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from readbetween.models.dao import Conversation
from readbetween.models.v1.model_available_cfg import ModelAvailableCfgInfo


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
    available_model_id: str = Field("xxxx-xxxx-xxxx-xxxx", description="所使用的可用模型配置ID")
    system_prompt: str = Field("你是一个有用的助手", description="系统提示")
    temperature: float = Field(0.3, ge=0, le=2, description="控制生成文本的随机性")
    knowledge_base_ids: Optional[List[str]] = Field(default=[], description="绑定的知识库ID列表")
    use_memory: int = Field(default=0, description="是否使用记忆")
    mcp_server_configs: Optional[Dict] = Field(None, description="绑定所使用的MCPServer")


class ChatUpdate(BaseModel):
    conv_id: str = Field(..., description="对话 ID")
    title: Optional[str] = Field(None, description="对话标题")
    system_prompt: Optional[str] = Field(None, description="系统提示")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="控制生成文本的随机性")
    knowledge_base_ids: Optional[List[str]] = Field([], description="绑定的知识库ID列表")
    use_memory: Optional[int] = Field(default=None, description="是否使用记忆")
    available_model_id: Optional[str] = Field("xxxx-xxxx-xxxx-xxxx", description="所使用的可用模型配置ID")
    mcp_server_configs: Optional[Dict] = Field(None, description="绑定所使用的MCPServer")


class ChatMessageSend(BaseModel):
    conv_id: str = Field(..., description="对话 ID")
    message: str = Field(..., description="消息内容")
    temperature: Optional[float] = Field(0.3, ge=0, le=2, description="控制生成文本的随机性")
    max_tokens: Optional[int] = Field(2000, ge=1, description="生成的最大 token 数量")
    search: bool = Field(default=False, description="是否开启网络搜索")
    thinking: bool = Field(default=False, description="是否开启思考模式")


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


class ConversationInfo(BaseModel):
    conversation: Conversation = Field(..., description="会话")
    model_cfg: ModelAvailableCfgInfo = Field(..., description="当前会话渠道模型配置")


class ChatMessageSendPlus(ChatMessageSend):
    conversation_info: ConversationInfo = Field(..., description="当前会话渠道配置信息")
