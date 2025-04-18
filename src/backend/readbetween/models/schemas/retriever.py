class RetrieverResult:
    def __init__(self, source, name, id, score, metadata, text, vector=None):
        """
        用于表示召回结果的通用类。
        :param source: 来源（"es" 或 "milvus"）
        :param name: 集合名称 | 索引名称
        :param id: 文档 ID | 集合 ID
        :param score: 相似度分数或相关性分数
        :param metadata: 元数据（字典形式）
        :param text: 文本内容
        :param vector: 向量（仅 Milvus 有，可选）
        """
        self.source = source  # 数据来源（"es" 或 "milvus"）
        self.name = name  # 集合名称或索引名称
        self.id = id  # 文档 ID 或集合 ID
        self.score = score  # 相似度分数或相关性分数
        self.metadata = metadata  # 元数据
        self.text = text  # 文本内容
        self.vector = vector  # 向量（仅 Milvus 有）

    def to_dict(self):
        """
        将召回结果转换为字典格式，方便后续处理。
        """
        result_dict = {
            "source": self.source,
            "name": self.name,
            "id": self.id,
            "score": self.score,
            "metadata": self.metadata,
            "text": self.text,
        }
        if self.vector is not None:
            result_dict["vector"] = self.vector
        return result_dict
