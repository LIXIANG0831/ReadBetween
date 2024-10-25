import asyncio
from typing import List, Dict, Any
from awsome.settings import get_config
from awsome.utils.logger_client import logger_client
from tavily import TavilyClient
from tavily.errors import UsageLimitExceededError
from fastapi import HTTPException
import openai

tavily_api_key = get_config("api.tavily.api_key")
tavily_api_keys = get_config("api.tavily.api_keys")
tavily_client = TavilyClient(api_key=tavily_api_key)


def _tavily_search():
    # 1. Executing a simple search query
    response_1 = tavily_client.search("今天西安天气怎么样？")
    # 2. Executing a context search query
    response_2 = tavily_client.get_search_context("今天西安天气怎么样？")
    # 3. Executing a Q&A search query
    response_3 = tavily_client.qna_search("今天西安天气怎么样？")

    print(response_1)
    print(response_2)
    print(response_3)


current_api_key_index = 0


async def search_with_retry(query: str, retries: int = 3) -> list[dict[str, Any]]:
    global current_api_key_index
    for attempt in range(retries):
        try:
            # 设置当前 API 密钥
            tavily_client.api_key = tavily_api_keys[current_api_key_index]
            search_resp = tavily_client.search(
                query=query,
                topic="general",
                search_depth="advanced",
                days=3,
                max_results=3,
                include_raw_content=False,
                include_images=False,
                include_answer=True,
            )
            search_results = search_resp.get("results", [])
            target_url = []
            for result in search_results:
                target_url.append(result.get("url", ""))
            # 抓取二级网页
            extract_resp = tavily_client.extract(target_url)
            extract_results = extract_resp.get("results", [])
            tavily_results = []
            for result in extract_results:
                url = result.get("url", "")
                raw_content = result.get("raw_content", "")
                tavily_dict = {
                    "url": url,
                    "raw_content": raw_content,
                }
                tavily_results.append(tavily_dict)

            return tavily_results
        except UsageLimitExceededError:
            # 切换到下一个 API 密钥
            current_api_key_index = (current_api_key_index + 1) % len(tavily_api_keys)
            logger_client.warning(f"使用限制超出，切换到 API 密钥索引: {current_api_key_index}")
        except Exception as e:
            logger_client.error(f"搜索过程中发生错误: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=503, detail="所有 API 密钥均已超出使用限制。")


openai_client = openai.Client(
    api_key="xxx",  # 请替换为你的实际API密钥
    base_url=f"http://10.193.22.12:9997/v1"
)


async def tavily_search_with_llm(query: str):
    tavily_results = await search_with_retry(query)

    context_list = []  # 网络检索上下文
    url_list = []  # 溯源信息
    messages = []  # 模型接收信息

    for result in tavily_results:
        url_list.append(result.get("url", ""))
        context_list.append(result.get("raw_content", ""))
    messages.append(
        {
            "role": "user",
            "content": f'网络检索内容: """{context_list}"""\n\n'
                       f'以上信息是来源于网络检索以及延长石油的知识库中，与用户问题相关的检索信息。'
                       f'请结合用户问题，根据信息回答问题。'
                       f'1. 当用户问题不需要网络搜索时，请忽略网络检索内容提供的信息，基于你的理解直接进行回复。'
                       f'2. 当用户问题需要进行网络搜索时，请结合网络检索内容提供的信息进行回复。'
                       f'不要提及网络搜索信息，只针对用户的问题进行回复。'
                       f'用户的问题为: "{query}" '
        }
    )

    response = openai_client.chat.completions.create(
        model="gpt-4-32k",
        messages=messages,
    )
    print("\033[31m=== 网络检索上下文信息 ===\033[0m")
    for context in context_list:
        print(context)
    print("\033[31m=== 网络溯源信息 ===\033[0m")
    for url in url_list:
        print(url)
    print("\033[31m=== 模型回答信息 ===\033[0m")
    print(response.choices[0].message.content)


# _tavily_search()
asyncio.run(tavily_search_with_llm("今天西安的天气怎么样？"))
