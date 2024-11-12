from pydantic import BaseModel, field_validator, Field
from typing import Optional, List
from pydantic_core.core_schema import ValidationInfo


class Chat(BaseModel):
    query: str = Field(..., examples=["可以给我推荐一些海子的诗歌吗？"], description="用户问题")
    stream: Optional[bool] = Field(True, examples=[True], description="是否开启流式回复")
    temperature: Optional[float] = Field(0.1, examples=[0.1], description="模型回复文温度")
    messages: Optional[List[dict]] = Field([], examples=[[{"role": "user", "content": "你好"}, {"role": "assistant", "content": "你好！有什么我能帮助你的吗？"}]], description="历史会话列表")
    return_history: Optional[bool] = Field(True, examples=[True], description="是否返回历史会话列表")
    max_messages_cnt: Optional[int] = Field(20, examples=[20], description="历史会话最大保存条数 save_messages为True时生效")
    pretty_print: Optional[bool] = Field(False, examples=[False], description="是否启用简介输出形式")

    # save_messages为False时 不保存历史会话
    @classmethod
    @field_validator('return_history', 'max_messages_cnt')
    def check_max_messages_cnt(cls, v: str, info: ValidationInfo):
        check = cls.__fields__['return_history'].default
        if info.field_name == 'max_messages_cnt':
            if check is False:
                return 0
        return v
