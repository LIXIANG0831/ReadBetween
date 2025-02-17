import os
from mem0 import Memory
from awsome.settings import get_config


class MemoryUtil:
    def __init__(self, config):
        """
        初始化 MemoryUtil 工具类.

        Args:
            config (dict): 内存配置字典，例如 openai_config 或 azure_config.
        """
        self.memory = Memory.from_config(config)

    def add_memory(self, text, user_id):
        """
        向记忆中添加信息.

        Args:
            text (str): 要添加的文本信息.
            user_id (str): 用户ID，用于区分不同用户的记忆.

        Returns:
            dict: 添加操作的结果.
        """
        return self.memory.add(text, user_id=user_id)

    def get_all_memories(self, user_id):
        """
        获取指定用户的所有记忆.

        Args:
            user_id (str): 用户ID.

        Returns:
            list: 用户的所有记忆列表.
        """
        return self.memory.get_all(user_id=user_id)

    def search_memories(self, query, user_id):
        """
        根据查询语句搜索指定用户的相关记忆.

        Args:
            query (str): 查询语句.
            user_id (str): 用户ID.

        Returns:
            list: 相关的记忆列表.
        """
        return self.memory.search(query, user_id=user_id)

    # 可以根据需要添加更多 Memory 类的方法封装


if __name__ == '__main__':
    # 配置文件 (保持不变)
    openai_config = {
        "llm": {  # LLM配置
            "provider": "openai",
            "config": {
                "model": "COSMO-GPT",
                "temperature": 0.1,
                "max_tokens": 2000,
                "top_p": 0.3,
                "api_key": get_config("api.openai.api_key"),
                "openai_base_url": get_config("api.openai.base_url")
            }
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "text-embedding-ada-002",
                "embedding_dims": "768",
                "api_key": get_config("api.openai.api_key"),
                "openai_base_url": get_config("api.openai.base_url")
            }
        },
        "graph_store": {
            "provider": "neo4j",
            "config": {
                # "url": "neo4j+s://localhost:7687",
                "url": "bolt://localhost:7687",
                "username": "neo4j",
                "password": "12345678"
            }
        },
        "vector_store": {
            "provider": "milvus",
            "config": {
                "collection_name": "test",
                "embedding_model_dims": "768",
                "url": get_config("storage.milvus.uri")
            }
        },
        "version": "v1.1"  # v1.1配置支持Graph
    }

    azure_config = {
        "llm": {  # LLM配置
            "provider": "azure_openai",
            "config": {
                "model": "gpt-4o-mini",
                "temperature": 0.1,
                "max_tokens": 2000,
                "azure_kwargs": {
                    "azure_deployment": "",
                    "api_version": "",
                    "azure_endpoint": "",
                    "api_key": ""
                },
            }
        },
        "embedder": {
            "provider": "azure_openai",
            "config": {
                "model": "text-embedding-ada-002",
                "azure_kwargs": {
                    "api_version": "",
                    "azure_deployment": "",
                    "azure_endpoint": "",
                    "api_key": ""
                }
            }
        },
        "graph_store": {
            "provider": "neo4j",
            "config": {
                # "url": "neo4j+s://localhost:7687",
                "url": "bolt://localhost:7687",
                "username": "neo4j",
                "password": "12345678"
            }
        },
        "version": "v1.1"  # v1.1配置支持Graph
    }

    # 使用工具类
    openai_memory_tool = MemoryUtil(openai_config)
    # azure_memory_tool = MemoryUtil(azure_config)

    owner_1 = "lixiang"
    owner_2 = "houxiaoqing"

    # 使用 openai_memory_tool
    results_openai = openai_memory_tool.add_memory("卡奥斯是一家公司", user_id=owner_1)
    print("OpenAI Memory Add Result:", results_openai)

    # openai_memory_tool.add_memory("我喜欢吃面包", user_id=owner_1)
    # openai_memory_tool.add_memory("我最喜欢吃的面包是我女朋友侯晓晴做的司康面包", user_id=owner_1)

    # owner_memery_openai = openai_memory_tool.get_all_memories(user_id=owner_1)
    # print("OpenAI Owner Memories:", owner_memery_openai)

    # query_openai = "我叫什么？"
    # related_memories_openai = openai_memory_tool.search_memories(query_openai, user_id=owner_1)
    # print("OpenAI Related Memories:", related_memories_openai)

    # 使用 azure_memory_tool (如果需要)
    # results_azure = azure_memory_tool.add_memory("一些 Azure 相关信息", user_id=owner_2)
    # print("Azure Memory Add Result:", results_azure)
