#  pip install openapi-llm
#  pip install openapi-spec-validator
import os
import asyncio
from typing import Any, Optional, Union, Callable

import aiohttp
from openapi_llm.client.openapi_async import AsyncOpenAPIClient, AsyncOpenAPIClientError, AsyncHttpClientError
from openai import AsyncOpenAI
from openapi_llm.client.config import ClientConfig, create_client_config
from openapi_spec_validator import validate
from openapi_llm.utils import build_request, apply_authentication
from pathlib import Path


# 校验OpenAPI Schema
def rb_openapi_config_factory(openapi_spec: str, **kwargs) -> ClientConfig:
    config = create_client_config(openapi_spec, **kwargs)
    validate(config.openapi_spec.spec_dict)
    return config


class CustomAsyncOpenAPIClient(AsyncOpenAPIClient):
    """自定义异步OpenAPI客户端，支持配置超时时间"""

    def __init__(self, client_config: ClientConfig, timeout: float = 180):
        super().__init__(client_config)
        self.timeout = timeout

    async def invoke(self, function_payload: Any) -> Any:
        """
        重写invoke方法，使用自定义超时时间
        """
        fn_invocation_payload = {}
        try:
            fn_extractor = self.client_config.get_payload_extractor()
            fn_invocation_payload = fn_extractor(function_payload)
        except Exception as e:
            raise AsyncOpenAPIClientError(
                f"Error extracting function invocation payload: {str(e)}"
            ) from e

        if (
                "name" not in fn_invocation_payload
                or "arguments" not in fn_invocation_payload
        ):
            raise AsyncOpenAPIClientError(
                f"Function invocation payload does not contain 'name' or 'arguments' keys: {fn_invocation_payload}, "
                f"the payload extraction function may be incorrect."
            )

        operation = self.client_config.openapi_spec.find_operation_by_id(
            fn_invocation_payload["name"]
        )
        request = build_request(operation, self.client_config, **fn_invocation_payload["arguments"])
        apply_authentication(self.client_config.get_authenticator(), operation, request)

        if not self._session:
            self._session = aiohttp.ClientSession()
            self._owns_session = True

        try:
            async with self._session.request(
                    request["method"],
                    request["url"],
                    headers=request.get("headers", {}),
                    params=request.get("params", {}),
                    json=request.get("json"),
                    timeout=self.timeout  # 使用自定义超时时间
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise AsyncHttpClientError(f"HTTP error occurred: {e}") from e
        except Exception as e:
            raise AsyncHttpClientError(f"An error occurred: {e}") from e

    @classmethod
    def from_spec(
            cls,
            openapi_spec: Union[str, Path],
            config_factory: Optional[Callable[[Union[str, Path]], ClientConfig]] = None,
            timeout: float = 180,
            **kwargs
    ) -> "CustomAsyncOpenAPIClient":
        """
        自定义的from_spec方法，支持超时参数
        """
        if config_factory:
            config = config_factory(openapi_spec, **kwargs)
        else:
            config = create_client_config(openapi_spec, **kwargs)
        return cls(config, timeout=timeout)


async def main():
    # Firecrawl openapi spec
    openapi_spec_uri = "./firecrawl-v1-openapi.json"

    # 使用自定义客户端，设置180秒超时
    service_api = CustomAsyncOpenAPIClient.from_spec(
        openapi_spec=openapi_spec_uri,
        credentials="fc-xxxxxxxxxxxxxxx",
        timeout=180  # 设置180秒超时
    )

    # Initialize an async LLM (OpenAI)
    client = AsyncOpenAI(
        base_url=os.getenv("MEMORY__LLM__BASE_URL"),
        api_key=os.getenv("MEMORY__LLM__API_KEY")
    )

    # Ask the LLM to call Firecrawl's scraping endpoint
    response = await client.chat.completions.create(
        model=os.getenv("MEMORY__LLM__LLM_NAME"),
        messages=[{"role": "user", "content": "查询806号空压机在2025-11-26到2025-11-26的图表数据"}],
        tools=service_api.tool_definitions,
    )
    print("=== LLM Call API Response ===")
    print(response)

    # 使用异步上下文管理器
    async with service_api as api:
        service_response = await api.invoke(response)
        print("=== API Execute Response ===")
        print(service_response)
        assert isinstance(service_response, dict)
        assert service_response.get("success", False), "Firecrawl scrape API call failed"


if __name__ == "__main__":
    asyncio.run(main())