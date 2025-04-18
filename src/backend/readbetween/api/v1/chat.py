import json
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, HTTPException
from readbetween.models.schemas.response import resp_200, resp_500
from readbetween.models.v1.chat import ChatRequest, ChatMessageSendPlus
from readbetween.utils.logger_util import logger_util
from readbetween.utils.model_factory import ModelFactory
from readbetween.models.v1.chat import ChatCreate, ChatUpdate, ChatMessageSend
from readbetween.services.chat import ChatService

router = APIRouter(tags=["模型会话"])


@router.post("/conversations/create")
async def create_conversation(create_data: ChatCreate):
    try:
        return resp_200(await ChatService.create_conversation(create_data))
    except Exception as e:
        logger_util.error(f"create_conversation error: {e}")
        return resp_500(message=str(e))


@router.post("/conversations/delete")
async def delete_conversation(conv_id: str):
    try:
        return resp_200(await ChatService.delete_conversation(conv_id))
    except Exception as e:
        logger_util.error(f"delete_conversation error: {e}")
        return resp_500(message=str(e))


@router.post("/conversations/update")
async def update_conversation(update_data: ChatUpdate):
    try:
        return resp_200(await ChatService.update_conversation(update_data))
    except Exception as e:
        logger_util.error(f"update_conversation error: {e}")
        return resp_500(message=str(e))


@router.get("/conversations/list")
async def list_conversations(page: int = 1, size: int = 10):
    try:
        return resp_200(await ChatService.list_conversations(page, size))
    except Exception as e:
        logger_util.error(f"list_conversations error: {e}")
        return resp_500(message=str(e))


@router.post("/conversations/messages/send", response_class=StreamingResponse)
async def send_message(message_data: ChatMessageSend):
    try:
        # 获取详细会话配置信息 通过缓存避免重复查询
        conversation_info = await ChatService.get_conversation_info(message_data.conv_id)
        # 返回StreamingResponse包装的生成器
        return StreamingResponse(
            ChatService.stream_chat_response(
                ChatMessageSendPlus(
                    **message_data.dict(),  # 解包ChatMessageSend
                    conversation_info=conversation_info,
                )
            ),
            media_type="text/event-stream"  # 设置正确的媒体类型
        )
    except Exception as e:
        logger_util.error(f"send_message初始化错误: {e}")

        # 注意：此处不能返回常规JSON响应，需通过生成器发送错误
        # 可考虑返回一个立即抛出错误的生成器
        async def error_generator():
            yield f"data: [ERROR] {str(e)}\n\n"

        return StreamingResponse(error_generator(), media_type="text/event-stream")


@router.get("/conversations/messages/history")
async def get_message_history(conv_id: str, limit: int = 100):
    try:
        return resp_200(await ChatService.get_message_history(conv_id, limit))
    except Exception as e:
        logger_util.error(f"get_message_history error: {e}")
        return resp_500(message=str(e))


@router.post("/conversations/messages/clear")
async def clear_message_history(conv_id: str):
    try:
        return resp_200(await ChatService.clear_message_history(conv_id))
    except Exception as e:
        logger_util.error(f"clear_message_history error: {e}")
        return resp_500(message=str(e))


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
