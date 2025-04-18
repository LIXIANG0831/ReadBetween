import asyncio
import json
from abc import ABC, abstractmethod
import dashscope
from openai import OpenAI

from readbetween.models.v1.model_available_cfg import ModelAvailableCfgInfo
from readbetween.utils.redis_util import RedisUtil
from readbetween.services.constant import redis_default_model_key
from readbetween.utils.tools import EncryptionTool

encryption_tool = EncryptionTool()


class BaseModelProvider(ABC):
    @abstractmethod
    async def generate_text(self, messages, stream=False, temperature=0.1, **kwargs):
        pass

    @abstractmethod
    def get_embeddings(self, inputs=None, **kwargs):
        from readbetween.core.dependencies import get_local_embed_manager
        glem = get_local_embed_manager()
        return glem.embed(inputs=inputs)


class OpenAIModelProvider(BaseModelProvider):
    def __init__(self, config):
        self.api_key = config.api_key
        self.base_url = config.base_url
        if config.type == "llm":
            self.llm_name = config.name
            self.embedding_name = ""
        elif config.type == "embedding":
            self.embedding_name = config.name
            self.llm_name = ""
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
        # response = self.client.embeddings.create(
        #     input=inputs,
        #     model=self.embedding_name,
        #     **kwargs
        # )
        # return response
        return super().get_embeddings(inputs=inputs, **kwargs)


class CompatibleOpenAIModelProvider(BaseModelProvider):
    def __init__(self, config):
        self.api_key = config.api_key
        self.base_url = config.base_url
        if config.type == "llm":
            self.llm_name = config.name
            self.embedding_name = ""
        elif config.type == "embedding":
            self.embedding_name = config.name
            self.llm_name = ""
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
        # response = self.client.embeddings.create(
        #     input=inputs,
        #     model=self.embedding_name,
        #     **kwargs
        # )
        # return response
        return super().get_embeddings(inputs=inputs, **kwargs)


class QwenModelProvider(BaseModelProvider):
    def __init__(self, config):
        self.api_key = encryption_tool.decrypt(config.get("api_key"))
        self.base_url = config.get("base_url") or ""
        self.llm_name = config.get("llm_name") or ""
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
        # response = dashscope.TextEmbedding.call(
        #     api_key=self.api_key,
        #     model=self.embedding_name,
        #     input=inputs,
        #     **kwargs
        # )
        # return response
        return super().get_embeddings(inputs=inputs, **kwargs)


class SystemModelProvider(BaseModelProvider):
    def __init__(self, config):
        self.api_key = config.api_key
        self.base_url = config.base_url
        if config.type == "llm":
            self.llm_name = config.name
            self.embedding_name = ""
        elif config.type == "embedding":
            self.embedding_name = config.name
            self.llm_name = ""

    async def generate_text(self, messages, stream=False, temperature=0.1, **kwargs):
        return None

    def get_embeddings(self, inputs=None, **kwargs):
        return super().get_embeddings(inputs=inputs, **kwargs)


# 工厂类
class ModelFactory:
    _default_model_cfg = None
    redis_util = RedisUtil()
    _client_cache = {}  # 全局缓存模型调用Client

    @classmethod
    def _get_default_model_config(cls):  # 已弃用
        if cls._default_model_cfg is None:
            default_model_cfg = cls.redis_util.get(redis_default_model_key)
            if default_model_cfg:
                try:
                    cls._default_model_cfg = json.loads(default_model_cfg)
                    # config api_key 还原
                    cls._default_model_cfg["api_key"] = encryption_tool.decrypt(cls._default_model_cfg.get("api_key"))
                except json.JSONDecodeError:
                    raise ValueError("默认模型配置为无效的Json格式")
            else:
                raise ValueError("Redis中不存在默认模型配置")
        return cls._default_model_cfg

    @classmethod
    def create_client(cls, config: ModelAvailableCfgInfo = None, **kwargs):
        # 解密API_KEY
        config.api_key = encryption_tool.decrypt(config.api_key) if config.api_key != "" else config.api_key
        # 构造缓存键
        cache_key = json.dumps(config.model_dump_json(), sort_keys=True)
        # 检查缓存
        if cache_key in cls._client_cache:
            return cls._client_cache[cache_key]
        # 匹配模型供应商
        if config.mark == "openai":  # 模型供应商标识
            client = OpenAIModelProvider(config)
        elif config.mark == "openai-compatible":
            client = CompatibleOpenAIModelProvider(config)
        elif config.mark == "system":  # 系统内置模型专用标识
            client = SystemModelProvider(config)
        else:
            raise ValueError("Unsupported model provider")

        # 将新创建的实例存储到缓存中
        cls._client_cache[cache_key] = client
        return client


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
