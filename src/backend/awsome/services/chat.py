from awsome.models.dao.conversation_knowledge_link import ConversationKnowledgeLinkDao
from awsome.models.dao.conversations import ConversationDao, Conversation
from awsome.models.dao.knowledge import KnowledgeDao
from awsome.models.dao.messages import MessageDao
from awsome.models.v1.chat import ChatCreate, ChatUpdate, ChatMessageSend
from fastapi import HTTPException
import asyncio
from typing import Generator
from awsome.utils.logger_util import logger_util

from awsome.utils.model_factory import ModelFactory


class ChatService:

    @classmethod
    async def create_conversation(cls, create_data: ChatCreate):
        """创建新对话"""
        # 验证所有知识库是否存在
        if create_data.knowledge_base_ids:
            existing_kbs = await KnowledgeDao.get_many(create_data.knowledge_base_ids)
            if len(existing_kbs) != len(create_data.knowledge_base_ids):
                invalid_ids = set(create_data.knowledge_base_ids) - {kb.id for kb in existing_kbs}
                raise HTTPException(status_code=404,
                                    detail=f"Invalid knowledge base IDs: {invalid_ids}")

        conv = await ConversationDao.create(
            title=create_data.title,
            model=create_data.model,
            system_prompt=create_data.system_prompt,
            temperature=create_data.temperature
        )

        # 创建关联关系
        if create_data.knowledge_base_ids:
            for knowledge_base_id in create_data.knowledge_base_ids:
                logger_util.debug(f"当前会话管理知识库ID: {knowledge_base_id}")
                await ConversationKnowledgeLinkDao.create(conversation_id=conv.id, knowledge_id=knowledge_base_id)

        return await cls._format_conversation_response(
            await ConversationDao.one_with_kb(conv.id)
        )

    @classmethod
    async def delete_conversation(cls, conv_id: str):
        """软删除对话"""
        # 先删除关联消息
        await MessageDao.delete_conversation_messages(conv_id)
        # 再删除管理知识库
        await ConversationKnowledgeLinkDao.delete(conv_id)
        # 再删除对话
        return await ConversationDao.soft_delete(conv_id)

    @classmethod
    async def update_conversation(cls, update_data: ChatUpdate):
        """更新对话信息"""
        await ConversationDao.update(
            conv_id=update_data.conv_id,
            title=update_data.title,
            system_prompt=update_data.system_prompt,
            temperature=update_data.temperature,
            knowledge_base_ids=ChatUpdate.knowledge_base_ids
        )

        return await cls._format_conversation_response(
            await ConversationDao.one_with_kb(update_data.conv_id)
        )

    @classmethod
    async def list_conversations(cls, page: int, size: int):
        """分页获取用户对话列表"""
        conversations = await ConversationDao.list_with_kb(page, size)
        return [
            {
                "id": conv.id,
                "title": conv.title,
                "model": conv.model,
                "knowledge_bases": [
                    {
                        "id": kb.id,
                        "name": kb.name,
                        "desc": kb.desc,
                        "model": kb.model,
                        "collection_name": kb.collection_name,
                        "index_name": kb.index_name,
                    }
                    for kb in conv.knowledge_bases
                ],
                "updated_at": conv.updated_at.isoformat()
            }
            for conv in conversations
        ]

    @classmethod
    async def get_message_history(cls, conv_id: str, limit: int):
        """获取对话历史消息"""
        return await MessageDao.get_conversation_messages(conv_id, limit)

    @classmethod
    async def clear_message_history(cls, conv_id: str):
        """软删除对话历史消息"""
        # 先删除关联消息
        return await MessageDao.delete_conversation_messages(conv_id)

    @classmethod
    async def stream_chat_response(cls, message_data: ChatMessageSend) -> Generator:
        """流式聊天处理"""
        # 获取对话配置
        conversation = await ConversationDao.get(message_data.conv_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")

        # 保存用户消息并记录ID
        try:
            user_msg = await MessageDao.create_message(
                conv_id=message_data.conv_id,
                role="user",
                content=message_data.message
            )
            user_msg_id = user_msg.id
            logger_util.debug(f"保存用户消息ID: {user_msg_id}")
        except Exception as e:
            logger_util.error(f"保存用户消息失败: {e}")
            yield f"data: [ERROR] 消息保存失败\n\n"
            return

        # 获取 历史记录
        # 构造 OpenAI 请求参数
        system_prompt = [{'role': 'system', 'content': f'{conversation.system_prompt}'}]
        history_messages = await cls._build_openai_messages(message_data.conv_id)
        messages = system_prompt + history_messages
        logger_util.debug(f"构造完整请求消息: {messages}")

        # 创建模型调用客户端
        client = ModelFactory.create_client(llm_name=conversation.model)
        try:
            response = await client.generate_text(
                messages=messages,
                temperature=message_data.temperature or conversation.temperature,
                max_tokens=message_data.max_tokens,
                stream=True
            )

            full_response = []
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                if content is not None:
                    full_response.append(content)
                    yield f"data: {content}\n\n"
                    await asyncio.sleep(0.02)  # 控制流式速度

            # 保存助手响应
            assistant_content = "".join(full_response)
            await MessageDao.create_message(
                conv_id=message_data.conv_id,
                role="assistant",
                content=assistant_content
            )
            logger_util.debug(f"保存助手响应消息: {assistant_content}")
        except Exception as e:
            # 删除刚保存的用户消息
            try:
                await MessageDao.delete_message(user_msg_id)
                logger_util.info(f"已回滚用户消息: {user_msg_id}")
            except Exception as delete_error:
                logger_util.error(f"消息回滚失败: {delete_error}")

            error_msg = f"[ERROR] {str(e)}"
            yield f"data: {error_msg}\n\n"

    @classmethod
    async def _build_openai_messages(cls, conv_id: str):
        """构建 OpenAI 需要的消息格式"""
        messages = await MessageDao.get_conversation_messages(conv_id)
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    @classmethod
    async def _format_conversation_response(cls, conv: Conversation):
        return {
            "id": conv.id,
            "title": conv.title,
            "model": conv.model,
            "system_prompt": conv.system_prompt,
            "temperature": conv.temperature,
            "knowledge_bases": [
                {
                    "id": kb.id,
                    "name": kb.name,
                    "desc": kb.desc,
                    "model": kb.model,
                    "collection_name": kb.collection_name,
                    "index_name": kb.index_name,
                }
                for kb in conv.knowledge_bases
            ],
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat()
        }
