from sklearn.decomposition import PCA
import numpy as np
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType, MilvusException, SearchResult
)
from readbetween.config import settings
from readbetween.utils.logger_util import logger_util
from readbetween.utils.model_factory import ModelFactory


class MilvusUtil:
    def __init__(self, uri=None):
        """
        初始化 MilvusUtil 实例并建立连接。

        :param uri: Milvus 服务的地址。
        """
        try:
            self.url = uri or settings.storage.milvus.uri
            self.connect()
        except Exception as e:
            logger_util.error(f"初始化MilvusUtil失败：{e}")
            raise Exception(f"初始化MilvusUtil失败：{e}")

    def connect(self):
        """
        连接到 Milvus 服务。

        :return: None
        """
        try:
            connections.connect("default", uri=self.url)
        except MilvusException as e:
            logger_util.error(f"连接到Milvus失败:{e}")
            raise MilvusException(message=f"连接到Milvus失败:{e}")

    @classmethod
    def check_collection_exists(cls, collection_name):
        """
        检查指定的集合是否存在。

        :param collection_name: 集合名称。
        :return: 如果集合存在返回 True，否则返回 False。
        """
        try:
            Collection(name=collection_name)
            return True
        except MilvusException as e:
            return False

    @classmethod
    def create_collection(cls, collection_name, fields):
        """
        创建一个新的集合。

        :param collection_name: 集合名称。
        :param fields: 字段定义列表，每个字段为一个 FieldSchema 对象。
        :return: None
        """
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
    def insert_data(cls, collection_name, insert_data: list, ids=None):
        """
        向指定集合中插入数据。

        :param collection_name: 集合名称。
        :param insert_data: 要插入的数据列表，每个元素为一个字典。
        :param ids: 自定义主键ID列表，可选。
        :return: None
        """
        try:
            # ids 用于自定义milvus主键
            collection = Collection(collection_name)
            logger_util.debug(f"插入Milvus向量维度{len(insert_data[0]['vector'])}")
            collection.insert(insert_data, ids=ids)
            collection.flush()  # 刷新到磁盘
        except MilvusException as e:
            logger_util.error(f"向{collection_name}集合插入向量失败:{e}")
            raise MilvusException(message=f"向{collection_name}集合插入向量失败:{e}")

    @classmethod
    def similarity_search(cls, query_vector, collection_names, search_params=None, top_k=5, expr=None,
                       output_fields=None):
        """
        根据向量进行相似性搜索。

        :param query_vector: 查询向量。
        :param collection_names: 要搜索的集合名称列表。
        :param search_params: 搜索参数，如 {"metric_type": "L2", "params": {"nprobe": 10}}。
        :param top_k: 返回的最相似结果数量，默认为 5。
        :param expr: 条件过滤表达式，可选。
        :param output_fields: 指定返回的字段列表，可选。
        :return: 搜索结果。
        """
        results = []

        if search_params is None:
            search_params = {"metric_type": "L2", "params": {"ef": 10}}

        try:
            for collection_name in collection_names:
                collection = Collection(collection_name)
                cls.load_collection(collection_name)  # 加载集合
                # 如果用户没有指定输出字段，则默认返回所有字段（除了向量字段本身）
                if output_fields is None:
                    output_fields = [field.name for field in collection.schema.fields if field.name != "vector"]
                result: SearchResult = collection.search(
                    data=[query_vector],
                    anns_field="vector",
                    param=search_params,
                    limit=top_k,
                    expr=expr,  # 条件过滤表达式
                    output_fields=output_fields  # 指定返回的字段
                )

                # 提取结果中的数据
                for hits in result:
                    # <class 'pymilvus.client.abstract.Hits'>
                    for hit in hits:
                        result_dict = hit.to_dict()
                        # 增加collection_name
                        result_dict["collection_name"] = collection_name
                        results.append(result_dict)

            logger_util.info(f"Milvus查询成功，返回结果数量: {len(results)}")
            return results
        except MilvusException as e:
            logger_util.error(f"搜索向量失败：{e}")
            return []

    @classmethod
    def create_index_on_field(cls, collection_name, field_name, index_params):
        """
        在指定字段上创建索引。

        :param collection_name: 集合名称。
        :param field_name: 字段名称。
        :param index_params: 索引参数。
        :return: None
        """
        try:
            collection = Collection(collection_name)
            collection.create_index(field_name=field_name, index_params=index_params)
        except MilvusException as e:
            logger_util.error(f"在{collection_name}集合上字段{field_name}创建索引失败:{e}")
            raise MilvusException(message=f"在{collection_name}集合上字段{field_name}创建索引失败:{e}")

    @classmethod
    def delete_collection(cls, collection_name):
        """
        删除指定的集合。

        :param collection_name: 集合名称。
        :return: None
        """
        try:
            if cls.check_collection_exists(collection_name):
                Collection(collection_name).drop()
                logger_util.info(f"集合{collection_name}已删除")
            else:
                logger_util.warning(f"集合{collection_name}不存在无需删除")
        except MilvusException as e:
            logger_util.error(f"删除集合{collection_name}失败：{e}")
            raise MilvusException(message=f"删除集合{collection_name}失败：{e}")

    @classmethod
    def load_collection(cls, collection_name: str):
        """
        检查集合是否已加载，如果未加载则加载集合到内存中。

        :param collection_name: 集合名称。
        :return: None
        """
        try:
            collection = Collection(collection_name)
            collection.load()
            logger_util.info(f"集合 {collection_name} 已加载到内存。")
        except MilvusException as e:
            logger_util.error(f"加载集合 {collection_name} 失败: {e}")
            raise MilvusException(message=f"加载集合 {collection_name} 失败: {e}")

    @staticmethod
    def close_connection(self):
        """
        断开与 Milvus 的连接。

        :return: None
        """
        try:
            connections.disconnect("default")
        except MilvusException as e:
            logger_util.error(f"断开与Milvus的连接失败：{e}")
            raise MilvusException(message=f"断开与Milvus的连接失败：{e}")

    @classmethod
    def delete_collection_file(cls, collection_name: str, expr: str):
        """
        根据条件删除指定集合中的数据记录。

        :param collection_name: 集合名称。
        :param expr: 条件表达式，用于指定要删除的记录。
        :return: None
        """
        try:
            # 检查集合是否存在
            if cls.check_collection_exists(collection_name):
                # 加载集合到内存
                cls.load_collection(collection_name)

                collection = Collection(collection_name)
                collection.delete(expr)  # 删除符合条件的记录
                collection.flush()  # 刷新集合，确保删除操作生效
                logger_util.info(f"从集合 {collection_name} 中删除了符合条件的记录，条件为: {expr}")
            else:
                logger_util.info(f"当前删除集合 {collection_name} 不存在，已被删除")
        except MilvusException as e:
            logger_util.error(f"删除集合 {collection_name} 中的记录失败，条件为: {expr}，错误信息: {e}")
            raise MilvusException(message=f"删除集合 {collection_name} 中的记录失败，条件为: {expr}，错误信息: {e}")

    @staticmethod
    def unified_pca(vectors, target_dim=1024):
        # 调用示例 ::: query_vectors = MilvusUtil.unified_pca([query_vectors], 1024)[0]
        if isinstance(vectors, list):
            vectors = np.array(vectors)
        original_dim = vectors.shape[1]
        try:
            if original_dim > target_dim:
                # 降维：PCA
                pca = PCA(n_components=target_dim)
                logger_util.debug(f"降维: {original_dim} to {target_dim}")
                return pca.fit_transform(vectors)
            elif original_dim < target_dim:
                # 升维：补零（或选择其他方法）
                logger_util.debug(f"升维: {original_dim} to {target_dim}")
                return np.pad(vectors, ((0, 0), (0, target_dim - original_dim)), mode='constant')
            else:
                # 维度相同：直接返回
                logger_util.debug(f"等维: {original_dim} to {target_dim}")
                return vectors
        except Exception as e:
            logger_util.error(f"PCA维度转换失败: {e}")
            raise Exception(f"PCA维度转换失败: {e}")


def main():
    milvus_client = MilvusUtil()
    model_client = ModelFactory().create_client()

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
    query_vectors = model_client.get_embeddings("卡萨帝热水器").data[0].embedding
    aa = milvus_client.unified_pca([query_vectors], 1024)
    print(aa)

    # results = milvus_client.search_vectors(query_vectors, ["c_awsome_6565131da2524faca0e726ec0ffa26d1", "c_awsome_de8ed36a35a444a19cec145308b78b1f"],)
    # print(len(results))
    # for result in results:
    #     print(result)

    # # 删除指定集合
    # milvus_client.drop_collection("collection_one")
    # milvus_client.drop_collection("collection_two")
    #
    # # 关闭连接
    # milvus_client.close()


# 使用示例
if __name__ == "__main__":
    # asyncio.run(main())
    main()