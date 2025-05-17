# pip install langchain_mcp_adapters
import json

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.utils.function_calling import convert_to_openai_tool
import asyncio
import openai
from readbetween.settings import get_config

llm = openai.Client(
    api_key=get_config("api.openai.api_key"),
    base_url=get_config("api.openai.base_url")
)

async def main():
    async with MultiServerMCPClient(
            {
                "amap-amap-sse": {
                    "url": "https://mcp.amap.com/sse?key=2f5e7338488ceb95f2252c61e60042fc",
                    "transport": "sse"  # 可以根据参数判断是否是sse | stdio
                }
            }
    ) as client:
        mcpTools = client.get_tools()
        # print(mcpTools)
        openai_tools = [convert_to_openai_tool(tool=t, strict=True) for t in mcpTools]
        # print(openai_tools)
    input_messages = [{"role": "user", "content": "规划从西安到青岛的路线？"}]
    # input_messages = [{"role": "user", "content": "介绍一下你自己"}]
    response_1 = llm.chat.completions.create(
        model="COSMO-GPT",
        messages=input_messages,
        stream=True,
        tools=openai_tools,
        tool_choice="auto"
    )

    # 工具列表
    func_call_list = []
    for chunk in response_1:
        if hasattr(chunk, 'choices') and chunk.choices:
            # print(chunk.choices)

            # 检查是否有内容更新
            if chunk.choices[0].delta and chunk.choices[0].delta.content is not None and chunk.choices[0].delta.content != "":
                print(chunk.choices[0].delta.content)

            # 检查是否有工具调用
            if chunk.choices[0].delta and chunk.choices[0].delta.tool_calls:
                for tcchunk in chunk.choices[0].delta.tool_calls:
                    if len(func_call_list) <= tcchunk.index:
                        func_call_list.append({
                            "id": "",
                            "name": "",
                            "role": "function",
                            "function": {"name": "", "arguments": ""}
                        })
                    tc = func_call_list[tcchunk.index]
                    if tcchunk.id:
                        tc["id"] += tcchunk.id
                    if tcchunk.function.name:
                        tc["function"]["name"] += tcchunk.function.name
                    if tcchunk.function.arguments:
                        tc["function"]["arguments"] += tcchunk.function.arguments
        else:
            print("No choices found in the response chunk.")

    # 根据调用信息获取工具结果
    print("开始工具调用==============》")

    if len(func_call_list) > 0:
        # print(func_call_list)
        # print(input_messages)
        for func_call in func_call_list:
            input_messages.append(func_call)
            tool_call_id = func_call.get("id")
            # 工具调用返回结果
            content = "西安到青岛需要坐2个小时的飞机，今日机票价格为999元。"
            input_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": content
            })
    print("==============》完成工具调用")

    # 再次调用模型 给出工具调用参考
    print(input_messages)
    response_2 = llm.chat.completions.create(
        model="COSMO-GPT",
        messages=input_messages,
        # stream=True,
        tools=openai_tools,
        tool_choice="auto"
    )
    print(response_2.choices[0].message.content)

if __name__ == "__main__":
    asyncio.run(main())