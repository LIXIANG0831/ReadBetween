import asyncio
import litellm



class ModelFactory:
    """
    工厂类，根据模型类型创建不同的客户端实例
    """

    def create_client(self, mark, model_class, model_name, api_key, base_url):
        if model_class == 'llm':
            return LLMFactory(mark, model_name, api_key, base_url)
        elif model_class == 'embedding':
            return EmbeddingFactory(mark, model_name, api_key, base_url)
        else:
            raise ValueError("Unsupported model class")


class LLMFactory:
    """
    根据用户模型配置信息
    获取可调用的LLM客户端
    """

    def __init__(self, mark, model_name, api_key, base_url):
        self.mark = mark
        self.model_name = model_name
        self.base_url = base_url or ""
        self.api_key = api_key

    async def completion(self, messages, stream=False, temperature=0.1):
        # OpenAI-Compatible
        if self.mark == 'openai-compatible':
            response = litellm.completion(
                model=f"openai/{self.model_name}",
                api_key=self.api_key,
                base_url=self.base_url,
                messages=messages,
                stream=stream,
                temperature=temperature
            )
            return response



class EmbeddingFactory:
    """
    根据用户模型配置信息
    获取可调用的Embedding客户端
    """

    def __init__(self, mark, model_name, api_key, base_url):
        self.mark = mark
        self.model_name = model_name
        self.base_url = base_url or ""
        self.api_key = api_key

    def get_client(self):
        pass

if __name__ == '__main__':
    messages = [{"content": "介绍一下你自己。", "role": "user"}]

    fatory = ModelFactory()
    resp = asyncio.run(fatory.create_client("openai-compatible", "llm", "qwen-long", "sk-3fbbebdfbdc04d9284621238b6967ba9", "https://dashscope.aliyuncs.com/compatible-mode/v1").completion(messages=messages))
    print(resp)

