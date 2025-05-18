import os
from contextlib import AsyncExitStack
from typing import Dict, Any, List, Union, Tuple

from mcp.client.sse import sse_client
from mcp import ClientSession, StdioServerParameters, stdio_client
import asyncio
import openai
from readbetween.settings import get_config

llm = openai.Client(
    api_key=get_config("api.openai.api_key"),
    base_url=get_config("api.openai.base_url")
)


class MCPClient:
    def __init__(
            self,
            server_configs: List[Union[str, Tuple[str, str]]],
    ):
        """
        初始化 MCP 客户端，支持多种连接方式。

        :param server_configs: 服务器配置列表，可以是：
            - 字符串：表示 stdio 服务脚本路径
            - 元组 (url, type): 表示 SSE 服务器地址和类型
        """
        self.server_configs = server_configs

        self.sessions = {}  # server_id -> (session, session_ctx, connection_ctx)
        self.tool_mapping = {}  # 带前缀的工具名 -> (session, 原始工具名)
        self.exit_stack = AsyncExitStack()

    async def initialize_sessions(self):
        """初始化所有服务器连接，并收集工具映射。"""
        for i, config in enumerate(self.server_configs):
            server_id = f"server{i}"
            try:
                if isinstance(config, str):  # stdio 配置
                    if not (os.path.exists(config) and config.endswith(".py")):
                        print(f"脚本 {config} 不存在或不是 .py 文件，跳过。")
                        continue

                    params = StdioServerParameters(command="python", args=[config], env=None)
                    connection_ctx = stdio_client(params)
                    connection = await self.exit_stack.enter_async_context(connection_ctx)
                    session_ctx = ClientSession(*connection)
                    session = await self.exit_stack.enter_async_context(session_ctx)
                    await session.initialize()
                    self.sessions[server_id] = (session, session_ctx, connection_ctx)
                    print(f"已通过 stdio 连接到 {config}")

                elif isinstance(config, tuple):  # SSE 配置
                    url, _ = config
                    try:
                        # 修改SSE连接方式，添加更健壮的错误处理
                        connection_ctx = sse_client(url=url)
                        connection = await self.exit_stack.enter_async_context(connection_ctx)
                        session_ctx = ClientSession(*connection)
                        session = await self.exit_stack.enter_async_context(session_ctx)
                        await session.initialize()
                        self.sessions[server_id] = (session, session_ctx, connection_ctx)
                        print(f"已通过 SSE 连接到 {url}")
                    except Exception as e:
                        print(f"SSE连接初始化失败: {e}")
                        continue  # 跳过这个服务器，继续下一个

                # 获取工具列表并建立映射
                await self._update_tool_mapping(server_id, session)

            except Exception as e:
                print(f"连接服务器 {server_id} 失败：{e}")

    async def _update_tool_mapping(self, server_id: str, session: ClientSession):
        """更新工具映射"""
        response = await session.list_tools()
        for tool in response.tools:
            prefixed_name = f"{server_id}_{tool.name}"
            self.tool_mapping[prefixed_name] = (session, tool.name)
        print(f"服务器 {server_id} 工具列表：{[tool.name for tool in response.tools]}")

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
            print("所有连接资源已释放")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"清理资源时异常：{e}")
