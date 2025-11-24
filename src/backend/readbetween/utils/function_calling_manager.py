import asyncio
import json
import os
import traceback
from contextlib import AsyncExitStack
from datetime import timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

import shortuuid
from mcp.client.sse import sse_client
from mcp import ClientSession, StdioServerParameters, stdio_client
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageFunctionToolCall, ChatCompletionMessageCustomToolCall, ChatCompletion
from openapi_llm.client.openapi_async import AsyncOpenAPIClient

from readbetween.utils.logger_util import logger_util


class ToolType(Enum):
    """工具类型枚举"""
    MCP = "mcp"
    OPENAPI = "openapi"


class ToolSource:
    """工具来源基类"""

    def __init__(self, source_type: ToolType, source_id: str, source_name: str):
        self.source_type = source_type
        self.source_id = source_id
        self.source_name = source_name


class MCPSource(ToolSource):
    """MCP 工具来源"""

    def __init__(self, server_id: str, server_name: str, session: ClientSession):
        super().__init__(ToolType.MCP, server_id, server_name)
        self.session = session


class OpenAPISource(ToolSource):
    """OpenAPI 工具来源"""

    def __init__(self, api_id: str, api_name: str, api_client: AsyncOpenAPIClient):
        super().__init__(ToolType.OPENAPI, api_id, api_name)
        self.api_client = api_client


