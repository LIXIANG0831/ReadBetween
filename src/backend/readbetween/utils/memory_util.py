from mem0 import Memory


class MemoryUtil:
    def __init__(self, config):
        """
        初始化 MemoryUtil 工具类.

        Args:
            config (dict): 内存配置字典.
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

    def search_memories(self, query, user_id, limit=3):
        """
        根据查询语句搜索指定用户的相关记忆.

        Args:
            query (str): 查询语句.
            user_id (str): 用户ID.
            limit (int): 返回条数

        Returns:
            list: 相关的记忆列表.
            str: 拼接记忆列表为字符串.
        """
        memory = self.memory.search(query, user_id=user_id, limit=limit)
        original_memories = memory.get("results", [])
        graph_entities = memory.get("relations", [])
        memory_str_list = []
        # 向量数据库
        for vc_memory_str in original_memories:
            current_memory_str = vc_memory_str.get("memory", "")
            memory_str_list.append(current_memory_str)
        # 图数据库
        for graph_memory_str in graph_entities:
            source = graph_memory_str.get("source", "")
            relationship = graph_memory_str.get("relationship", "")
            target = graph_memory_str.get("target", "")
            # 替换UUID为用户 防止模型理解不充分
            source, target = ("用户" if source == user_id else source), ("用户" if target == user_id else target)
            current_memory_str = f"[{source}][{relationship}][{target}]"
            memory_str_list.append(current_memory_str)

        return memory, "\n".join(f"- {memory_str}" for memory_str in memory_str_list)

    def delete_all_memories(self, user_id):
        """
        删除指定用户的相关记忆.

        Args:
            user_id (str): 用户ID.

        """
        self.memory.delete_all(user_id=user_id)


if __name__ == '__main__':
    # 配置文件
    from readbetween.services.constant import memory_config

    # 使用工具类
    openai_memory_tool = MemoryUtil(memory_config)

    owner_1 = "lixiang"
    owner_2 = "houxiaoqing"

    # 使用 openai_memory_tool
    # openai_memory_tool.add_memory("卡奥斯是一家公司", user_id=owner_1)
    # openai_memory_tool.add_memory("我喜欢吃面包", user_id=owner_1)
    # openai_memory_tool.add_memory("我最喜欢吃的面包是我女朋友侯晓晴做的司康面包", user_id=owner_1)

    # owner_memery_openai = openai_memory_tool.get_all_memories(user_id=owner_1)
    # print("OpenAI Owner Memories:", owner_memery_openai)

    query_openai = "精神抖擞啊"
    related_memories_openai, related_memories_str= openai_memory_tool.search_memories(query_openai, user_id=owner_1, limit=1)
    print(related_memories_str)
    print("OpenAI Related Memories:", related_memories_openai)