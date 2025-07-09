import asyncio
import json
from datetime import datetime

from mcp.types import CallToolResult, TextContent, ImageContent, EmbeddedResource

from readbetween.models.dao.model_available_cfg import ModelAvailableCfgDao
from readbetween.models.schemas.source import SourceMsg
from readbetween.models.dao.conversation_knowledge_link import ConversationKnowledgeLinkDao
from readbetween.models.dao.conversation import ConversationDao, Conversation
from readbetween.models.dao.knowledge import KnowledgeDao, Knowledge
from readbetween.models.dao.messages import MessageDao
from readbetween.models.schemas.response import PageModel
from readbetween.models.v1.chat import ChatCreate, ChatUpdate, ChatMessageSend, ChatMessageSendPlus
from fastapi import HTTPException
from typing import Generator, List, Dict

from readbetween.models.v1.chat import ConversationInfo
from readbetween.models.v1.knowledge import KnowledgeInfo
from readbetween.models.v1.model_available_cfg import ModelAvailableCfgInfo
from readbetween.services.constant import ModelType_LLM, PrefixRedisConversation, Ex_PrefixRedisConversation, \
    SourceMsgType
from readbetween.services.conversation_knowledge_link import ConversationKnowledgeLinkService
from readbetween.services.knowledge import KnowledgeService
from readbetween.services.retriever import RetrieverService
from readbetween.services.tasks import celery_add_memory
from readbetween.utils.logger_util import logger_util
from readbetween.utils.mcp_client import MCPClient
from readbetween.utils.memory_util import MemoryUtil
from readbetween.utils.minio_util import MinioUtil
from readbetween.utils.model_factory import ModelFactory
from readbetween.utils.tools import WebSearchTool
from readbetween.utils.redis_util import RedisUtil

minio_client = MinioUtil()
redis_client = RedisUtil()


