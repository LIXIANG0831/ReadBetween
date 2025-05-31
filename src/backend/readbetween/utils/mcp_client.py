import asyncio
import traceback
from contextlib import AsyncExitStack
from typing import Dict, Any, List, Union, Tuple
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
        self.server_configs = server_configs
        self.sessions = {}  # server_id -> (session, session_ctx, connection_ctx)
        self.tool_mapping = {}  # 带前缀的工具名 -> (session, 原始工具名)
        self.exit_stack = AsyncExitStack()

    async def initialize_sessions(self):
        """初始化所有服务器连接，并收集工具映射。"""
        for server_name, config in self.server_configs.items():
            server_id = server_name  # 直接使用配置中的名称作为 server_id
            try:
                if not config.get("url") and  not config.get("command"):
                    logger_util.error(f"[{server_id}] 无法判断MCP服务器类型")
                    raise Exception(f"[{server_id}] 无法判断MCP服务器类型")

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
                        logger_util.debug(f"[{server_id}] 已通过 stdio 连接")
                    except Exception as e:
                        logger_util.error(f"[{server_id}] stdio连接初始化失败: {e}")
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
                        logger_util.debug(f"[{server_id}] 已通过 SSE 连接到 {config['url']}")
                    except Exception as e:
                        logger_util.error(f"[{server_id}] SSE连接初始化失败: {e}")
                        logger_util.error(traceback.format_exc())  # 打印完整堆栈
                        continue

                # 获取工具列表并建立映射
                await self._update_tool_mapping(server_id, session)

            except Exception as e:
                logger_util.error(f"[{server_id}] 连接失败：{e}")
                raise e

    async def _update_tool_mapping(self, server_id: str, session: ClientSession):
        """更新工具映射（保持不变）"""
        response = await session.list_tools()
        for tool in response.tools:
            prefixed_name = f"{server_id}_{tool.name}"
            self.tool_mapping[prefixed_name] = (session, tool.name)
        logger_util.debug(f"[{server_id}] 工具列表：{[tool.name for tool in response.tools]}")

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
        all_tools = {}
        for server_id, (session, _, _) in self.sessions.items():
            response = await session.list_tools()
            server_tools = {}
            for tool in response.tools:
                prefixed_name = f"{server_id}_{tool.name}"
                server_tools[tool.name] = {
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                    "prefixed_name": prefixed_name
                }
            all_tools[server_id] = server_tools
        return all_tools

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
                result = await session.call_tool(original_tool, tool_args)
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
