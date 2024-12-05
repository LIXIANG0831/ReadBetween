from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType, MilvusException
)
from awsome.settings import get_config
from awsome.utils.logger_util import logger_util


class MilvusUtil:
    def __init__(self, host=None, port=None):
        try:
            host = host or get_config("storage.milvus.host")
            port = port or get_config("storage.milvus.port")
            self.host = host
            self.port = port
            self.connect()
        except Exception as e:
            logger_util.error(f"初始化MilvusUtil失败：{e}")
            raise Exception(f"初始化MilvusUtil失败：{e}")

    def connect(self):
        try:
            connections.connect("default", host=self.host, port=self.port)
        except MilvusException as e:
            logger_util.error(f"连接到Milvus失败:{e}")
            raise MilvusException(message=f"连接到Milvus失败:{e}")

    @classmethod
    def has_collection(self, collection_name):
        try:
            Collection(name=collection_name)
            return True
        except MilvusException as e:
            return False

    @classmethod
    def create_collection(self, collection_name, fields):
        try:
            field_schemas = [
                field
                for field in fields
            ]
            schema = CollectionSchema(fields=field_schemas, description="Collection for storing vectors")
            Collection(name=collection_name, schema=schema)
        except MilvusException as e:
            logger_util.error(f"创建集合{collection_name}失败:{e}")
            raise MilvusException(message=f"创建集合{collection_name}失败:{e}")

    @classmethod
    def insert_data(self, collection_name, insert_data: list, ids=None):
        try:
            collection = Collection(collection_name)
            collection.insert(insert_data, ids=ids)
            collection.flush()  # 刷新到磁盘
        except MilvusException as e:
            logger_util.error(f"向{collection_name}集合插入向量失败:{e}")
            raise MilvusException(message=f"向{collection_name}集合插入向量失败:{e}")

    @classmethod
    def search_by_vectors(self, query_vectors, collection_names, top_k=5):
        results = {}
        try:
            for collection_name in collection_names:
                collection = Collection(collection_name)
                search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
                result = collection.search(query_vectors, "vector_field_name", search_params, limit=top_k)
                results[collection_name] = result
            return results
        except MilvusException as e:
            logger_util.error(f"搜索向量失败：{e}")
            return {}

    @classmethod
    def create_index_on_field(self, collection_name, field_name, index_params):
        try:
            collection = Collection(collection_name)
            collection.create_index(field_name=field_name, index_params=index_params)
        except MilvusException as e:
            logger_util.error(f"在{collection_name}集合上字段{field_name}创建索引失败:{e}")
            raise MilvusException(message=f"在{collection_name}集合上字段{field_name}创建索引失败:{e}")

    @classmethod
    def drop_collection(self, collection_name):
        try:
            if self.has_collection(collection_name):
                Collection(collection_name).drop()
            else:
                logger_util.warning(f"集合{collection_name}不存在无需删除")
        except MilvusException as e:
            logger_util.error(f"删除集合{collection_name}失败：{e}")
            raise MilvusException(message=f"删除集合{collection_name}失败：{e}")

    @staticmethod
    def close(self):
        try:
            connections.disconnect("default")
        except MilvusException as e:
            logger_util.error(f"断开与Milvus的连接失败：{e}")
            raise MilvusException(message=f"断开与Milvus的连接失败：{e}")


# 使用示例
if __name__ == "__main__":
    # milvus_client = MilvusUtil()
    #
    # # 创建集合
    # fields = [
    #     {"name": "id", "dtype": DataType.INT64, "is_primary": True},
    #     {"name": "vector_field_name", "dtype": DataType.FLOAT_VECTOR}
    # ]
    # milvus_client.create_collection("collection_one", fields)
    # milvus_client.create_collection("collection_two", fields)
    #
    # # 向指定集合插入向量
    # data = [
    #     {"id": 1, "name": "Alice", "age": 30, "height": 165.5, "embedding": [float(i) for i in range(128)]},
    #     {"id": 2, "name": "Bob", "age": 24, "height": 180.2, "embedding": [float(i) for i in range(128, 256)]},
    # ]
    # milvus_client.insert_data("collection_one", data)
    #
    # # 为集合创建索引
    # index_params = {"index_type": "IVF_FLAT", "nlist": 1024}
    # milvus_client.create_index("collection_one", "vector_field_name", index_params)
    # milvus_client.create_index("collection_two", "vector_field_name", index_params)
    #
    # # 从多个集合中搜索向量
    # query_vectors = [[0.1, 0.2, 0.3]]
    # results = milvus_client.search_by_vectors(query_vectors, ["collection_one", "collection_two"])
    # print(results)
    #
    # # 删除指定集合
    # milvus_client.drop_collection("collection_one")
    # milvus_client.drop_collection("collection_two")
    #
    # # 关闭连接
    # milvus_client.close()
    pass
