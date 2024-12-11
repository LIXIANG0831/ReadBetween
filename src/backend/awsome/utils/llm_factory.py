from abc import ABC, abstractmethod
import dashscope
from openai import OpenAI


class BaseLLMModel(ABC):
    @abstractmethod
    def generate_text(self, messages, stream=False, temperature=0.1, **kwargs):
        pass


class BaseEmbeddingModel(ABC):
    @abstractmethod
    def get_embeddings(self, inputs=None, **kwargs):
        pass


class OpenAILLMModel(BaseLLMModel):
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def generate_text(self, messages, stream=False, temperature=0.1, **kwargs):
        # OpenAI模型的文本生成逻辑
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=stream,
            **kwargs
        )
        return response


class OpenAIEmbeddingModel(BaseEmbeddingModel):
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def get_embeddings(self, inputs=None, **kwargs):
        # OpenAI模型的嵌入向量生成逻辑
        response = self.client.embeddings.create(
            input=inputs,
            model=self.model,
            **kwargs
        )
        return response


class CompatibleOpenAILLMModel(BaseLLMModel):
    def __init__(self, api_key, model, base_url):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def generate_text(self, messages, stream=False, temperature=0.1, **kwargs):
        # OpenAI模型的文本生成逻辑
        pass


class CompatibleOpenAIEmbeddingModel(BaseEmbeddingModel):
    def __init__(self, api_key, base_url, model):
        self.api_key = api_key

    def get_embeddings(self, inputs=None, **kwargs):
        # OpenAI模型的嵌入向量生成逻辑
        pass


class QwenLLMModel(BaseLLMModel):
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model

    def generate_text(self, messages, stream=False, temperature=0.1, **kwargs):
        response = dashscope.Generation.call(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=self.api_key,
            model=self.model,  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            messages=messages,
            result_format='message',
            stream=stream,
            temperature=temperature,
            **kwargs
        )
        return response


class QwenEmbeddingModel(BaseEmbeddingModel):
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model

    def get_embeddings(self, inputs=None, **kwargs):
        response = dashscope.TextEmbedding.call(
            api_key=self.api_key,
            model=self.model,
            input=inputs,
            **kwargs
        )
        return response


class AnotherLLMModel(BaseLLMModel):
    def generate_text(self, messages, stream=False, temperature=0.1, **kwargs):
        pass


class AnotherEmbeddingModel(BaseEmbeddingModel):
    def get_embeddings(self, inputs=None, **kwargs):
        pass


# 工厂类
class ModelFactory:
    @staticmethod
    def get_model(model_class, mark, api_key, **kwargs):
        # kwargs 取值
        model = kwargs.get("model")
        base_url = kwargs.get("base_url")

        if model_class == "llm":
            if mark == "openai":
                return OpenAILLMModel(api_key)
            elif mark == "openai-compatible":
                return CompatibleOpenAILLMModel(api_key, model, base_url)
            elif mark == "qwen":
                return QwenLLMModel(api_key, model)
        elif model_class == "embedding":
            if mark == "openai":
                return OpenAIEmbeddingModel(api_key)
            elif mark == "openai-compatible":
                return CompatibleOpenAIEmbeddingModel(api_key)
            elif mark == "qwen":
                return QwenEmbeddingModel(api_key, model)
        else:
            raise ValueError("Unsupported model class")


if __name__ == '__main__':
    # messages = [{"content": "介绍一下你自己。", "role": "user"}]
    # llm_model = ModelFactory.get_model("llm",
    #                                    "qwen",
    #                                    "sk-3fbbebdfbdc04d9284621238b6967ba9",
    #                                    model="qwen-long")
    # response = llm_model.generate_text(messages)
    # print(response)

    embedding_model = ModelFactory.get_model("embedding",
                                             "qwen",
                                             "sk-3fbbebdfbdc04d9284621238b6967ba9",
                                             model="text-embedding-v3")
    response = embedding_model.get_embeddings("今天天气怎么样")
    print(response)
