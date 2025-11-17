import asyncio
import json
from datetime import datetime
from typing import Generator, List, Dict

from fastapi import HTTPException

from readbetween.models.dao.messages import MessageDao
from readbetween.models.schemas.source import SourceMsg
from readbetween.models.schemas.sse_response import StreamResponseTemplate
from readbetween.models.v1.chat import ChatMessageSendPlus, ConversationInfo
from readbetween.models.v1.knowledge import KnowledgeInfo
from readbetween.services.conversation_knowledge_link import ConversationKnowledgeLinkService
from readbetween.services.knowledge import KnowledgeService
from readbetween.services.prompt import DEFAULT_PROMPT, KB_RECALL_PROMPT, WEB_SEARCH_PROMPT, MEMORY_PROMPT, \
    WEB_LINK_PROMPT, WEB_LINK_ERROR_PROMPT
from readbetween.services.retriever import RetrieverService
from readbetween.utils.logger_util import logger_util
from readbetween.utils.mcp_client import MCPClient, mcp_client_manager
from readbetween.utils.memory_util import MemoryUtil
from readbetween.utils.minio_util import MinioUtil
from readbetween.utils.model_factory import ModelFactory
from readbetween.utils.thread_pool_executor_util import ThreadPoolExecutorUtil
from readbetween.utils.tools import WebSearchTool, BaseTool
from readbetween.services.constant import SourceMsgType
from readbetween.services.tasks import celery_add_memory

minio_client = MinioUtil()


