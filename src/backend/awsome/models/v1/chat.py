from pydantic import BaseModel, field_validator, Field
from typing import Optional, List


class Message(BaseModel):
    role: str = Field(..., description="角色，可以是 'user' 或 'assistant'")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="对话历史")
    stream: bool = Field(False, description="是否启用流式输出")
    temperature: float = Field(1.0, ge=0, le=2, description="控制生成文本的随机性")
    max_tokens: Optional[int] = Field(None, description="生成的最大 token 数量")
    # model: str = Field("gpt-3.5-turbo", description="使用的模型名称")
