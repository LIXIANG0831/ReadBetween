import asyncio
import json
from readbetween.utils.logger_util import logger_util
import openai
from readbetween.settings import get_config
from pydantic import BaseModel, field_validator
from typing import Optional, List

client = openai.Client(
    api_key=get_config("api.openai.api_key"),
    base_url=get_config("api.openai.base_url")
)

class Chat(BaseModel):
    query: str  # 用户问题
    stream: Optional[bool] = True  # 是否开启流式回复
    temperature: Optional[float] = 0.1  # Temperature
    messages: Optional[List[dict]] = []  # 会话列表
    save_messages: Optional[bool] = True  # 是否启用多轮会话 返回历史会话列表
    max_messages_cnt: Optional[int] = 20  # 历史会话最大保存条数 save_messages为True时生效
    pretty_print: Optional[bool] = False  # 输出形式

    # save_messages为False时 不保存历史会话
    @field_validator('max_messages_cnt', mode='before')
    def check_max_messages_cnt(cls, v, values):
        if values.get('save_messages') is False:
            return 0
        return v


async def chat(chat_request: Chat):
    async def generate():
        messages = chat_request.messages.copy()  # 复制现有的消息列表
        messages.append({"role": "user", "content": chat_request.query})
        try:
            response = client.chat.completions.create(
                model="gpt-4-32k",
                stream=chat_request.stream,
                temperature=chat_request.temperature,
                messages=messages,
            )

            answer = "" # 拼接模型响应

            if chat_request.stream:
                for chunk in response: # 处理流式响应
                    answer += chunk.choices[0].delta.content
                    if chat_request.pretty_print:
                        output = chunk.choices[0].delta.content
                        output and print(output)
                    else:
                        print(chunk.choices[0].delta.json())
                logger_util.info(f"\n用户询问:{chat_request.query}\n流式响应:{answer}")
            else:
                answer = response.choices[0].message.content
                if chat_request.pretty_print: # 处理非流式响应
                    print(response.choices[0].message.content)
                else:
                    print(response.choices[0].message.json())
                logger_util.info(f"\n用户询问:{chat_request.query}\n非流式响应:{answer}")


            if chat_request.save_messages:
                if len(messages) > chat_request.max_messages_cnt:
                    messages.pop(0)
                messages.append({"role": "assistant", "content": answer})
                history = {
                    "history": messages,
                }
                print(json.dumps(history, ensure_ascii=False))
        except Exception as e:
            logger_util.error(f"An error occurred: {e}")

    await generate()

if __name__ == '__main__':
    c = Chat(query="介绍一下你自己", save_messages=True)
    # c = Chat(query="介绍一下你自己", stream=False, save_messages=True, pretty_print=True)
    asyncio.run(chat(c))  # 使用 asyncio.run 来运行异步函数