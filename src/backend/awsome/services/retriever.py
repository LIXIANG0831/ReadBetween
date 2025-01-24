import asyncio
import json
from typing import List, Dict, Union, Optional
from awsome.services.base import BaseService
from awsome.utils.elasticsearch_util import ElasticSearchUtil
from awsome.utils.logger_util import logger_util
from awsome.models.schemas.es.base import BaseDocument
from awsome.utils.milvus_util import MilvusUtil
from awsome.utils.model_factory import ModelFactory


class RetrieverService(BaseService):
    @classmethod
    async def retrieve(
            cls,
            query: str,
            mode: str = "both",  # 检索模式：'milvus', 'es', 'both'
            milvus_collection_name: Optional[str] = None,
            milvus_fields: List[str] = None,
            es_index_name: Optional[str] = None,
            es_fields: List[str] = None,
            es_query: Union[str, Dict] = None,
            top_k: int = 5,
    ) -> Dict:
        """
        检索服务，支持通过 Milvus 和 Elasticsearch 进行检索。
        :param query: 查询内容。
        :param mode: 检索模式，可选值为 'milvus'、'es' 或 'both'。
        :param milvus_collection_name: Milvus 集合名称。
        :param milvus_fields: Milvus 返回的字段列表。
        :param es_index_name: Elasticsearch 索引名称。
        :param es_fields: Elasticsearch 返回的字段列表。
        :param es_query: Elasticsearch 查询内容，可以是字符串或字典。
        :param top_k: 返回的最相似结果数量，默认为 5。
        :return: 检索结果字典。
        """
        results = {"milvus": None, "es": None}

        # 初始化 Milvus 和 Elasticsearch 客户端
        milvus_client = MilvusUtil()
        es_client = ElasticSearchUtil()

        # 检索模式：仅使用 Milvus
        if mode in ["milvus", "both"]:
            if not milvus_collection_name:
                logger_util.error("未指定 Milvus 集合名称")
                raise ValueError("未指定 Milvus 集合名称")

            # 获取查询向量
            model_client = ModelFactory().create_client()
            query_vector = model_client.get_embeddings(query).data[0].embedding

            # 在 Milvus 中进行向量检索
            try:
                milvus_results = milvus_client.search_vectors(
                    query_vectors=query_vector,
                    collection_names=[milvus_collection_name],
                    top_k=top_k,
                    output_fields=milvus_fields,
                )
                results["milvus"] = milvus_results[milvus_collection_name]
            except Exception as e:
                logger_util.error(f"Milvus 检索失败: {e}")

        # 检索模式：仅使用 Elasticsearch
        if mode in ["es", "both"]:
            if not es_index_name:
                logger_util.error("未指定 Elasticsearch 索引名称")
                raise ValueError("未指定 Elasticsearch 索引名称")

            # 构建 Elasticsearch 查询
            if es_query is None:
                es_query = query  # 默认使用简单字符串查询

            try:
                es_results = es_client.search_documents(
                    index_name=es_index_name,
                    query=es_query,
                    size=top_k,
                    fields=es_fields,
                )
                results["es"] = es_results
            except Exception as e:
                logger_util.error(f"Elasticsearch 检索失败: {e}")

        # 返回检索结果
        return results

    @classmethod
    async def rerank_retrieve(cls):
        # TODO 检索重排序
        pass


async def main():
    # c_awsome_2691029c826546819578e5e69a8afc23
    # i_awsome_fba56f730a124d5895db003677734978
    考虑多个collection
    retrieve_resp = await RetrieverService.retrieve("卡萨帝热水器",
                                                    milvus_collection_name="c_awsome_2691029c826546819578e5e69a8afc23",
                                                    milvus_fields=['text'],
                                                    es_index_name="i_awsome_fba56f730a124d5895db003677734978",
                                                    es_fields=['text'])
    print(retrieve_resp)

if __name__ == '__main__':
    asyncio.run(main())