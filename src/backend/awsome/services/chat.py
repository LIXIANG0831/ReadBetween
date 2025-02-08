from awsome.models.schemas.source import SourceMsg
from awsome.models.dao.conversation_knowledge_link import ConversationKnowledgeLinkDao
from awsome.models.dao.conversations import ConversationDao, Conversation
from awsome.models.dao.knowledge import KnowledgeDao, Knowledge
from awsome.models.dao.messages import MessageDao
from awsome.models.schemas.response import PageModel
from awsome.models.v1.chat import ChatCreate, ChatUpdate, ChatMessageSend
from fastapi import HTTPException
import asyncio
from typing import Generator, List

from awsome.services.retriever import RetrieverService
from awsome.utils.logger_util import logger_util

from awsome.utils.model_factory import ModelFactory
from awsome.utils.tools import WebSearchTool


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
            knowledge_base_ids=update_data.knowledge_base_ids
        )

        return await cls._format_conversation_response(
            await ConversationDao.one_with_kb(update_data.conv_id)
        )

    @classmethod
    async def list_conversations(cls, page: int, size: int):
        """分页获取用户对话列表"""
        total = await ConversationDao.cnt_conversation_total()
        conversations = await ConversationDao.list_with_kb(page, size)
        return PageModel(total=total, data=[{
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
        ])

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
        # 来源信息
        source_msg_list: List[SourceMsg] = []
        # 获取对话配置
        conversation: Conversation = await ConversationDao.get(message_data.conv_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")

        # 最终给模型的输入
        final_query = message_data.message

        # 获取知识库召回内容
        if len(conversation.knowledge_bases) > 0:
            logger_util.debug(f"用户开启并使用知识库检索")
            try:
                final_query = await cls._append_kb_recall_msg(conversation.knowledge_bases, final_query)
            except Exception as e:
                logger_util.error(f"知识库召回内容失败: {e}")

        # 获取网络搜索内容
        if message_data.search is True:
            logger_util.debug(f"用户开启并使用网络检索")
            try:
                final_query = await cls._append_web_search_msg(message_data.message, final_query)
            except Exception as e:
                logger_util.error(f"网络检索失败：{e}")

        # 获取 历史记录
        # 构造 OpenAI 请求参数
        system_prompt = [{'role': 'system', 'content': f'{conversation.system_prompt}'}]
        history_messages = await cls._build_openai_messages(message_data.conv_id)
        current_message = [{'role': 'user', 'content': f'{final_query}'}]
        messages = system_prompt + history_messages + current_message
        logger_util.debug(f"当前请求模型完整请求消息: {messages}")

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

        try:
            # 创建模型调用客户端
            client = ModelFactory.create_client(llm_name=conversation.model)
            # 完整的模型回复
            full_response = []
            try:
                response = await client.generate_text(
                    messages=messages,
                    temperature=message_data.temperature or conversation.temperature,
                    max_tokens=message_data.max_tokens,
                    stream=True
                )

                for chunk in response:
                    content = chunk.choices[0].delta.content or ""
                    if content is not None:
                        full_response.append(content)
                        yield f"data: {content}\n\n"
                        # await asyncio.sleep(0.02)  # 控制流式速度
            except Exception as e:
                error_msg = f"模型响应失败: {str(e)}"
                raise Exception(error_msg)

            # 保存助手响应
            try:
                assistant_content = "".join(full_response)
                await MessageDao.create_message(
                    conv_id=message_data.conv_id,
                    role="assistant",
                    content=assistant_content
                )
                logger_util.debug(f"保存助手响应消息: {assistant_content}")
            except Exception as e:
                error_msg = f"保存助手响应信息失败: {e}"
                raise Exception(error_msg)
        except Exception as e:
            logger_util.error(f"模型调用或保存模型回复失败: {str(e)}")
            # 回滚用户保存消息
            try:
                await MessageDao.delete_message(user_msg_id)
                logger_util.info(f"已回滚用户消息: {user_msg_id}")
            except Exception as delete_error:
                logger_util.error(f"消息回滚失败: {delete_error}")
            yield f"data: [ERROR] {e}\n\n"

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

    @classmethod
    async def _append_kb_recall_msg(cls, knowledge_bases: List[Knowledge], message: str):
        recall_chunk = ""
        if knowledge_bases:
            retrieve_resp = await RetrieverService.retrieve(
                query=message,
                mode="both",
                milvus_collection_names=[
                    knowledge_base.collection_name
                    for knowledge_base in knowledge_bases
                ],
                milvus_fields=['text', 'title'],
                es_index_names=[
                    knowledge_base.index_name
                    for knowledge_base in knowledge_bases
                ],
                es_fields=['text', 'metadata.title'],
                top_k=3
            )
            for retrieve_result in retrieve_resp:
                # TODO 考虑是否抽象为配置项
                if retrieve_result.source == 'milvus' and float(retrieve_result.score) > 0.8:
                    recall_chunk += f"Title: {retrieve_result.metadata['title']}\nContent: {retrieve_result.text}\n\n"
                if retrieve_result.source == 'es' and float(retrieve_result.score) < 4:
                    recall_chunk += f"Title: {retrieve_result.metadata['title']}\nContent: {retrieve_result.text}\n\n"

        if recall_chunk:
            return f"""
                    【上下文参考】
                    {recall_chunk.strip()}
                    
                    【用户最新消息】
                    {message}
                    
                    【生成要求】
                    请基于上下文参考内容，用自然对话的方式响应用户消息。注意：
                    1. 不要使用"根据检索内容"、"根据资料"等暴露检索过程的表述
                    2. 不要直接引用上下文中的标题或元数据
                    3. 若上下文内容与用户需求无关，则忽略它直接回答
            """
        else:
            return message

    @classmethod
    async def _append_web_search_msg(cls, query: str, message: str):
        search_tool = WebSearchTool()
        web_search_info = ""
        # 一级检索
        search_results = search_tool.search_baidu(query, size=3, lm=3)
        # 二级检索
        for search_item in search_results:
            # TODO 拼接检索内容到提示词final_query
            search_content = search_tool.get_page_detail(search_item.url)
            if search_content is not None:
                # source_msg_list.append(SourceMsg(source="web", title=search_item.name, url=search_item.url))
                web_search_info += f"Title: {search_item.name}\nContent: {search_content}\n\n"
        if web_search_info:
            return f"""
                【网络检索内容】
                {web_search_info}
                
                {message}
            """
        else:
            return message