async def main():
    # 配置服务器 - 可以是脚本路径或 (url, type) 元组
    server_configs = [
        # "server.py",  # stdio 服务器
        ("https://mcp.amap.com/sse?key=2f5e7338488ceb95f2252c61e60042fc", "sse"),  # SSE 服务器
        ("https://mcp.amap.com/sse?key=2f5e7338488ceb95f2252c61e60042fc", "sse"),  # SSE 服务器
    ]
    mcp_client = MCPClient(server_configs)
    await mcp_client.initialize_sessions()
    tools = await mcp_client.get_all_tools()
    print(tools)
    # name: maps_weather
    # args: city

    tool_res = await mcp_client.execute_tools([{
        "name": "server0_maps_weather",  # 带服务器前缀的工具名
        "arguments": {  # 工具参数
            "city": "青岛"
        }
    }])
    print(tool_res)
    await mcp_client.cleanup()















    # async with MultiServerMCPClient(
    #         {
    #             "amap-amap-sse": {
    #                 "url": "https://mcp.amap.com/sse?key=2f5e7338488ceb95f2252c61e60042fc",
    #                 "transport": "sse"  # 可以根据参数判断是否是 sse | stdio | streamable_http
    #             }
    #         }
    # ) as client:
    #     mcpTools = client.get_tools()
    #     # print(mcpTools)
    #     openai_tools = [convert_to_openai_tool(tool=t, strict=True) for t in mcpTools]
    #     # print(openai_tools)
    # input_messages = [{"role": "user", "content": "规划从西安到青岛的路线？"}]
    # # input_messages = [{"role": "user", "content": "介绍一下你自己"}]
    # response_1 = llm.chat.completions.create(
    #     model="COSMO-GPT",
    #     messages=input_messages,
    #     stream=True,
    #     tools=openai_tools,
    #     tool_choice="auto"
    # )
    #
    # # 工具列表
    # func_call_list = []
    # for chunk in response_1:
    #     if hasattr(chunk, 'choices') and chunk.choices:
    #         # print(chunk.choices)
    #
    #         # 检查是否有内容更新
    #         if chunk.choices[0].delta and chunk.choices[0].delta.content is not None and chunk.choices[0].delta.content != "":
    #             print(chunk.choices[0].delta.content)
    #
    #         # 检查是否有工具调用
    #         if chunk.choices[0].delta and chunk.choices[0].delta.tool_calls:
    #             for tcchunk in chunk.choices[0].delta.tool_calls:
    #                 if len(func_call_list) <= tcchunk.index:
    #                     func_call_list.append({
    #                         "id": "",
    #                         "name": "",
    #                         "role": "function",
    #                         "function": {"name": "", "arguments": ""}
    #                     })
    #                 tc = func_call_list[tcchunk.index]
    #                 if tcchunk.id:
    #                     tc["id"] += tcchunk.id
    #                 if tcchunk.function.name:
    #                     tc["function"]["name"] += tcchunk.function.name
    #                 if tcchunk.function.arguments:
    #                     tc["function"]["arguments"] += tcchunk.function.arguments
    #     else:
    #         print("No choices found in the response chunk.")
    #
    # # 根据调用信息获取工具结果
    # print("开始工具调用==============》")
    #
    # if len(func_call_list) > 0:
    #     # print(func_call_list)
    #     # print(input_messages)
    #     for func_call in func_call_list:
    #         input_messages.append(func_call)
    #         tool_call_id = func_call["id"]
    #         tool_name = func_call["function"]["name"]
    #         tool_args = func_call["function"]["arguments"]
    #
    #         # TODO 进行工具调用 获取工具返回的内容
    #         try:
    #             # 解析参数
    #             args_dict = json.loads(tool_args)
    #
    #             # 查找对应的工具
    #             tool = next((t for t in mcpTools if t.name == tool_name), None)
    #
    #             print(func_call)
    #             print(args_dict)
    #             print(tool)
    #
    #             if tool:
    #                 # 实际调用工具
    #                 if asyncio.iscoroutinefunction(tool.func):
    #                     # 如果是异步函数
    #                     content = await tool.func(**args_dict)
    #                 else:
    #                     # 如果是同步函数
    #                     content = tool.func(**args_dict)
    #
    #                 # 确保内容是字符串格式
    #                 if not isinstance(content, str):
    #                     content = json.dumps(content, ensure_ascii=False)
    #             else:
    #                 content = f"Error: Tool {tool_name} not found"
    #
    #         except Exception as e:
    #             content = f"Error calling tool {tool_name}: {str(e)}"
    #
    #         # content = "西安到青岛需要坐2个小时的飞机，今日机票价格为999元。"
    #         print(content)
    #
    #         input_messages.append({
    #                 "role": "tool",
    #                 "tool_call_id": tool_call_id,
    #                 "content": content
    #         })
    # print("==============》完成工具调用")
    #
    # # 再次调用模型 给出工具调用参考
    # print(input_messages)
    # response_2 = llm.chat.completions.create(
    #     model="COSMO-GPT",
    #     messages=input_messages,
    #     # stream=True,
    #     tools=openai_tools,
    #     tool_choice="auto"
    # )
    # print(response_2.choices[0].message.content)

if __name__ == "__main__":
    asyncio.run(main())