class ConversationService:

    @classmethod
    async def create_conversation(cls, create_data: ChatCreate):
        """创建新对话"""
        # 验证所用知识库是否存在
        if create_data.knowledge_base_ids:
            existing_kbs = await KnowledgeDao.get_many(create_data.knowledge_base_ids)
            if len(existing_kbs) != len(create_data.knowledge_base_ids):
                invalid_ids = set(create_data.knowledge_base_ids) - {kb.id for kb in existing_kbs}
                raise HTTPException(status_code=404,
                                    detail=f"无效的知识库ID: {invalid_ids}")

        # 验证 available_model_id 是否符合要求
        if create_data.available_model_id:
            is_valid = ModelAvailableCfgDao.select_one(create_data.available_model_id).type == ModelType_LLM
            if not is_valid:
                raise HTTPException(status_code=500,
                                    detail=f"模型类型有误 {create_data.available_model_id}")

        # 创建会话渠道
        conv = await ConversationDao.create(
            title=create_data.title,
            available_model_id=create_data.available_model_id,
            system_prompt=create_data.system_prompt,
            temperature=create_data.temperature,
            use_memory=create_data.use_memory,
            mcp_server_configs=create_data.mcp_server_configs
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
        # 再删除会话-知识库关联关系
        await ConversationKnowledgeLinkDao.delete(conv_id)
        # 再删除记忆
        conversation: Conversation = await ConversationDao.get(conv_id)
        if conversation.use_memory == 1:
            from readbetween.services.constant import memory_config
            memory_util = MemoryUtil(memory_config)
            memory_util.delete_all_memories(user_id=conv_id)
        # 再删除缓存
        redis_client.delete(f"{PrefixRedisConversation}{conv_id}")
        # 再删除对话
        return await ConversationDao.soft_delete(conv_id)

    @classmethod
    async def update_conversation(cls, update_data: ChatUpdate):
        """更新对话信息"""
        # TODO 增加记忆更新
        await ConversationDao.update(
            conv_id=update_data.conv_id,
            title=update_data.title,
            system_prompt=update_data.system_prompt,
            temperature=update_data.temperature,
            knowledge_base_ids=update_data.knowledge_base_ids,
            use_memory=update_data.use_memory,
            available_model_id=update_data.available_model_id,
            mcp_server_configs=update_data.mcp_server_configs
        )

        # 更新模型 则删除配置缓存
        if update_data.available_model_id is not None:
            redis_client.delete(f"{PrefixRedisConversation}{update_data.conv_id}")

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
            "available_model_id": conv.available_model_id,
            "use_memory": conv.use_memory,
            "system_prompt": conv.system_prompt,
            "temperature": conv.temperature,
            "knowledge_bases": [
                {
                    "id": kb.id,
                    "name": kb.name,
                    "desc": kb.desc,
                    # "model": kb.model,
                    "collection_name": kb.collection_name,
                    "index_name": kb.index_name,
                }
                for kb in conv.knowledge_bases
            ],
            "selected_mcp_servers": conv.mcp_server_configs,
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
    async def stream_chat_response(
            cls,
            message_data: ChatMessageSendPlus,
            mcp_client: MCPClient = None,
            is_recursion: bool = False
    ) -> Generator:
        """流式聊天处理"""
        # 初始化变量
        source_msg_list: List[SourceMsg] = []  # 来源信息返回列表
        kb_source_list = None  # RAG知识库来源信息
        web_source_list = None  # 网络来源信息
        should_cleanup = False  # 标记是否需要清理 MCP Client

        conversation_info: ConversationInfo = message_data.conversation_info
        if not conversation_info:
            raise HTTPException(status_code=404, detail="对话不存在")

        # 非递归调用时的预处理
        if not is_recursion:
            # 处理用户输入和各类检索
            content = json.loads(message_data.message)
            is_multimodal = isinstance(content, list)

            # 初始化最终查询和原始查询
            final_query, first_query = cls._init_user_query(content, is_multimodal)

            # 多模态问答 默认不启用
            if not is_multimodal:
                # 并发执行任务
                concurrent_tasks = []

                # 处理知识库检索
                knowledge_bases = await ConversationKnowledgeLinkService.get_attached_knowledge(
                    conversation_info.conversation.id)
                if knowledge_bases:
                    # Desperate -- 修改为并发执行 修改原 append 逻辑为直接返回
                    # final_query, kb_source_list = await cls._append_kb_recall_msg(knowledge_bases, final_query)
                    concurrent_tasks.append(cls._append_kb_recall_msg(knowledge_bases, content))


                # 处理网络搜索
                if message_data.search:
                    # Desperate -- 修改为并发执行 修改原 append 逻辑为直接返回
                    # final_query, web_source_list = await cls._append_web_search_msg(content, final_query)
                    concurrent_tasks.append(cls._append_web_search_msg(content))

                # 处理记忆
                if conversation_info.conversation.use_memory == 1:
                    # Desperate -- 修改为并发执行 修改原 append 逻辑为直接返回
                    # final_query = await cls._append_memory_msg(content, final_query, message_data.conv_id, 3)
                    concurrent_tasks.append(cls._append_memory_msg(content, message_data.conv_id, 3))

                # 并发执行所有任务
                task_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
                for result in task_results:
                    # 处理异常情况
                    if isinstance(result, Exception):
                        logger_util.error(f"并发任务执行出错: {str(result)}")
                        continue
                    # 跳过空结果
                    if not result:
                        continue

                    # 解析结果
                    try:
                        add_context = result[0]  # 第一个元素总是要添加的上下文

                        # 如果有第二个元素，处理来源列表
                        if len(result) > 1 and isinstance(result[1], list):
                            source_list = result[1]
                            if not source_list:
                                continue

                            # 分类来源类型
                            if all(isinstance(item, SourceMsg) and item.source == SourceMsgType.KB for item in
                                   source_list):
                                kb_source_list = source_list
                            else:
                                web_source_list = source_list

                        # 更新最终查询
                        final_query = f"{final_query}\n{add_context}"

                    except (IndexError, TypeError) as e:
                        logger_util.error(f"结果解析错误: {str(e)}，结果: {result}")
                        continue


            # 保存用户消息
            user_msg = await MessageDao.create_message(
                conv_id=message_data.conv_id,
                role="user",
                content=json.dumps(first_query, ensure_ascii=False),
            )
            user_msg_id = user_msg.id

        # 准备MCP Client 获取MCP Tool列表
        openai_tools = []
        if not is_recursion and conversation_info.conversation.mcp_server_configs:  # 只在第一次调用时创建MCP Client
            mcp_client = MCPClient(conversation_info.conversation.mcp_server_configs)
            await mcp_client.initialize_sessions()
            should_cleanup = True
        if mcp_client:
            tools = await mcp_client.get_all_tools()  # 获取 MCP Tool列表
            for k, v in tools.items():
                for inner_k, inner_v in v.items():
                    inner_v["name"] = inner_v["prefixed_name"]
                    openai_tools.append({
                        'type': 'function',
                        'function': inner_v
                    })

        # 构建消息历史
        system_prompt = [{'role': 'system', 'content': conversation_info.conversation.system_prompt}]
        history_messages = await cls._build_openai_messages(message_data.conv_id)

        # 添加当前消息（如果是非递归调用）
        if not is_recursion:
            current_message = [{'role': 'user', 'content': final_query}]
            messages = system_prompt + history_messages + current_message
            logger_util.debug(f"\n完整模型请求信息:\n{messages}")
            logger_util.debug(f"\n本次模型请求信息:\n{current_message}")
        else:
            messages = system_prompt + history_messages
            logger_util.debug(f"\n工具递归调用中...\n模型请求信息:\n{messages}")


        try:
            # 初始化模型客户端
            model_cfg = conversation_info.model_cfg
            client = ModelFactory.create_client(config=model_cfg)

            full_response = []
            func_call_list = []
            thinking_opened = False

            # 开始流式响应
            yield cls._format_stream_response(event="START", text="")

            response = await client.generate_text(
                messages=messages,
                temperature=message_data.temperature or conversation_info.conversation.temperature,
                max_tokens=message_data.max_tokens,
                stream=True,
                tools=openai_tools,
                tool_choice="auto" if openai_tools else "none",
                extra_body={"thinking_budget": 1024},
            )

            async for chunk in response:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                # 处理思考链内容
                if hasattr(delta, 'reasoning_content'):
                    reasoning = delta.reasoning_content
                    if reasoning:
                        content = f"<think>{reasoning}" if not thinking_opened else reasoning
                        thinking_opened = True
                    elif thinking_opened:
                        content = "</think>"
                        thinking_opened = False
                    else:
                        content = ""

                    if content:
                        full_response.append(content)
                        yield cls._format_stream_response(event="MESSAGE", text=content)

                # 处理普通消息内容
                if hasattr(delta, 'content') and delta.content and not thinking_opened:
                    content = delta.content
                    full_response.append(content)
                    yield cls._format_stream_response(event="MESSAGE", text=content)

                # 处理工具调用
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    for tcchunk in delta.tool_calls:
                        if len(func_call_list) <= tcchunk.index:
                            func_call_list.append({
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            })
                        tc = func_call_list[tcchunk.index]
                        if tcchunk.id:
                            tc["id"] += tcchunk.id
                        if tcchunk.function.name:
                            tc["function"]["name"] += tcchunk.function.name
                        if tcchunk.function.arguments:
                            tc["function"]["arguments"] += tcchunk.function.arguments

            # 处理工具调用结果
            if func_call_list:
                async for response in cls._handle_tool_calls(message_data.conv_id, func_call_list, mcp_client):
                    yield response

                # 递归调用处理工具响应
                message_data.conversation_info = await cls.get_conversation_info(message_data.conv_id)
                async for content in cls.stream_chat_response(message_data, mcp_client, True):
                    yield content

            # 收集来源信息
            if web_source_list is not None:
                source_msg_list.extend(web_source_list)
            if kb_source_list is not None:
                source_msg_list.extend(kb_source_list)

            # 保存助手响应
            assistant_content = "".join(full_response)
            if assistant_content.strip():  # 如果内容为空或只有空白字符不进行保存
                await MessageDao.create_message(
                    conv_id=message_data.conv_id,
                    role="assistant",
                    content=json.dumps(assistant_content, ensure_ascii=False),
                    source=json.dumps([msg.to_dict() for msg in list(set(source_msg_list))], ensure_ascii=False) if len(
                        list(set(source_msg_list))) > 0 else None,
                )

            # 返回来源信息
            if not is_recursion and (len(source_msg_list) != 0):
                yield cls._format_stream_response(
                    event="SOURCE",
                    text="",
                    extra=[source_msg.to_dict() for source_msg in list(set(source_msg_list))]
                )

            yield cls._format_stream_response(event="END", text="")

        except Exception as e:
            logger_util.error(f"模型调用失败: {str(e)}")
            if not is_recursion:
                try:
                    await MessageDao.delete_message(user_msg_id)
                except Exception as delete_error:
                    logger_util.error(f"消息回滚失败: {delete_error}")
            yield cls._format_stream_response(event="ERROR", text=str(e))
        finally:
            if should_cleanup and mcp_client:
                try:
                    await mcp_client.cleanup()
                except Exception as cleanup_error:
                    logger_util.error(f"清理MCP客户端时出错: {cleanup_error}")

    @classmethod
    async def _build_openai_messages(cls, conv_id: str):
        """构建 OpenAI 需要的消息格式"""
        messages = await MessageDao.get_conversation_messages(conv_id)
        openai_messages = []
        for msg in messages:
            if msg.role == "user":
                content = json.loads(msg.content)
                # 'message': 'At most 1 image(s) may be provided in one request.
                # 清洗历史多模态交互信息
                # 多模态image_url在使用后, 应无需再组装到 messages 中.
                if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
                    content = content[0].get('text', '')
                openai_messages.append({
                    "role": msg.role,
                    "content": content
                })
            elif msg.role == "tool":
                openai_messages.append({
                    "role": msg.role,
                    "tool_call_id": msg.tool_call_id,
                    "content": json.loads(msg.content)
                })
            elif msg.role == "assistant":
                assistant_msg = {
                    "role": msg.role,
                }
                if msg.content is not None:
                    assistant_msg["content"] = json.loads(msg.content)
                if msg.tool_calls is not None:
                    assistant_msg["tool_calls"] = json.loads(msg.tool_calls)
                openai_messages.append(assistant_msg)
            else:
                pass
        return openai_messages

    @classmethod
    async def _stream_second_model_response(
            cls,
            client,
            conversation_info: ConversationInfo,
            message_data: ChatMessageSendPlus
    ) -> Generator:
        """Stream the second model response after tool calls"""
        system_prompt = [{'role': 'system', 'content': f'{conversation_info.conversation.system_prompt}'}]
        history_messages = await cls._build_openai_messages(message_data.conv_id)
        messages = system_prompt + history_messages

        logger_util.debug("已获取工具响应信息进行二次模型调用")

        second_response = await client.generate_text(
            messages=messages,
            temperature=message_data.temperature or conversation_info.conversation.temperature,
            max_tokens=message_data.max_tokens,
            stream=True,
        )

        async for chunk in second_response:
            if hasattr(chunk, 'choices') and chunk.choices:
                if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                    content = chunk.choices[0].delta.content or ""
                    if content is not None:
                        yield content  # 直接 yield 内容，不收集，不格式转换

    @classmethod
    async def _handle_tool_calls(
            cls,
            conv_id: str,
            func_call_list: List[Dict],
            mcp_client: MCPClient
    ) -> Generator:
        """Handle tool calls and yield responses"""
        # 保存助手调用信息
        assistant_tool_calls_msg = await MessageDao.create_message(
            conv_id=conv_id,
            role="assistant",
            tool_calls=json.dumps(func_call_list, ensure_ascii=False)
        )

        tool_calls_msg = None
        try:
            yield cls._format_stream_response(event="TOOL_START", text="", extra=func_call_list)
            for func_calling in func_call_list:
                tool_call_id = func_calling["id"]
                tool_name = func_calling["function"]["name"]
                tool_args = func_calling["function"]["arguments"]

                # Yield tool start information
                tool_yield_msg = {
                    "tool": tool_name,
                    "input": json.loads(tool_args),
                }

                logger_util.debug("开始执行MCP工具调用...")
                mcp_tool_call_resp = await mcp_client.execute_tools([{
                    "name": tool_name,
                    "arguments": json.loads(tool_args)
                }])
                logger_util.debug("完成执行MCP工具调用...")

                call_tool_result: CallToolResult = mcp_tool_call_resp[tool_name]['result']
                call_tool_result_content_list: List[
                    TextContent | ImageContent | EmbeddedResource] = call_tool_result.content

                # 处理工具响应内容
                call_tool_result_content_msg = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": "工具调用结果异常"
                }

                for content in call_tool_result_content_list:
                    if isinstance(content, TextContent):
                        call_tool_result_content_msg["content"] = content.text
                    elif isinstance(content, ImageContent):
                        # TODO: Handle image content
                        pass
                    elif isinstance(content, EmbeddedResource):
                        # TODO: Handle embedded resource
                        pass

                # Yield tool end information
                tool_yield_msg["output"] = call_tool_result_content_msg.get("content", "工具调用结果异常")
                yield cls._format_stream_response(event="TOOL_END", text="", extra=call_tool_result_content_msg)
                yield cls._format_stream_response(event="TOOL_FINISH", text="", extra=tool_yield_msg)

                # 保存工具调用信息
                tool_calls_msg = await MessageDao.create_message(
                    conv_id=conv_id,
                    role=call_tool_result_content_msg.get("role", "tool"),
                    tool_call_id=call_tool_result_content_msg.get("tool_call_id", tool_call_id),
                    content=json.dumps(call_tool_result_content_msg.get("content", "工具调用结果异常"),
                                       ensure_ascii=False)
                )

        except Exception as e:
            # Clean up messages if error occurs
            if assistant_tool_calls_msg is not None:
                await MessageDao.delete_message(assistant_tool_calls_msg.id)
                logger_util.info(f"已回滚模型调用工具响应消息: {assistant_tool_calls_msg.id}")
            if tool_calls_msg is not None:
                await MessageDao.delete_message(tool_calls_msg.id)
                logger_util.info(f"已回滚工具调用响应消息: {tool_calls_msg.id}")
            raise Exception(f"MCP调用失败: {str(e)}")

    @classmethod
    async def _format_conversation_response(cls, conv: Conversation):
        return {
            "id": conv.id,
            "title": conv.title,
            "available_model_id": conv.available_model_id,
            "system_prompt": conv.system_prompt,
            "temperature": conv.temperature,
            "knowledge_bases": [
                {
                    "id": kb.id,
                    "name": kb.name,
                    "desc": kb.desc,
                    # "model": kb.model,
                    "collection_name": kb.collection_name,
                    "index_name": kb.index_name,
                }
                for kb in conv.knowledge_bases
            ],
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat()
        }

    @classmethod
    async def _append_kb_recall_msg(cls, knowledge_bases: List[Knowledge], query: str):
        recall_chunk = ""
        source_list: List[SourceMsg] = []
        if knowledge_bases:
            # 收集知识库及知识库所用模型信息
            milvus_knowledge_info: Dict[ModelAvailableCfgInfo, List[Knowledge]] = {}
            for knowledge in knowledge_bases:
                knowledge_info: KnowledgeInfo = await KnowledgeService.get_knowledge_info(knowledge.id)
                model_cfg = knowledge_info.model_cfg
                knowledge_obj = knowledge_info.knowledge
                if model_cfg not in milvus_knowledge_info:
                    milvus_knowledge_info[model_cfg] = []
                milvus_knowledge_info[model_cfg].append(knowledge_obj)

            retrieve_resp = await RetrieverService.retrieve(
                query=query,
                mode="both",
                milvus_knowledge_info=milvus_knowledge_info,
                milvus_fields=['text', 'title', 'source'],
                es_index_names=[
                    knowledge_base.index_name
                    for knowledge_base in knowledge_bases
                ],
                es_fields=['text', 'metadata.title', 'metadata.source'],
                top_k=3
            )
            for retrieve_result in retrieve_resp:
                # print(retrieve_result.source)
                # print(retrieve_result.score)
                # print(retrieve_result)
                # 返回object_name minio获取预签名链接
                minio_object_name = retrieve_result.metadata['source']
                minio_file_url = minio_client.get_presigned_url(object_name=minio_object_name)
                # 保存来源信息
                source_list.append(SourceMsg(source=SourceMsgType.KB.value, title=retrieve_result.metadata['title'], url=minio_file_url))
                # TODO 考虑是否抽象为配置项
                # if retrieve_result.source == 'milvus' and float(retrieve_result.score) < 1:  # 较为宽松的召回
                if retrieve_result.source == 'milvus' and float(retrieve_result.score) < 0.9:  # 较为严格的召回
                    recall_chunk += f"Title: {retrieve_result.metadata['title']}\nContent: {retrieve_result.text}\n\n"
                    logger_util.debug(f"Milvus Score: {float(retrieve_result.score)}")
                # if retrieve_result.source == 'es' and float(retrieve_result.score) > 2.5:  # 较为宽松的召回
                if retrieve_result.source == 'es' and float(retrieve_result.score) > 4.5:  # 较为严格的召回
                    recall_chunk += f"Title: {retrieve_result.metadata['title']}\nContent: {retrieve_result.text}\n\n"
                    logger_util.debug(f"ES Score: {float(retrieve_result.score)}")

        if recall_chunk:
            return f"""
**RAG Retrieval Information:** This is relevant information retrieved from a knowledge base, which may contain the answer to the question or related background knowledge.
{recall_chunk.strip()}
            """, source_list
        else:
            return "", None

    @classmethod
    async def _append_web_search_msg(cls, query: str):
        search_tool = WebSearchTool()
        web_search_info = ""
        source_list: List[SourceMsg] = []
        # 一级检索
        now = datetime.now().strftime("%Y年%m月%d日")
        now_query = f"{now}{query}"
        search_results = search_tool.search_baidu(query, size=10, lm=3)
        # 二级检索
        for search_item in search_results:
            search_content = search_tool.get_page_detail(search_item.url)
            if search_content is not None:
                source_list.append(SourceMsg(source=SourceMsgType.WEB.value, title=search_item.name, url=search_item.url))
                web_search_info += f"Title: {search_item.name}\nContent: {search_content}\n\n"
        if web_search_info:
            return f"""
**Web Search Information:** This is relevant information gathered from internet searches, which may contain the latest information or different perspectives.
{web_search_info}
            """, source_list
        else:
            return "", None

    @classmethod
    async def _append_memory_msg(cls, query: str, user_id, limit: int = 3):
        # user_id 用来标识唯一记忆
        from readbetween.services.constant import memory_config
        memory_tool = MemoryUtil(memory_config)
        # 检索记忆
        related_memories, memory_str = memory_tool.search_memories(query=query, user_id=user_id, limit=limit)
        logger_util.debug(f"记忆召回[results(向量)/relations(图)]: {related_memories}")
        logger_util.debug(f"记忆召回文本内容\n: {memory_str}")
        # 添加记忆
        # memory_tool.add_memory(text=query, user_id=user_id)
        # 使用Celery后台添加记忆
        celery_add_memory.delay(query=query, user_id=user_id)
        # 向量库记忆
        original_memories = related_memories.get("results", [])
        # 图记忆
        graph_entities = related_memories.get("relations", [])
        if len(graph_entities) == 0 and len(original_memories) == 0:
            return ""
        else:
            return f"""
**User Memory Information:** This is information about the user's past conversations and preferences, which can help you better understand the user's needs.
{memory_str}
            """

    @classmethod
    def _format_stream_response(cls, event: str, text: str, extra=None):
        data = {"event": event, "text": text}
        if extra is not None:
            data["extra"] = extra
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    @classmethod
    def _init_user_query(cls, message, is_vl_query):
        if is_vl_query is True:
            return message, message
        else:
            return f"""
**User Question:** {message}

**Your task is to:**

1. **Task Execution:**  
   - Carefully read and fully comprehend all provided information.  
   - Cross-reference all available sources to determine relevance, accuracy, and reliability.  

2. **Response Requirements:**  
   - Generate a clear, concise, and helpful response that directly addresses the user’s query.  
   - If conflicts exist between sources, reconcile differing viewpoints or explicitly note the discrepancy.  
   - Exclude all irrelevant information.  

3. **Language Preference:**  
   - Respond in **Chinese** unless otherwise specified.  

4. **Function Calling Protocol:**  
   - When a user request necessitates **Function Calling** (e.g., real-time data, APIs, or external tools), **automatically invoke the required function without seeking user confirmation**.  
   - Prioritize tool-based results for accuracy and immediacy.  
   - Process the returned data and deliver a finalized answer seamlessly.  

**Example Workflow:**  
   - User asks for weather → Auto-call weather API → Parse data → Return structured response.  
   - No intermediate steps (e.g., "Should I check the weather for you?").  

            """, message

    @classmethod
    async def get_conversation_info(cls, conv_id):
        # 拼接 Redis Key
        conv_info_key = f"{PrefixRedisConversation}{conv_id}"
        if redis_client.exists(conv_info_key):  # 缓存存在 直接返回
            conv_info_from_redis = json.loads(redis_client.get(conv_info_key))
            return ConversationInfo(
                conversation=Conversation.parse_obj(conv_info_from_redis.get("conversation", {})),
                model_cfg=ModelAvailableCfgInfo.parse_obj(conv_info_from_redis.get("model_cfg", {}))
            )

        conversation: Conversation = await ConversationDao.get(conv_id)
        available, setting, provider = ModelAvailableCfgDao.select_cfg_info_by_id(conversation.available_model_id)
        conversation_info = ConversationInfo(
            conversation=conversation,
            model_cfg=ModelAvailableCfgInfo(
                type=available.type,
                name=available.name,
                api_key=setting.api_key,
                base_url=setting.base_url,
                mark=provider.mark
            )
        )

        # 加入缓存 30分钟
        redis_client.set(conv_info_key, conversation_info.model_dump_json(), Ex_PrefixRedisConversation)

        return conversation_info
