import json
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, HTTPException
from awsome.models.v1.chat import ChatRequest
from awsome.utils.logger_util import logger_util
from awsome.utils.model_factory import ModelFactory

router = APIRouter(tags=["模型会话"])


@router.post("/chat", summary="直接与模型对话")
async def chat(chat_request: ChatRequest):
    try:
        # 创建模型客户端
        client = ModelFactory.create_client()

        # 构造 OpenAI 请求参数
        generate_params = {
            "messages": [msg.dict() for msg in chat_request.messages],
            "temperature": chat_request.temperature,
            "max_tokens": chat_request.max_tokens,
            "stream": chat_request.stream,
        }

        if chat_request.stream:
            # 流式输出
            async def generate():
                response = await client.generate_text(**generate_params)
                for chunk in response:
                    # 直接访问 ChoiceDelta 对象的 content 属性
                    content = chunk.choices[0].delta.content or ""
                    if content:
                        yield json.dumps({"content": content}, ensure_ascii=False) + "\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            # 非流式输出
            response = await client.generate_text(**generate_params)
            content = response.choices[0].message.content
            return {"content": content}

    except Exception as e:
        logger_util.warning(f"模型直接对话异常: An error occurred: {str(e)}")
        return HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
