import asyncio
import json
from abc import ABC, abstractmethod
import dashscope
from openai import OpenAI
from awsome.utils.redis_util import RedisUtil
from awsome.utils.tools import EncryptionTool
from awsome.services.constant import redis_default_model_key
from fastapi.responses import StreamingResponse
from typing import AsyncIterable

encryption_tool = EncryptionTool()


class BaseModelProvider(ABC):
    @abstractmethod
    async def generate_text(self, messages, stream=False, temperature=0.1, **kwargs):
        pass

    @abstractmethod
    def get_embeddings(self, inputs=None, **kwargs):
        pass


class OpenAIModelProvider(BaseModelProvider):
    def __init__(self, config):
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.llm_name = config.get("llm_name")
        self.embedding_name = config.get("embedding_name")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    async def generate_text(self, messages, stream=False, temperature=0.1, **kwargs):
        # OpenAI模型的文本生成逻辑
        response = self.client.chat.completions.create(
            model=self.llm_name,
            messages=messages,
            temperature=temperature,
            stream=stream,
            **kwargs
        )
        return response

    def get_embeddings(self, inputs=None, **kwargs):
        # OpenAI模型的嵌入向量生成逻辑
        response = self.client.embeddings.create(
            input=inputs,
            model=self.embedding_name,
            **kwargs
        )
        return response


class CompatibleOpenAIModelProvider(BaseModelProvider):
    def __init__(self, config):
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.llm_name = config.get("llm_name")
        self.embedding_name = config.get("embedding_name")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    async def generate_text(self, messages, stream=False, temperature=0.1, **kwargs):
        # OpenAI模型的文本生成逻辑
        response = self.client.chat.completions.create(
            model=self.llm_name,
            messages=messages,
            temperature=temperature,
            stream=stream,
            **kwargs
        )
        return response

    def get_embeddings(self, inputs=None, **kwargs):
        # OpenAI模型的嵌入向量生成逻辑
        response = self.client.embeddings.create(
            input=inputs,
            model=self.embedding_name,
            **kwargs
        )
        return response


class QwenModelProvider(BaseModelProvider):
    def __init__(self, config):
        self.api_key = encryption_tool.decrypt(config.get("api_key"))
        self.base_url = config.get("base_url")
        self.llm_name = config.get("llm_name")
        self.embedding_name = config.get("embedding_name")

    async def generate_text(self, messages, stream=False, temperature=0.1, **kwargs):
        response = dashscope.Generation.call(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=self.api_key,
            model=self.llm_name,  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            messages=messages,
            result_format='message',
            stream=stream,
            temperature=temperature,
            **kwargs
        )
        return response

    def get_embeddings(self, inputs=None, **kwargs):
        response = dashscope.TextEmbedding.call(
            api_key=self.api_key,
            model=self.embedding_name,
            input=inputs,
            **kwargs
        )
        return response


# 工厂类
class ModelFactory:
    _default_model_cfg = None
    redis_util = RedisUtil()

    @classmethod
    def _get_default_model_config(cls):
        if cls._default_model_cfg is None:
            default_model_cfg = cls.redis_util.get(redis_default_model_key)
            if default_model_cfg:
                try:
                    cls._default_model_cfg = json.loads(default_model_cfg)
                except json.JSONDecodeError:
                    raise ValueError("默认模型配置为无效的Json格式")
            else:
                raise ValueError("Redis中不存在默认模型配置")
        return cls._default_model_cfg

    @staticmethod
    def create_client(config=None, **kwargs):
        if config is None:
            config = ModelFactory._get_default_model_config()

        # 默认配置外 程序中可单独指定默认供应商的其他模型
        if kwargs.get("embedding_name") is not None:
            config["embedding_name"] = kwargs.get("embedding_name")
        if kwargs.get("llm_name") is not None:
            config["llm_name"] = kwargs.get("llm_name")

        provider = config.get("provider_mark")
        # config api_key 还原
        config["api_key"] = encryption_tool.decrypt(config.get("api_key"))
        if provider == "openai":
            return OpenAIModelProvider(config)
        elif provider == "openai-compatible":
            return CompatibleOpenAIModelProvider(config)
        else:
            raise ValueError("Unsupported model provider")


if __name__ == '__main__':
    # {
    #     "model_cfg_id": "7168786f-96d8-4a27-9bbc-106fb2180ffd",
    #     "api_key": "gAAAAABnhkSV7l63z9WP2wJoj3moIGT1IhK6RKfRZNkcEbHAA2eMtbPi7nprT8oDQEGYJzpaiEG4zmz8iIWOLNfFiMeu5caGLIx7bNcHp5iWyZi34GB_TR_7_j_-cH4VRWGC6jSElWW9",
    #     "base_url": "https://xianglee-gemini-play.deno.dev/v1",
    #     "provider_mark": "openai-compatible",
    #     "llm_name": "gemini-2.0-flash-exp",
    #     "embedding_name": "text-embedding-004"
    # }

    async def main():
        # client = ModelFactory.create_client()

        messages = [
            {"role": "system", "content": "你是一个有帮助的 AI 助手。"},
            {"role": "user", "content": "为什么海水在阳光下是蓝色的。"}
        ]
        # 阻塞返回
        # llm_resp = await client.generate_text(messages=messages)
        # print(llm_resp)
        # 流式返回
        # llm_stream_resp = await client.generate_text(messages=messages, stream=True)
        # for chunk in llm_stream_resp:
        #     print(chunk.choices[0].delta.content or '', end='')
        # embedding_resp = await client.get_embeddings(inputs="天王盖地虎，宝塔镇河妖。")
        # print(embedding_resp)

        #-------------------------------------------------------
        client = ModelFactory.create_client(llm_name="gemini-1.5-flash-8b", embedding_name="embedding-001")
        # 单独指定llm
        llm_stream_resp = await client.generate_text(messages=messages, stream=True)
        for chunk in llm_stream_resp:
            print(chunk.choices[0].delta.content or '', end='')
        # 单独指定embedding
        embedding_resp = client.get_embeddings(inputs="天王盖地虎，宝塔镇河妖。")
        print(embedding_resp)


    asyncio.run(main())
