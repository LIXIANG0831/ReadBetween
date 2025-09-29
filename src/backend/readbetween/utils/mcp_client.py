import asyncio
import json
import traceback
from contextlib import AsyncExitStack
from datetime import timedelta
from typing import Dict, Any, List, Optional

import shortuuid
from mcp.client.sse import sse_client
from mcp import ClientSession, StdioServerParameters, stdio_client
from readbetween.utils.logger_util import logger_util


class MCPClient:
    def __init__(
            self,
            server_configs: Dict[str, Dict[str, Any]],  # 改为字典格式的配置
    ):
        """
        初始化 MCP 客户端，支持多种连接方式。

        :param server_configs: 服务器配置字典，格式为:
            {
                "服务器名称": {
                    "type": "stdio"/"sse",
                    "command": str,          # stdio 专用
                    "args": List[str],       # stdio 专用
                    "env": Dict[str, str],   # stdio 专用
                    "url": str,              # SSE 专用
                    "headers": Dict[str, str] # SSE 专用
                },
                ...
            }
        """
        self.server_configs = {server_name: {k: v for k, v in config.items() if v is not None} for server_name, config in server_configs.items()}  # 去除None值
        self.sessions = {}  # K: server_id -> V: (session, session_ctx, connection_ctx)
        self.server_tools = {}  # K: server_id -> V: [name1: V: description, parameters, prefixed_name1), name2: V: description, parameters, prefixed_name2)]
        self.server_id_to_name = {}
        self.tool_mapping = {}  # K: 带前缀的工具名 -> V: (session, 原始工具名)
        self.exit_stack = AsyncExitStack()

    async def initialize_mcp_sessions(self):
        """初始化所有服务器连接，并收集工具映射。"""
        for server_name, config in self.server_configs.items():
            server_id_dict = {server_name: config}  # 与渠道配置挂载MCP配置保持一致 方便匹配
            server_id = json.dumps(server_id_dict, ensure_ascii=False, sort_keys=True)
            # 记录 server_id 到 name 的映射
            self.server_id_to_name[server_id] = server_name
            try:
                if not config.get("url") and not config.get("command"):
                    logger_util.error(f"[{server_name}] 无法判断MCP服务器类型")
                    raise Exception(f"[{server_name}] 无法判断MCP服务器类型")

                if config.get("command") and not config.get("url"):
                    # 处理 stdio 连接
                    params = StdioServerParameters(
                        command=config["command"],
                        args=config.get("args", []),
                        env=config.get("env", None)
                    )
                    try:
                        connection_ctx = stdio_client(params)
                        connection = await self.exit_stack.enter_async_context(connection_ctx)
                        session_ctx = ClientSession(*connection)
                        session = await self.exit_stack.enter_async_context(session_ctx)
                        await session.initialize()
                        self.sessions[server_id] = (session, session_ctx, connection_ctx)
                        logger_util.debug(f"[{server_name}] 已通过 stdio 连接")
                    except Exception as e:
                        logger_util.error(f"[{server_name}] stdio连接初始化失败: {e}")
                        logger_util.error(traceback.format_exc())  # 打印完整堆栈
                        continue

                elif not config.get("command") and config.get("url"):
                    try:
                        connection_ctx = sse_client(
                            url=config["url"],
                            headers=config.get("headers", {})
                        )
                        connection = await self.exit_stack.enter_async_context(connection_ctx)
                        session_ctx = ClientSession(*connection)
                        session = await self.exit_stack.enter_async_context(session_ctx)
                        await session.initialize()
                        self.sessions[server_id] = (session, session_ctx, connection_ctx)
                        logger_util.debug(f"[{server_name}] 已通过 SSE 连接到 {config['url']}")
                    except Exception as e:
                        logger_util.error(f"[{server_name}] SSE连接初始化失败: {e}")
                        logger_util.error(traceback.format_exc())  # 打印完整堆栈
                        continue

                # 获取工具列表并建立映射
                await self._update_tool_mapping(server_id, session)

            except Exception as e:
                logger_util.error(f"[{server_name}] 连接失败：{e}")
                raise e

    async def _update_tool_mapping(self, server_id: str, session: ClientSession):
        """更新工具映射（保持不变）"""
        response = await session.list_tools()
        short_id_8 = shortuuid.ShortUUID().random(length=8)
        all_tool_list = {}
        for tool in response.tools:
            prefixed_name = f"{short_id_8}_{tool.name}"
            self.tool_mapping[prefixed_name] = (session, tool.name)
            all_tool_list[tool.name] = {
                "description": tool.description,
                "parameters": tool.inputSchema,
                "prefixed_name": prefixed_name
            }
        self.server_tools[server_id] = all_tool_list
        logger_util.debug(f"工具列表：{[tool.name for tool in response.tools]}")

    async def get_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有服务器的工具列表。

        :return: 返回字典格式的工具列表，结构为:
            {
                "server_id": {
                    "tool_name": {
                        "description": str,
                        "parameters": dict,
                        "prefixed_name": str  # 带服务器前缀的工具名
                    },
                    ...
                },
                ...
            }
        """
        return self.server_tools

    async def get_all_tools_by_config(self, mcp_server_configs: Dict) -> Dict[str, Dict[str, Any]]:

        server_tools_by_config = {}

        for server_name, server_config in mcp_server_configs.items():
            target_server_id_dict = {server_name: server_config}
            target_server_id = json.dumps(target_server_id_dict, ensure_ascii=False, sort_keys=True)
            server_tools_by_config[target_server_id] = self.server_tools[target_server_id]

        return server_tools_by_config

    async def execute_tools(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        执行工具列表中的工具并返回结果。

        :param tool_calls: 工具调用列表，每个元素应包含:
            {
                "name": str,  # 带服务器前缀的工具名
                "arguments": dict  # 工具参数
            }
        :return: 返回字典格式的结果，结构为:
            {
                "tool_name": {
                    "success": bool,
                    "result": Any,  # 工具返回结果
                    "error": str  # 错误信息（如果失败）
                },
                ...
            }
        """
        results = {}
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["arguments"]

            if tool_name not in self.tool_mapping:
                results[tool_name] = {
                    "success": False,
                    "result": None,
                    "error": f"工具 {tool_name} 未找到"
                }
                continue

            session, original_tool = self.tool_mapping[tool_name]
            try:
                read_timeout_seconds = timedelta(minutes=1)  # 工具调用超时时间
                result = await session.call_tool(original_tool, tool_args, read_timeout_seconds)
                results[tool_name] = {
                    "success": True,
                    "result": result,
                    "error": None
                }
            except Exception as e:
                results[tool_name] = {
                    "success": False,
                    "result": None,
                    "error": str(e)
                }
        return results

    async def cleanup(self):
        """释放所有资源。"""
        try:
            """释放所有资源（由 AsyncExitStack 自动管理）"""
            await self.exit_stack.aclose()  # 自动关闭所有注册的上下文管理器
            self.sessions.clear()  # 清理会话字典
            logger_util.debug("所有 MCP Session 连接资源已释放")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger_util.error(f"清理 MCP Session 连接资源时异常：{e}")


class MCPClientManager:
    _instance: Optional['MCPClientManager'] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._mcp_client: Optional[MCPClient] = None
        return cls._instance

    async def initialize_client(self, server_configs: dict) -> MCPClient:
        """初始化 MCP 客户端（线程安全）"""
        async with self._lock:
            if self._mcp_client is not None:
                # 如果已有客户端，先清理
                await self._mcp_client.cleanup()
            self._mcp_client = MCPClient(server_configs)
            await self._mcp_client.initialize_mcp_sessions()
            logger_util.info("MCPClient 初始化完成")
            return self._mcp_client

    def get_client(self) -> Optional[MCPClient]:
        """获取当前的 MCP 客户端实例"""
        return self._mcp_client

    async def cleanup(self):
        """清理当前的 MCP 客户端"""
        async with self._lock:
            if self._mcp_client is not None:
                await self._mcp_client.cleanup()
                self._mcp_client = None
                logger_util.info("MCPClient 已清理")


# 全局单例实例
mcp_client_manager = MCPClientManager()