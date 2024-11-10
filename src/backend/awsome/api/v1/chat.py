import json
from fastapi.responses import StreamingResponse
from fastapi import HTTPException, APIRouter
from awsome.db.models.v1.chat import Chat
from awsome.utils.logger_client import logger_client
from awsome.settings import get_config
import openai

client = openai.Client(
    api_key=get_config("api.openai.api_key"),
    base_url=get_config("api.openai.base_url")
)

router = APIRouter(tags=["模型会话"])


@router.post("/chat", summary="直接与模型会话" )
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

            answer = ""  # 拼接模型响应

            if chat_request.stream:
                for chunk in response:  # 处理流式响应
                    answer += chunk.choices[0].delta.content
                    if chat_request.pretty_print:
                        output = chunk.choices[0].delta.content
                        if output:
                            yield output + "\n\n"
                    else:
                        yield chunk.choices[0].delta.json() + "\n\n"
                logger_client.info(f"\n用户询问:{chat_request.query}\n流式响应:{answer}")
            else:
                answer = response.choices[0].message.content
                if chat_request.pretty_print:  # 处理非流式响应
                    yield response.choices[0].message.content + "\n\n"
                else:
                    yield response.choices[0].message.json() + "\n\n"
                logger_client.info(f"\n用户询问:{chat_request.query}\n非流式响应:{answer}")

            if chat_request.save_messages:
                if len(messages) > chat_request.max_messages_cnt:
                    messages.pop(0)
                messages.append({"role": "assistant", "content": answer})
                history = {
                    "history": messages,
                }
                yield json.dumps(history, ensure_ascii=False) + "\n\n"
        except openai.OpenAIError as e:
            error_message = f"OpenAI API error: {str(e)}"
            logger_client.error(error_message)
            yield f"Error: {error_message}\n\n"
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            logger_client.error(error_message)
            yield f"Error: {error_message}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
