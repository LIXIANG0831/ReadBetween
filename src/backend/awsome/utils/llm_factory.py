from abc import ABC, abstractmethod


class BaseProvider(ABC):
    @abstractmethod
    def generate_text(self, messages, stream=False, temperature=0.1):
        pass

    @abstractmethod
    def get_embeddings(self, inputs=None, dimensions=1024):
        pass


class OpenAIModel(BaseProvider):
    def __init__(self, api_key):
        self.api_key = api_key

    def generate_text(self, messages, stream=False, temperature=0.1):
        # OpenAI模型的文本生成逻辑
        pass

    def get_embeddings(self, inputs=None, dimensions=1024):
        # OpenAI模型的嵌入向量生成逻辑
        pass


class CompatibleOpenAIModel(BaseProvider):
    def __init__(self, api_key):
        self.api_key = api_key

    def generate_text(self, messages, stream=False, temperature=0.1):
        # OpenAI模型的文本生成逻辑
        pass

    def get_embeddings(self, inputs=None, dimensions=1024):
        # OpenAI模型的嵌入向量生成逻辑
        pass


class QwenModel(BaseProvider):
    def __init__(self, api_key):
        self.api_key = api_key

    def generate_text(self, messages, stream=False, temperature=0.1):
        pass

    def get_embeddings(self, inputs=None, dimensions=1024):
        pass


class AnotherModel(BaseProvider):
    # 另一个模型的实现
    pass


# 工厂类
class ModelFactory:
    @staticmethod
    def get_model(mark, api_key):
        if mark == "openai":
            return OpenAIModel(api_key)
        elif mark == "openai-compatible":
            return CompatibleOpenAIModel(api_key)
        elif mark == "qwen":
            return QwenModel(api_key)
