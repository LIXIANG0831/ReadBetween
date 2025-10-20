#  pip install openapi-llm
#  pip install openapi-spec-validator
import os
import asyncio
from openapi_llm.client.openapi_async import AsyncOpenAPIClient
from openai import AsyncOpenAI
from openapi_llm.client.config import ClientConfig, create_client_config
from openapi_spec_validator import validate


# 校验OpenAPI Schema
def rb_openapi_config_factory(openapi_spec: str, **kwargs) -> ClientConfig:
    config = create_client_config(openapi_spec, **kwargs)
    validate(config.openapi_spec.spec_dict)
    return config


async def main():
    # Firecrawl openapi spec
    openapi_spec_uri = "./firecrawl-v1-openapi.json"

    # Create the async client
    service_api = AsyncOpenAPIClient.from_spec(
        openapi_spec=openapi_spec_uri,
        credentials="fc-xxxxxxxxxxxxxxx"
    )
    # credentials 为鉴权的值 支持 2 种类型传入。
    # 由OpenApi Schema 中的 components - securitySchemes 决定
    # 1. components - securitySchemes - {} - type 为 "apiKey"
    # 对应行为：
    # 请求时，credentials作为api_key。
    # if security_scheme["in"] == "header":
    #     request.setdefault("headers", {})[security_scheme["name"]] = api_key
    # elif security_scheme["in"] == "query":
    #     request.setdefault("params", {})[security_scheme["name"]] = api_key
    # elif security_scheme["in"] == "cookie":
    #     request.setdefault("cookies", {})[security_scheme["name"]] = api_key
    # 2. components - securitySchemes - {} - type 为 "http"
    # 对应行为：
    # 请求时，credentials作为token。
    # request.setdefault("headers", {})["Authorization"] = f"Bearer {token}"

    # Initialize an async LLM (OpenAI)
    client = AsyncOpenAI(
        base_url=os.getenv("MEMORY__LLM__BASE_URL"),
        api_key=os.getenv("MEMORY__LLM__API_KEY")
    )

    # Ask the LLM to call Firecrawl's scraping endpoint
    response = await client.chat.completions.create(
        model=os.getenv("MEMORY__LLM__LLM_NAME"),
        messages=[{"role": "user", "content": "Scrape URL: https://news.ycombinator.com/"}],
        tools=service_api.tool_definitions,
    )
    print("=== LLM Call API Response ===")
    print(response)

    # Use context manager to manage aiohttp sessions
    async with service_api as api:
        service_response = await api.invoke(response)
        print("=== API Execute Response ===")
        print(service_response)
        assert isinstance(service_response, dict)
        assert service_response.get("success", False), "Firecrawl scrape API call failed"


asyncio.run(main())