class UnifiedToolManager:
    """
    统一的工具管理器，支持 MCP 和 OpenAPI 工具
    """

    def __init__(self):
        self.tool_sources: Dict[str, ToolSource] = {}  # K: source_id -> V: ToolSource
        self.tool_mapping: Dict[str, tuple] = {}  # K: prefixed_tool_name -> V: (source_id, original_tool_name)
        self.tool_definitions: Dict[str, Dict] = {}  # K: prefixed_tool_name -> V: tool_definition
        self.exit_stack = AsyncExitStack()

    async def add_mcp_server(self, server_configs: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """
        添加 MCP 服务器

        :param server_configs: MCP 服务器配置
        :return: 服务器ID到名称的映射
        """
        server_id_to_name = {}

        for server_name, config in server_configs.items():
            # 创建标准化的配置字典，确保所有字段都存在
            standardized_config = {
                "command": config.get("command"),
                "args": config.get("args"),
                "env": config.get("env"),
                "url": config.get("url"),
                "headers": config.get("headers")
            }

            server_id_dict = {server_name: standardized_config}
            server_id = json.dumps(server_id_dict, ensure_ascii=False, sort_keys=True)
            server_id_to_name[server_id] = server_name

            # 如果已经存在相同的服务器ID，跳过重复添加
            if server_id in self.tool_sources:
                logger_util.debug(f"[{server_name}] MCP服务器已存在，跳过重复添加")
                continue

            try:
                if not config.get("url") and not config.get("command"):
                    logger_util.error(f"[{server_name}] 无法判断MCP服务器类型")
                    continue

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

                        # 创建 MCP 工具源
                        mcp_source = MCPSource(server_id, server_name, session)
                        self.tool_sources[server_id] = mcp_source

                        # 获取工具列表并建立映射
                        await self._update_mcp_tool_mapping(server_id, mcp_source)
                        logger_util.debug(f"[{server_name}] MCP服务器添加成功")

                    except Exception as e:
                        logger_util.error(f"[{server_name}] stdio连接初始化失败: {e}")
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

                        # 创建 MCP 工具源
                        mcp_source = MCPSource(server_id, server_name, session)
                        self.tool_sources[server_id] = mcp_source

                        # 获取工具列表并建立映射
                        await self._update_mcp_tool_mapping(server_id, mcp_source)
                        logger_util.debug(f"[{server_name}] MCP服务器添加成功")

                    except Exception as e:
                        logger_util.error(f"[{server_name}] SSE连接初始化失败: {e}")
                        continue

            except Exception as e:
                logger_util.error(f"[{server_name}] MCP服务器添加失败：{e}")
                continue

        return server_id_to_name

    async def add_openapi_service(self, service_configs: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """
        添加 OpenAPI 服务

        :param service_configs: OpenAPI 服务配置
        :return: 服务ID到名称的映射
        """
        service_id_to_name = {}

        for service_name, config in service_configs.items():
            service_id_dict = {service_name: config}
            service_id = json.dumps(service_id_dict, ensure_ascii=False, sort_keys=True)
            service_id_to_name[service_id] = service_name

            # 如果已经存在相同的服务ID，跳过重复添加
            if service_id in self.tool_sources:
                logger_util.debug(f"[{service_name}] OpenAPI服务已存在，跳过重复添加")
                continue

            try:
                openapi_spec = config.get("openapi_spec")
                credentials = config.get("credentials")

                if not openapi_spec:
                    logger_util.error(f"[{service_name}] OpenAPI spec 未提供")
                    continue

                # 创建 OpenAPI 客户端
                api_client = AsyncOpenAPIClient.from_spec(
                    openapi_spec=openapi_spec,
                    credentials=credentials
                )

                # 创建 OpenAPI 工具源
                openapi_source = OpenAPISource(service_id, service_name, api_client)
                self.tool_sources[service_id] = openapi_source

                # 获取工具列表并建立映射
                await self._update_openapi_tool_mapping(service_id, openapi_source)
                logger_util.debug(f"[{service_name}] OpenAPI服务添加成功")

            except Exception as e:
                logger_util.error(f"[{service_name}] OpenAPI服务添加失败：{e}")
                continue

        return service_id_to_name

    async def _update_mcp_tool_mapping(self, server_id: str, mcp_source: MCPSource):
        """更新 MCP 工具映射"""
        try:
            response = await mcp_source.session.list_tools()
            short_id_8 = shortuuid.ShortUUID().random(length=8)

            for tool in response.tools:
                prefixed_name = f"{short_id_8}_{tool.name}"
                self.tool_mapping[prefixed_name] = (server_id, tool.name)

                self.tool_definitions[prefixed_name] = {
                    "name": prefixed_name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                    "prefixed_name": prefixed_name,
                    "source_type": ToolType.MCP.value
                }

            logger_util.debug(f"MCP工具列表：{[tool.name for tool in response.tools]}")
        except Exception as e:
            logger_util.error(f"更新MCP工具映射失败: {e}")

    async def _update_openapi_tool_mapping(self, service_id: str, openapi_source: OpenAPISource):
        """更新 OpenAPI 工具映射"""
        try:
            for tool_definition in openapi_source.api_client.tool_definitions:
                original_name = tool_definition['function']['name']
                # 对于OpenAPI工具，使用原始名称，不添加前缀
                prefixed_name = original_name

                self.tool_mapping[prefixed_name] = (service_id, original_name)

                self.tool_definitions[prefixed_name] = {
                    "name": prefixed_name,
                    "description": tool_definition['function'].get('description', ''),
                    "parameters": tool_definition['function'].get('parameters', {}),
                    "prefixed_name": prefixed_name,
                    "source_type": ToolType.OPENAPI.value
                }

            logger_util.debug(
                f"OpenAPI工具列表：{[tool['function']['name'] for tool in openapi_source.api_client.tool_definitions]}")
        except Exception as e:
            logger_util.error(f"更新OpenAPI工具映射失败: {e}")

    def get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的定义，用于传递给 LLM

        :return: OpenAI 格式的工具定义列表
        """
        openai_tools = []
        for tool_def in self.tool_definitions.values():
            openai_tools.append({
                'type': 'function',
                'function': {
                    'name': tool_def['name'],
                    'description': tool_def['description'],
                    'parameters': tool_def['parameters']
                }
            })
        return openai_tools

    def get_tools_by_sources(self, source_configs: Dict) -> List[Dict[str, Any]]:
        """
        根据源配置获取特定工具

        :param source_configs: 源配置
        :return: 工具定义列表
        """
        tools = []
        for source_name, source_config in source_configs.items():
            # 创建标准化的配置字典
            standardized_config = {
                "command": source_config.get("command"),
                "args": source_config.get("args"),
                "env": source_config.get("env"),
                "url": source_config.get("url"),
                "headers": source_config.get("headers")
            }

            target_source_id_dict = {source_name: standardized_config}
            target_source_id = json.dumps(target_source_id_dict, ensure_ascii=False, sort_keys=True)

            # 查找匹配的工具
            for prefixed_name, tool_def in self.tool_definitions.items():
                source_id, _ = self.tool_mapping[prefixed_name]
                if source_id == target_source_id:
                    tools.append({
                        'type': 'function',
                        'function': {
                            'name': tool_def['name'],
                            'description': tool_def['description'],
                            'parameters': tool_def['parameters']
                        }
                    })
        return tools

    async def execute_tools(self, tool_calls: list[ChatCompletionMessageFunctionToolCall | ChatCompletionMessageCustomToolCall | dict] | None) -> Dict[str, Any]:
        """
        执行工具调用

        :param tool_calls: OpenAI 响应的工具列表
        :return: 执行结果
        """
        results = {}

        for i, tool_call in enumerate(tool_calls):
            # 统一处理不同格式的工具调用
            if isinstance(tool_call, dict):
                # 处理字典格式
                tool_call_id = tool_call.get("id", f"tool_call_{i}")
                function_data = tool_call.get("function", {})
                mapped_tool_name = function_data.get("name", "")
                tool_args_str = function_data.get("arguments", "{}")
            else:
                # 处理 OpenAI 对象格式
                tool_call_id = tool_call.id
                mapped_tool_name = tool_call.function.name
                tool_args_str = tool_call.function.arguments

            # 解析参数
            try:
                tool_args = json.loads(tool_args_str)
            except json.JSONDecodeError:
                tool_args = {}

            # 为每个工具调用生成唯一的结果键
            result_key = f"{mapped_tool_name}_{i}"

            if mapped_tool_name not in self.tool_mapping:
                results[result_key] = {
                    "success": False,
                    "result": None,
                    "error": f"工具 {mapped_tool_name} 未找到",
                    "source_type": None,
                    "tool_call_id": tool_call_id,
                    "original_tool_name": mapped_tool_name,
                    "arguments": tool_args
                }
                continue

            source_id, original_tool_name = self.tool_mapping[mapped_tool_name]
            tool_source = self.tool_sources.get(source_id)

            if not tool_source:
                results[result_key] = {
                    "success": False,
                    "result": None,
                    "error": f"工具源 {source_id} 未找到",
                    "source_type": None,
                    "tool_call_id": tool_call_id,
                    "original_tool_name": original_tool_name,
                    "arguments": tool_args
                }
                continue

            try:
                if tool_source.source_type == ToolType.MCP:
                    # 执行 MCP 工具 - 使用原始工具名称
                    mcp_source: MCPSource = tool_source
                    read_timeout_seconds = timedelta(minutes=1)
                    result = await mcp_source.session.call_tool(original_tool_name, tool_args, read_timeout_seconds)

                    results[result_key] = {
                        "success": True,
                        "result": result,
                        "error": None,
                        "source_type": ToolType.MCP.value,
                        "tool_call_id": tool_call_id,
                        "original_tool_name": original_tool_name,
                        "arguments": tool_args
                    }

                elif tool_source.source_type == ToolType.OPENAPI:
                    # 执行 OpenAPI 工具 - 构建正确的 function_payload
                    openapi_source: OpenAPISource = tool_source

                    # 构建符合 SDK 要求的 function_payload
                    function_payload = {
                        "name": original_tool_name,  # 使用原始工具名称
                        "arguments": tool_args  # 直接使用解析后的参数
                    }

                    # 使用 OpenAPI 客户端执行工具
                    async with openapi_source.api_client as api:
                        service_response = await api.invoke(function_payload)
                        logger_util.debug(f"OpenAPI 工具执行结果: {service_response=}")
                        results[result_key] = {
                            "success": True,
                            "result": service_response,
                            "error": None,
                            "source_type": ToolType.OPENAPI.value,
                            "tool_call_id": tool_call_id,
                            "original_tool_name": original_tool_name,
                            "arguments": tool_args
                        }

            except Exception as e:
                # 获取完整的堆栈跟踪
                stack_trace = traceback.format_exc()

                # 记录详细错误
                logger_util.error(f"工具 {mapped_tool_name} 执行失败:\n"
                                  f"错误: {str(e)}\n"
                                  f"堆栈跟踪:\n{stack_trace}\n"
                                  f"参数: {tool_args}\n"
                                  f"工具类型: {tool_source.source_type.value if tool_source else 'Unknown'}")

                results[result_key] = {
                    "success": False,
                    "result": None,
                    "error": str(e),
                    "source_type": tool_source.source_type.value if tool_source else None,
                    "tool_call_id": tool_call_id,
                    "original_tool_name": original_tool_name,
                    "arguments": tool_args
                }

        return results

    async def cleanup(self):
        """清理资源"""
        try:
            # 先关闭所有会话
            for source_id, tool_source in list(self.tool_sources.items()):
                if isinstance(tool_source, MCPSource):
                    try:
                        # 优雅关闭会话
                        if hasattr(tool_source.session, 'aclose'):
                            await tool_source.session.aclose()
                    except Exception as e:
                        logger_util.debug(f"关闭MCP会话失败 {source_id}: {e}")

            # 清空数据结构
            self.tool_sources.clear()
            self.tool_mapping.clear()
            self.tool_definitions.clear()

            # 最后清理退出栈
            if hasattr(self.exit_stack, 'aclose'):
                await self.exit_stack.aclose()
            logger_util.debug("所有工具资源已释放")
        except Exception as e:
            logger_util.error(f"清理工具资源时异常：{e}")


class FunctionCallingManager:
    """
    函数调用管理器单例
    """
    _instance: Optional['FunctionCallingManager'] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tool_manager: Optional[UnifiedToolManager] = None
            cls._instance._mcp_configs: Dict = {}
            cls._instance._openapi_configs: Dict = {}
        return cls._instance

    async def initialize(
            self,
            mcp_server_configs: Optional[Dict] = None,
            openapi_service_configs: Optional[Dict] = None
    ) -> UnifiedToolManager:
        """
        初始化工具管理器

        :param mcp_server_configs: MCP 服务器配置
        :param openapi_service_configs: OpenAPI 服务配置
        :return: 工具管理器实例
        """
        async with self._lock:
            if self._tool_manager is not None:
                await self._tool_manager.cleanup()

            self._tool_manager = UnifiedToolManager()

            # 保存配置
            self._mcp_configs = mcp_server_configs or {}
            self._openapi_configs = openapi_service_configs or {}

            # 添加 MCP 服务器
            if mcp_server_configs:
                await self._tool_manager.add_mcp_server(mcp_server_configs)

            # 添加 OpenAPI 服务
            if openapi_service_configs:
                await self._tool_manager.add_openapi_service(openapi_service_configs)

            logger_util.info("FunctionCallingManager 初始化完成")
            return self._tool_manager

    async def update_mcp_servers(self, new_mcp_configs: Dict) -> bool:
        """
        更新 MCP 服务器配置

        :param new_mcp_configs: 新的 MCP 服务器配置
        :return: 是否成功更新
        """
        async with self._lock:
            if self._tool_manager is None:
                logger_util.error("工具管理器未初始化")
                return False

            try:
                # 更新配置
                self._mcp_configs = new_mcp_configs

                # 重新初始化工具管理器
                await self._tool_manager.cleanup()
                self._tool_manager = UnifiedToolManager()

                # 重新添加所有配置
                if self._mcp_configs:
                    await self._tool_manager.add_mcp_server(self._mcp_configs)
                if self._openapi_configs:
                    await self._tool_manager.add_openapi_service(self._openapi_configs)

                logger_util.info("MCP 服务器配置更新成功")
                return True

            except Exception as e:
                logger_util.error(f"更新 MCP 服务器配置失败: {e}")
                return False

    async def update_openapi_services(self, new_openapi_configs: Dict) -> bool:
        """
        更新 OpenAPI 服务配置

        :param new_openapi_configs: 新的 OpenAPI 服务配置
        :return: 是否成功更新
        """
        async with self._lock:
            if self._tool_manager is None:
                logger_util.error("工具管理器未初始化")
                return False

            try:
                # 更新配置
                self._openapi_configs = new_openapi_configs

                # 重新初始化工具管理器
                if self._tool_manager is not None:
                    await self._tool_manager.cleanup()
                self._tool_manager = UnifiedToolManager()

                # 重新添加所有配置
                if self._mcp_configs:
                    await self._tool_manager.add_mcp_server(self._mcp_configs)
                if self._openapi_configs:
                    await self._tool_manager.add_openapi_service(self._openapi_configs)

                logger_util.info("OpenAPI 服务配置更新成功")
                return True

            except Exception as e:
                logger_util.error(f"更新 OpenAPI 服务配置失败: {e}")
                return False

    def get_tool_manager(self) -> Optional[UnifiedToolManager]:
        """获取工具管理器实例"""
        return self._tool_manager

    def get_mcp_configs(self) -> Dict:
        """获取当前 MCP 配置"""
        return self._mcp_configs

    def get_openapi_configs(self) -> Dict:
        """获取当前 OpenAPI 配置"""
        return self._openapi_configs

    async def cleanup(self):
        """清理工具管理器"""
        async with self._lock:
            if self._tool_manager is not None:
                await self._tool_manager.cleanup()
                self._tool_manager = None
                self._mcp_configs = {}
                self._openapi_configs = {}
                logger_util.info("FunctionCallingManager 已清理")


# 全局单例实例
function_calling_manager = FunctionCallingManager()


# 使用示例
async def example_usage():
    # Notice:
    # function_calling_manager.initialize 相当于执行器，加载全部的可调用MCP和OpenAPI的工具
    # 输入给LLM的 tool_definitions 包含2部分：1. 配置到会话的mcp_server; 2. 直接挂载到会话的OpenAPI的tool_definition;
    # LLM输出工具调用Response使用tool_manager.execute_tools自动执行

    # MCP 服务器配置
    mcp_configs = {
        "高德地图": {
            "url": "https://mcp.amap.com/sse?key=2f5e7338488ceb95f2252c61e60042fc"
        }
    }

    # OpenAPI 服务配置
    openapi_configs = {
        "空压工具": {
            "openapi_spec": "{\r\n    \"openapi\": \"3.1.0\",\r\n    \"info\": {\r\n        \"title\": \"空压分析工具\",\r\n        \"description\": \"空压站能耗、能效、流量、压力等分析工具接口\",\r\n        \"version\": \"v1.0.0\"\r\n    },\r\n    \"servers\": [\r\n        {\r\n            \"url\": \"https:\/\/emat.t.cosmoplat.cn\/dev-api\"\r\n        }\r\n    ],\r\n    \"paths\": {\r\n        \"\/tool\/v1\/compressor\/getEnergyStatistics\": {\r\n            \"post\": {\r\n                \"description\": \"能耗统计，包含空压站的流量、功率、压力、用电量、总电费、能耗等信息。\",\r\n                \"operationId\": \"getEnergyStatistics\",\r\n                \"requestBody\": {\r\n                    \"content\": {\r\n                        \"application\/json\": {\r\n                            \"schema\": {\r\n                                \"type\": \"object\",\r\n                                \"properties\": {\r\n                                    \"start_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"开始时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"end_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"结束时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"config_type\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"配置类型，固定为2\"\r\n                                    },\r\n                                    \"station_id\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"空压站id\"\r\n                                    }\r\n                                },\r\n                                \"required\": [\"start_date\", \"end_date\", \"config_type\", \"station_id\"]\r\n                            }\r\n                        }\r\n                    }\r\n                },\r\n                \"responses\": {\r\n                    \"200\": {\r\n                        \"description\": \"成功响应\"\r\n                    }\r\n                }\r\n            }\r\n        },\r\n        \"\/tool\/v1\/compressor\/getEfficiencyAnalysis\": {\r\n            \"post\": {\r\n                \"description\": \"能效分析，包含空压站日总电量、日总流量、平均压力、单位能耗等信息\",\r\n                \"operationId\": \"getEfficiencyAnalysis\",\r\n                \"requestBody\": {\r\n                    \"content\": {\r\n                        \"application\/json\": {\r\n                            \"schema\": {\r\n                                \"type\": \"object\",\r\n                                \"properties\": {\r\n                                    \"start_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"开始时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"end_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"结束时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"config_type\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"配置类型，固定为2\"\r\n                                    },\r\n                                    \"station_id\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"空压站id\"\r\n                                    }\r\n                                },\r\n                                \"required\": [\"start_date\", \"end_date\", \"config_type\", \"station_id\"]\r\n                            }\r\n                        }\r\n                    }\r\n                },\r\n                \"responses\": {\r\n                    \"200\": {\r\n                        \"description\": \"成功响应\"\r\n                    }\r\n                }\r\n            }\r\n        },\r\n        \"\/tool\/v1\/compressor\/getAirCompressorAnalysis\": {\r\n            \"post\": {\r\n                \"description\": \"空压站下空压机的详细信息，包含设备名称、额定功率、运行模式（0-工频 1-变频）、工频（加载率\/变频：负荷率（%））耗电量占比等信息。\",\r\n                \"operationId\": \"getAirCompressorAnalysis\",\r\n                \"requestBody\": {\r\n                    \"content\": {\r\n                        \"application\/json\": {\r\n                            \"schema\": {\r\n                                \"type\": \"object\",\r\n                                \"properties\": {\r\n                                    \"start_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"开始时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"end_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"结束时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"config_type\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"配置类型，固定为2\"\r\n                                    },\r\n                                    \"station_id\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"空压站id\"\r\n                                    }\r\n                                },\r\n                                \"required\": [\"start_date\", \"end_date\", \"config_type\", \"station_id\"]\r\n                            }\r\n                        }\r\n                    }\r\n                },\r\n                \"responses\": {\r\n                    \"200\": {\r\n                        \"description\": \"成功响应\"\r\n                    }\r\n                }\r\n            }\r\n        },\r\n        \"\/tool\/v1\/compressor\/getFlowAnalysis\": {\r\n            \"post\": {\r\n                \"description\": \"空压站流量分析，包含流量最值、流量类型（1-产气标况流量 2-用气标况流量）等信息。\",\r\n                \"operationId\": \"getFlowAnalysis\",\r\n                \"requestBody\": {\r\n                    \"content\": {\r\n                        \"application\/json\": {\r\n                            \"schema\": {\r\n                                \"type\": \"object\",\r\n                                \"properties\": {\r\n                                    \"start_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"开始时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"end_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"结束时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"config_type\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"配置类型，固定为2\"\r\n                                    },\r\n                                    \"station_id\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"空压站id\"\r\n                                    },\r\n                                    \"device_name\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"根据指标筛选返回数据，可用的device_name包括：总产气量、总用气量\"\r\n                                    },\r\n                                    \"time_type\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"时间类型：second-秒 minute-分钟 hour-小时 day-天\"\r\n                                    },\r\n                                    \"time_value\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"时间值，时间粒度 = 时间类型 + 时间值，例：time_type为minute，time_value为60，则时间粒度为60分钟\"\r\n                                    }\r\n                                },\r\n                                \"required\": [\"start_date\", \"end_date\", \"config_type\", \"station_id\", \"time_type\", \"time_value\"]\r\n                            }\r\n                        }\r\n                    }\r\n                },\r\n                \"responses\": {\r\n                    \"200\": {\r\n                        \"description\": \"成功响应\"\r\n                    }\r\n                }\r\n            }\r\n        },\r\n        \"\/tool\/v1\/compressor\/getFlowRangeDistribution\": {\r\n            \"post\": {\r\n                \"description\": \"空压站的产气流量范围分布，包含在范围内的流量占比、流量最值、平均值。\",\r\n                \"operationId\": \"getFlowRangeDistribution\",\r\n                \"requestBody\": {\r\n                    \"content\": {\r\n                        \"application\/json\": {\r\n                            \"schema\": {\r\n                                \"type\": \"object\",\r\n                                \"properties\": {\r\n                                    \"start_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"开始时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"end_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"结束时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"config_type\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"配置类型，固定为2\"\r\n                                    },\r\n                                    \"station_id\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"空压站id\"\r\n                                    },\r\n                                    \"time_type\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"时间类型：second-秒 minute-分钟 hour-小时 day-天\"\r\n                                    },\r\n                                    \"time_value\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"时间值，时间粒度 = 时间类型 + 时间值，例：time_type为minute，time_value为60，则时间粒度为60分钟\"\r\n                                    },\r\n                                    \"block\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"分块数量，不传则由最大值决定\"\r\n                                    }\r\n                                },\r\n                                \"required\": [\"start_date\", \"end_date\", \"config_type\", \"station_id\", \"time_type\", \"time_value\"]\r\n                            }\r\n                        }\r\n                    }\r\n                },\r\n                \"responses\": {\r\n                    \"200\": {\r\n                        \"description\": \"成功响应\"\r\n                    }\r\n                }\r\n            }\r\n        },\r\n        \"\/tool\/v1\/compressor\/getPressureAnalysis\": {\r\n            \"post\": {\r\n                \"description\": \"空压站的压力分析，包含压力最值、平均值、压力类型（1-产气压力 2-用气压力）等。\",\r\n                \"operationId\": \"getPressureAnalysis\",\r\n                \"requestBody\": {\r\n                    \"content\": {\r\n                        \"application\/json\": {\r\n                            \"schema\": {\r\n                                \"type\": \"object\",\r\n                                \"properties\": {\r\n                                    \"start_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"开始时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"end_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"结束时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"config_type\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"配置类型，固定为2\"\r\n                                    },\r\n                                    \"station_id\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"空压站id\"\r\n                                    },\r\n                                    \"time_type\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"时间类型：second-秒 minute-分钟 hour-小时 day-天\"\r\n                                    },\r\n                                    \"time_value\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"时间值，时间粒度 = 时间类型 + 时间值，例：time_type为minute，time_value为60，则时间粒度为60分钟\"\r\n                                    }\r\n                                },\r\n                                \"required\": [\"start_date\", \"end_date\", \"config_type\", \"station_id\", \"time_type\", \"time_value\"]\r\n                            }\r\n                        }\r\n                    }\r\n                },\r\n                \"responses\": {\r\n                    \"200\": {\r\n                        \"description\": \"成功响应\"\r\n                    }\r\n                }\r\n            }\r\n        },\r\n        \"\/tool\/v1\/compressor\/getPressureDropAnalysis\": {\r\n            \"post\": {\r\n                \"description\": \"空压站的压降分析，包含压降最值、平均值等。\",\r\n                \"operationId\": \"getPressureDropAnalysis\",\r\n                \"requestBody\": {\r\n                    \"content\": {\r\n                        \"application\/json\": {\r\n                            \"schema\": {\r\n                                \"type\": \"object\",\r\n                                \"properties\": {\r\n                                    \"start_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"开始时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"end_date\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"结束时间，格式yyyy-MM-dd\"\r\n                                    },\r\n                                    \"config_type\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"配置类型，固定为2\"\r\n                                    },\r\n                                    \"station_id\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"空压站id\"\r\n                                    },\r\n                                    \"time_type\": {\r\n                                        \"type\": \"string\",\r\n                                        \"description\": \"时间类型：second-秒 minute-分钟 hour-小时 day-天\"\r\n                                    },\r\n                                    \"time_value\": {\r\n                                        \"type\": \"integer\",\r\n                                        \"description\": \"时间值，时间粒度 = 时间类型 + 时间值，例：time_type为minute，time_value为60，则时间粒度为60分钟\"\r\n                                    }\r\n                                },\r\n                                \"required\": [\"start_date\", \"end_date\", \"config_type\", \"station_id\", \"time_type\", \"time_value\"]\r\n                            }\r\n                        }\r\n                    }\r\n                },\r\n                \"responses\": {\r\n                    \"200\": {\r\n                        \"description\": \"成功响应\"\r\n                    }\r\n                }\r\n            }\r\n        }\r\n    },\r\n    \"components\": {\r\n        \"schemas\": {}\r\n    }\r\n}"
        },
        "天气工具": {
            "openapi_spec": "{\r\n    \"openapi\": \"3.1.0\",\r\n    \"info\":\r\n    {\r\n        \"title\": \"天气数据MCP\",\r\n        \"description\": \"获取本周天气情况（温度范围、降雨天数）\",\r\n        \"version\": \"v1.0.0\"\r\n    },\r\n    \"servers\": [\r\n    {\r\n        \"url\": \"https:\/\/mock.apipost.net\/mock\"\r\n    }],\r\n    \"paths\":\r\n    {\r\n        \"\/4ff3871fcc1c000\/?apipost_id=11f435e9fbc086\":\r\n        {\r\n            \"get\":\r\n            {\r\n                \"description\": \"天气情况\",\r\n                \"operationId\": \"getWeather\"\r\n            }\r\n        }\r\n    },\r\n    \"components\":\r\n    {\r\n        \"schemas\":\r\n        {}\r\n    }\r\n}"
        }
    }

    # 初始化统一工具管理器
    await function_calling_manager.initialize(
        mcp_server_configs=mcp_configs,
        openapi_service_configs=openapi_configs
    )

    # 获取工具管理器
    tool_manager = function_calling_manager.get_tool_manager()

    # 获取所有工具定义（用于传递给 LLM）
    tool_definitions = tool_manager.get_all_tool_definitions()
    # print(f"可用工具: {[tool['function']['name'] for tool in tool_definitions]}")

    # 执行工具调用
    client = AsyncOpenAI(
        base_url=os.getenv("MEMORY__LLM__BASE_URL"),
        api_key=os.getenv("MEMORY__LLM__API_KEY")
    )
    response = await client.chat.completions.create(
        model="COSMO-Mind",
        # messages=[{"role": "user", "content": "空压机794在2025-11-11日的能效信息"}],  # OpenAPI调用 - 通过
        # messages=[{"role": "user", "content": "获取今天的天气信息"}],  # OpenAPI调用 - 通过
        # messages=[{"role": "user", "content": "青岛琴屿路的地理坐标"}],  # MCP调用 - 通过
        # messages=[{"role": "user", "content": "青岛琴屿路的地理坐标和上海东华大学的地理坐标"}],  # 多MCP调用 - 通过
        # messages=[{"role": "user", "content": "先查询，空压机794在2025-11-11日的能效信息。再查询，今天的天气。"}],  # 多OpenAPI混合调用
        # messages=[{"role": "user", "content": "一次性完成工具调用。先查询，青岛琴屿路的地理坐标。再查询，空压机794在2025-11-11日的能效信息"}],  # MCP/OpenAPI混合调用
        messages=[{"role": "user", "content": "一次性完成工具调用。先查询，空压机794在2025-11-11日的能效信息；再查询，青岛琴屿路的地理坐标；再查询，今天的天气。"}],  # MCP/OpenAPI混合调用
        tools=tool_definitions
    )
    print("=== LLM Call API Response ===")
    print(response)
    tool_calls = response.choices[0].message.tool_calls
    results = await tool_manager.execute_tools(tool_calls)
    print(f"\n执行结果: {results}")

    # 清理资源
    await function_calling_manager.cleanup()


# 运行示例
# asyncio.run(example_usage())