class StreamingChatEngine:
    """流式聊天处理器 - 专门处理 stream_chat_response 逻辑"""

    @classmethod
    async def generate_chat_stream(
            cls,
            message_data: ChatMessageSendPlus,
            is_recursion: bool = False
    ) -> Generator:
        """流式聊天处理"""
        try:
            # 初始化基础数据
            conversation_info, source_msg_list = await cls._initialize_chat_data(message_data)

            # 非递归调用时的预处理
            if not is_recursion:
                final_query, user_msg_id, new_sources = await cls._preprocess_user_message(
                    message_data,
                    conversation_info
                )
                source_msg_list.extend(new_sources)  # 添加收集到的来源信息
            else:
                final_query, user_msg_id = None, None

            # 准备工具和消息历史
            openai_tools = await cls._prepare_tools(conversation_info)
            messages = await cls._build_openai_request_messages(
                conversation_info, message_data, final_query, is_recursion
            )

            # 执行流式聊天
            async for response in cls._execute_stream_chat(
                    conversation_info, message_data, messages, openai_tools,
                    source_msg_list, user_msg_id, is_recursion
            ):
                yield response

        except Exception as e:
            logger_util.error(f"流式聊天处理失败: {str(e)}")
            yield StreamResponseTemplate.error_event(str(e))

    @classmethod
    async def _initialize_chat_data(cls, message_data: ChatMessageSendPlus):
        """初始化聊天数据"""
        conversation_info = message_data.conversation_info
        if not conversation_info:
            raise HTTPException(status_code=404, detail="对话不存在")

        return conversation_info, []

    @classmethod
    async def _preprocess_user_message(
            cls,
            message_data: ChatMessageSendPlus,
            conversation_info: ConversationInfo
    ):
        """预处理用户消息"""
        content = json.loads(message_data.message)
        is_multimodal = isinstance(content, list)

        # 初始化查询
        final_query, first_query = cls._init_user_query(content, is_multimodal)

        # 多模态问答默认不启用，只处理文本
        source_collector = []  # 用于收集所有来源信息
        if not is_multimodal:
            final_query, source_collector = await cls._enhance_query_with_external_sources(
                final_query, first_query, conversation_info, message_data
            )

        # 保存用户消息
        user_msg = await MessageDao.create_message(
            conv_id=message_data.conv_id,
            role="user",
            content=json.dumps(first_query, ensure_ascii=False),
        )

        return final_query, user_msg.id, source_collector

    @classmethod
    async def _enhance_query_with_external_sources(
            cls,
            final_query: str,
            first_query: str,
            conversation_info: ConversationInfo,
            message_data: ChatMessageSendPlus
    ):
        """使用外部资源增强查询"""
        task_results, source_collector = await cls._execute_concurrent_tasks(
            first_query, conversation_info, message_data
        )

        # 合并任务结果到最终查询
        final_query = cls._merge_task_results(final_query, task_results)

        return final_query, source_collector

    @classmethod
    async def _execute_concurrent_tasks(
            cls,
            query: str,
            conversation_info: ConversationInfo,
            message_data: ChatMessageSendPlus
    ):
        """并发执行各种检索任务"""
        task_results = {
            'kb_recall': None,
            'web_search': None,
            'memory_recall': None,
            'webpage_text': None
        }

        source_collector = []  # 用于收集所有来源信息

        thread_pool = ThreadPoolExecutorUtil(max_workers=5, async_max_workers=5)

        # 知识库检索
        knowledge_bases = await ConversationKnowledgeLinkService.get_attached_knowledge(
            conversation_info.conversation.id
        )
        if knowledge_bases:
            recall_chunk, kb_sources = await cls._append_kb_recall_msg(knowledge_bases, query)
            task_results['kb_recall'] = (recall_chunk, kb_sources)
            if kb_sources:
                source_collector.extend(kb_sources)

        # 网络搜索
        if hasattr(message_data, 'search') and message_data.search:
            task_results['web_search'] = thread_pool.submit_task(
                cls._append_web_search_msg, query
            )

        # 记忆召回
        if conversation_info.conversation.use_memory == 1:
            task_results['memory_recall'] = thread_pool.submit_task(
                cls._append_memory_msg, query, message_data.conv_id, 3
            )

        # 网页直链处理
        urls, url_cnt = BaseTool.extract_urls(query)
        if url_cnt > 0:
            task_results['webpage_text'] = await cls._append_webpage_text(urls)

        # 等待所有任务完成
        thread_pool.wait_for_all()
        await thread_pool.wait_for_all_async()

        # 处理网络搜索的来源信息
        if task_results['web_search'] and task_results['web_search'].done():
            try:
                web_search_info, web_sources = task_results['web_search'].result()
                if web_sources:
                    source_collector.extend(web_sources)
            except Exception as e:
                logger_util.error(f"网络检索来源信息收集失败: {str(e)}")

        return task_results, source_collector

    @classmethod
    def _merge_task_results(cls, final_query: str, task_results: dict):
        """合并任务结果到最终查询"""
        # 知识库召回结果
        if task_results['kb_recall']:
            try:
                recall_chunk, _ = task_results['kb_recall']
                if recall_chunk:
                    final_query = f"{final_query}\n{recall_chunk}"
            except Exception as e:
                logger_util.error(f"知识库召回结果合并失败: {str(e)}")

        # 网络搜索结果
        if task_results['web_search'] and task_results['web_search'].done():
            try:
                web_search_info, _ = task_results['web_search'].result()
                if web_search_info:
                    final_query = f"{final_query}\n{web_search_info}"
            except Exception as e:
                logger_util.error(f"网络检索结果合并失败: {str(e)}")

        # 记忆召回结果
        if task_results['memory_recall'] and task_results['memory_recall'].done():
            try:
                memory_info = task_results['memory_recall'].result()
                if memory_info:
                    final_query = f"{final_query}\n{memory_info}"
            except Exception as e:
                logger_util.error(f"记忆召回结果合并失败: {str(e)}")

        # 网页直链结果
        if task_results['webpage_text']:
            try:
                webpage_info = task_results['webpage_text']
                if webpage_info:
                    final_query = f"{final_query}\n{webpage_info}"
            except Exception as e:
                logger_util.error(f"网页直链结果合并失败: {str(e)}")

        return final_query

    @classmethod
    async def _prepare_tools(cls, conversation_info: ConversationInfo):
        """准备工具列表"""
        openai_tools = []
        mcp_client = mcp_client_manager.get_client()

        if mcp_client and conversation_info.conversation.mcp_server_configs:
            tools = await mcp_client.get_all_tools_by_config(
                conversation_info.conversation.mcp_server_configs
            )

            for server_tools in tools.values():
                for tool_name, tool_config in server_tools.items():
                    tool_config["name"] = tool_config["prefixed_name"]
                    openai_tools.append({
                        'type': 'function',
                        'function': tool_config
                    })

        return openai_tools

    @classmethod
    async def _build_openai_request_messages(
            cls,
            conversation_info: ConversationInfo,
            message_data: ChatMessageSendPlus,
            final_query: str,
            is_recursion: bool
    ):
        """构建请求消息"""
        system_prompt = [{
            'role': 'system',
            'content': f"{conversation_info.conversation.system_prompt}\n{DEFAULT_PROMPT}"
        }]

        history_messages = await cls._build_openai_messages(message_data.conv_id)

        if not is_recursion:
            current_message = [{'role': 'user', 'content': final_query}]
            messages = system_prompt + history_messages[:-1] + current_message
            cls._log_request_messages(messages, current_message, final_query)
        else:
            messages = system_prompt + history_messages
            logger_util.debug(f"工具递归调用中...\n模型请求信息:\n{messages}")

        return messages

    @classmethod
    def _log_request_messages(cls, full_messages, current_message, final_query):
        """记录请求消息日志"""
        if isinstance(final_query, list):
            sanitized_message = []
            for item in final_query:
                if isinstance(item, dict) and item.get('type') == 'image_url' and 'image_url' in item:
                    sanitized_item = item.copy()
                    sanitized_item['image_url'] = {'url': '图片的Base64'}
                    sanitized_message.append(sanitized_item)
                else:
                    sanitized_message.append(item)

            logger_util.debug(
                f"\n完整模型请求信息:\n{json.dumps(full_messages, indent=2, ensure_ascii=False)}")
            logger_util.debug(
                f"\n本次模型请求信息:\n{json.dumps(sanitized_message, indent=2, ensure_ascii=False)}")
        else:
            logger_util.debug(f"\n完整模型请求信息:\n{json.dumps(full_messages, indent=2, ensure_ascii=False)}")
            logger_util.debug(f"\n本次模型请求信息:\n{json.dumps(current_message, indent=2, ensure_ascii=False)}")

    @classmethod
    async def _execute_stream_chat(
            cls,
            conversation_info: ConversationInfo,
            message_data: ChatMessageSendPlus,
            messages: List[Dict],
            openai_tools: List[Dict],
            source_msg_list: List[SourceMsg],
            user_msg_id: str,
            is_recursion: bool
    ) -> Generator:
        """执行流式聊天处理"""
        # 初始化模型客户端
        model_cfg = conversation_info.model_cfg
        client = ModelFactory.create_client(config=model_cfg)

        full_response = []
        func_call_list = []
        thinking_opened = False

        # 开始流式响应
        yield StreamResponseTemplate.start_event()

        try:
            response = await client.generate_text(
                messages=messages,
                temperature=message_data.temperature or conversation_info.conversation.temperature,
                max_tokens=message_data.max_tokens,
                stream=True,
                tools=openai_tools,
                tool_choice="auto" if openai_tools else "none",
                extra_body={"enable_thinking": message_data.thinking},
            )

            # 处理流式响应
            async for chunk in response:
                async for response_chunk in cls._process_stream_chunk(
                        chunk, full_response, func_call_list, thinking_opened
                ):
                    yield response_chunk

            # 处理工具调用
            if func_call_list:
                async for tool_response in cls._handle_tool_calls_and_recursion(
                        message_data, func_call_list, source_msg_list
                ):
                    yield tool_response

            # 保存助手响应并返回最终结果
            async for final_response in cls._finalize_chat_response(
                    full_response, source_msg_list, message_data, user_msg_id, is_recursion
            ):
                yield final_response

        except Exception as e:
            logger_util.error(f"模型调用失败: {str(e)}")
            if not is_recursion and user_msg_id:
                await cls._rollback_user_message(user_msg_id)
            raise

    @classmethod
    async def _process_stream_chunk(
            cls,
            chunk,
            full_response: List[str],
            func_call_list: List[Dict],
            thinking_opened: bool
    ) -> Generator:
        """处理流式响应的单个数据块"""
        if not chunk.choices:
            return

        delta = chunk.choices[0].delta

        # 处理思考链内容
        if hasattr(delta, 'reasoning_content'):
            content = cls._process_reasoning_content(delta.reasoning_content, thinking_opened)
            if content:
                full_response.append(content)
                yield StreamResponseTemplate.message_event(content)

        # 处理普通消息内容
        if hasattr(delta, 'content') and delta.content and not thinking_opened:
            full_response.append(delta.content)
            yield StreamResponseTemplate.message_event(delta.content)

        # 处理工具调用
        if hasattr(delta, 'tool_calls') and delta.tool_calls:
            cls._process_tool_calls(delta.tool_calls, func_call_list)

    @classmethod
    def _process_reasoning_content(cls, reasoning_content: str, thinking_opened: bool):
        """处理思考链内容"""
        if reasoning_content:
            return f"<think>{reasoning_content}" if not thinking_opened else reasoning_content
        elif thinking_opened:
            return "</think>"
        return ""

    @classmethod
    def _process_tool_calls(cls, tool_calls, func_call_list: List[Dict]):
        """处理工具调用"""
        for tcchunk in tool_calls:
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

    @classmethod
    async def _handle_tool_calls_and_recursion(
            cls,
            message_data: ChatMessageSendPlus,
            func_call_list: List[Dict],
            source_msg_list: List[SourceMsg]
    ) -> Generator:
        """处理工具调用和递归调用"""
        mcp_client = mcp_client_manager.get_client()

        # 处理工具调用
        async for tool_response in cls._handle_tool_calls(
                message_data.conv_id, func_call_list, mcp_client
        ):
            yield tool_response

        # 递归调用处理工具响应
        from readbetween.services.conversation import ConversationService
        message_data.conversation_info = await ConversationService.get_conversation_info(message_data.conv_id)
        async for content in cls.generate_chat_stream(message_data, True):
            yield content

    @classmethod
    async def _finalize_chat_response(
            cls,
            full_response: List[str],
            source_msg_list: List[SourceMsg],
            message_data: ChatMessageSendPlus,
            user_msg_id: str,
            is_recursion: bool
    ) -> Generator:
        """完成聊天响应处理"""
        assistant_content = "".join(full_response)

        # 保存助手响应
        if assistant_content.strip():
            await MessageDao.create_message(
                conv_id=message_data.conv_id,
                role="assistant",
                content=json.dumps(assistant_content, ensure_ascii=False),
                source=json.dumps([msg.to_dict() for msg in list(set(source_msg_list))], ensure_ascii=False)
                if source_msg_list else None,
            )

        # 返回来源信息（仅非递归调用）
        if not is_recursion and source_msg_list:
            yield StreamResponseTemplate.source_event(
                sources=[source_msg.to_dict() for source_msg in list(set(source_msg_list))]
            )

        yield StreamResponseTemplate.end_event()

    @classmethod
    async def _rollback_user_message(cls, user_msg_id: str):
        """回滚用户消息"""
        try:
            await MessageDao.delete_message(user_msg_id)
        except Exception as delete_error:
            logger_util.error(f"消息回滚失败: {delete_error}")

    @classmethod
    def _init_user_query(cls, message, is_vl_query):
        """初始化用户查询"""
        if is_vl_query is True:
            return message, message
        else:
            return f"**用户问题:** {message}", message

    @classmethod
    async def _build_openai_messages(cls, conv_id: str):
        """
        优化后的消息构建方法

        特性：
        1. 自动过滤中间工具调用过程，当存在最终文本回复时
        2. 保留必要的用户消息上下文
        3. 更高效的状态管理机制
        """
        messages = await MessageDao.get_conversation_messages(conv_id)
        optimized_messages = []

        # 状态跟踪变量
        last_user_msg_idx = -1
        pending_tool_calls = False
        tool_call_chain_complete = False
        has_final_response = False

        for idx, msg in enumerate(messages):
            if msg.role == "user":
                # 处理用户消息（始终保留）
                content = json.loads(msg.content)
                # 清洗历史多模态交互信息
                if isinstance(content, list) and content and isinstance(content[0], dict):
                    content = content[0].get('text', '')

                optimized_messages.append({
                    "role": msg.role,
                    "content": content
                })
                last_user_msg_idx = len(optimized_messages) - 1
                pending_tool_calls = False
                tool_call_chain_complete = False
                has_final_response = False

            elif msg.role == "assistant":
                if msg.content:
                    # 这是最终回复，不是工具调用
                    has_final_response = True
                    # 如果之前有工具调用链但未完成，清理掉
                    if pending_tool_calls and not tool_call_chain_complete:
                        # 回退到最后一个用户消息
                        optimized_messages = optimized_messages[:last_user_msg_idx + 1]

                    optimized_messages.append({
                        "role": msg.role,
                        "content": json.loads(msg.content)
                    })
                    pending_tool_calls = False
                    tool_call_chain_complete = False

                elif msg.tool_calls:
                    # 处理工具调用请求
                    optimized_messages.append({
                        "role": msg.role,
                        "tool_calls": json.loads(msg.tool_calls)
                    })
                    pending_tool_calls = True
                    tool_call_chain_complete = False

            elif msg.role == "tool" and pending_tool_calls:
                # 处理工具响应
                optimized_messages.append({
                    "role": msg.role,
                    "tool_call_id": msg.tool_call_id,
                    "content": json.loads(msg.content)
                })
                # 标记工具调用链完成（等待最终回复）
                tool_call_chain_complete = True

        # 如果没有最终回复但有工具调用链，保留完整的工具调用过程
        if pending_tool_calls and not has_final_response:
            # 这种情况下，工具调用还在进行中，需要保留所有消息
            pass

        return optimized_messages

    @classmethod
    async def _handle_tool_calls(
            cls,
            conv_id: str,
            func_call_list: List[Dict],
            mcp_client: MCPClient
    ) -> Generator:
        """处理工具调用并返回响应"""
        # 保存助手调用信息
        assistant_tool_calls_msg = await MessageDao.create_message(
            conv_id=conv_id,
            role="assistant",
            tool_calls=json.dumps(func_call_list, ensure_ascii=False)
        )

        tool_calls_msg = None
        try:
            yield StreamResponseTemplate.tool_init_event(func_call_list)

            for func_calling in func_call_list:
                async for tool_response in cls._execute_single_tool_call(
                        func_calling, mcp_client, conv_id
                ):
                    yield tool_response

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
    async def _execute_single_tool_call(
            cls,
            func_calling: Dict,
            mcp_client: MCPClient,
            conv_id: str
    ) -> Generator:
        """执行单个工具调用"""
        tool_call_id = func_calling["id"]
        tool_name = func_calling["function"]["name"]
        tool_args = func_calling["function"]["arguments"]

        try:
            tool_args_json = json.loads(tool_args)
        except json.JSONDecodeError:
            raise Exception(f"无效的JSON参数: {tool_args}")

        # Yield tool start information
        tool_yield_msg = {
            "tool": tool_name,
            "input": tool_args_json,
        }

        logger_util.debug(f"开始执行MCP工具【{tool_name}】调用...")
        mcp_tool_call_resp = await mcp_client.execute_tools([{
            "name": tool_name,
            "arguments": tool_args_json
        }])
        logger_util.debug(f"完成执行MCP工具【{tool_name}】调用...")

        # 处理工具响应内容
        call_tool_result_content_msg = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": "当前工具调用未获取到有效信息。"
        }

        is_mcp_executed: bool = mcp_tool_call_resp[tool_name]["success"]
        if is_mcp_executed:
            from mcp.types import CallToolResult, TextContent, ImageContent, EmbeddedResource
            call_tool_result: CallToolResult = mcp_tool_call_resp[tool_name]['result']
            call_tool_result_content_list: List[
                TextContent | ImageContent | EmbeddedResource] = call_tool_result.content

            for content in call_tool_result_content_list:
                if isinstance(content, TextContent):
                    call_tool_result_content_msg["content"] = content.text
                elif isinstance(content, ImageContent):
                    # TODO: Handle image content
                    pass
                elif isinstance(content, EmbeddedResource):
                    # TODO: Handle embedded resource
                    pass
        else:
            # MCP执行失败
            call_tool_result_content_msg["content"] = mcp_tool_call_resp[tool_name]['error']

        # Yield tool end information
        tool_yield_msg["output"] = call_tool_result_content_msg["content"]
        yield StreamResponseTemplate.tool_execute_event(call_tool_result_content_msg)
        yield StreamResponseTemplate.tool_execute_info_event(tool_yield_msg)

        # 保存工具调用信息
        await MessageDao.create_message(
            conv_id=conv_id,
            role=call_tool_result_content_msg["role"],
            tool_call_id=call_tool_result_content_msg["tool_call_id"],
            content=json.dumps(call_tool_result_content_msg["content"], ensure_ascii=False)
        )

    # 以下是原有的辅助方法，保持不变
    @classmethod
    async def _append_kb_recall_msg(cls, knowledge_bases: List, query: str):
        """知识库召回消息处理"""
        recall_chunk = ""
        source_list: List[SourceMsg] = []
        if knowledge_bases:
            # 收集知识库及知识库所用模型信息
            milvus_knowledge_info: Dict = {}
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
                minio_object_name = retrieve_result.metadata['source']
                minio_file_url = minio_client.get_presigned_url(object_name=minio_object_name)
                source_list.append(SourceMsg(
                    source=SourceMsgType.KB.value,
                    title=retrieve_result.metadata['title'],
                    url=minio_file_url
                ))

                if retrieve_result.source == 'milvus' and float(retrieve_result.score) < 0.9:
                    recall_chunk += f"Title: {retrieve_result.metadata['title']}\nContent: {retrieve_result.text}\n\n"
                    logger_util.debug(f"Milvus Score: {float(retrieve_result.score)}")
                if retrieve_result.source == 'es' and float(retrieve_result.score) > 4.5:
                    recall_chunk += f"Title: {retrieve_result.metadata['title']}\nContent: {retrieve_result.text}\n\n"
                    logger_util.debug(f"ES Score: {float(retrieve_result.score)}")

        if recall_chunk:
            kb_recall_prompt = KB_RECALL_PROMPT.format(kb_recall_content=recall_chunk.strip())
            return kb_recall_prompt, source_list
        else:
            return "", None

    @classmethod
    def _append_web_search_msg(cls, query: str):
        """网络搜索消息处理"""
        search_tool = WebSearchTool()
        web_search_info = ""
        source_list: List[SourceMsg] = []

        now = datetime.now().strftime("%Y年%m月%d日")
        now_query = f"{now}{query}"
        search_results = search_tool.search_baidu(query, size=10, lm=3)

        for search_item in search_results:
            search_content = search_tool.get_page_detail(search_item.url)
            if search_content is not None:
                source_list.append(
                    SourceMsg(source=SourceMsgType.WEB.value, title=search_item.name, url=search_item.url))
                web_search_info += f"Title: {search_item.name}\nContent: {search_content}\n\n"

        if web_search_info:
            web_search_prompt = WEB_SEARCH_PROMPT.format(web_search_content=web_search_info)
            return web_search_prompt, source_list
        else:
            return "", None

    @classmethod
    def _append_memory_msg(cls, query: str, user_id, limit: int = 3):
        """记忆召回消息处理"""
        from readbetween.services.constant import memory_config
        memory_tool = MemoryUtil(memory_config)

        related_memories, memory_str = memory_tool.search_memories(query=query, user_id=user_id, limit=limit)
        logger_util.debug(f"记忆召回[results(向量)/relations(图)]: {related_memories}")
        logger_util.debug(f"记忆召回文本内容\n: {memory_str}")

        celery_add_memory.delay(query=query, user_id=user_id)

        original_memories = related_memories.get("results", [])
        graph_entities = related_memories.get("relations", [])

        if len(graph_entities) == 0 and len(original_memories) == 0:
            return ""
        else:
            memory_prompt = MEMORY_PROMPT.format(memory_recall_content=memory_str)
            return memory_prompt

    @classmethod
    async def _append_webpage_text(cls, urls: List[str]):
        """网页直链文本处理"""
        fetch_tasks = []
        for url in urls:
            task = BaseTool.fetch_webpage_text_async(url)
            fetch_tasks.append(task)

        fetched_contents = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        successful_contents = []

        for url, content in zip(urls, fetched_contents):
            if content is not None and content != '':
                successful_contents.append(WEB_LINK_PROMPT.format(web_link=url, web_link_content=content))
            else:
                successful_contents.append(WEB_LINK_ERROR_PROMPT.format(web_link=url))

        return "\n".join(successful_contents)