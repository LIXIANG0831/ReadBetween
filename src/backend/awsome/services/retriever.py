import asyncio
import json
import threading
from typing import List, Dict, Union, Optional

from awsome.models.schemas.retriever import RetrieverResult
from awsome.services.base import BaseService
from awsome.utils.elasticsearch_util import ElasticSearchUtil
from awsome.utils.logger_util import logger_util
from awsome.utils.milvus_util import MilvusUtil
from awsome.utils.model_factory import ModelFactory


class RetrieverService(BaseService):
    # 添加类属性
    _milvus_client = None
    _es_client = None
    _model_client = None

    @classmethod
    def _get_clients(cls):
        """初始化所有客户端（线程安全）"""
        with threading.Lock():
            if cls._milvus_client is None:
                cls._milvus_client = MilvusUtil()
            if cls._es_client is None:
                cls._es_client = ElasticSearchUtil()
            if cls._model_client is None:
                cls._model_client = ModelFactory().create_client()
        return cls._milvus_client, cls._es_client, cls._model_client

    @classmethod
    def _convert_milvus_result_to_retriever_result(cls, milvus_result: Dict) -> RetrieverResult:
        """
        将 Milvus 的结果转换为 RetrieverResult 格式。
        :param milvus_result: Milvus 返回的结果
        :param name: 集合名称或索引名称
        :return: RetrieverResult 格式的字典
        """
        # 提取 metadata，排除 text 字段
        metadata = milvus_result.get("entity", {})
        text = milvus_result.get("entity", {}).get("text")
        if "text" in metadata:
            del metadata["text"]  # 删除 text 字段
        return RetrieverResult(
            source="milvus",
            name=milvus_result.get("collection_name", "Unknown"),
            id=milvus_result.get("id", ""),
            score=milvus_result.get("distance", ""),
            metadata=metadata,
            text=text,
            vector=milvus_result.get("vector", None)
        )

    @classmethod
    def _convert_es_result_to_retriever_result(cls, es_result: Dict) -> RetrieverResult:
        """
        将 Elasticsearch 的结果转换为 RetrieverResult 格式。
        :param es_result: Elasticsearch 返回的结果
        :param name: 集合名称或索引名称
        :return: RetrieverResult 格式的字典
        """
        return RetrieverResult(
            source="es",
            name=es_result.get("index_name", "Unknown"),
            id=es_result.get("id", ""),
            score=es_result.get("score", ""),
            metadata=es_result.get("document", {}).get("metadata", {}),
            text=es_result.get("document", {}).get("text", ""),
        )

    @classmethod
    async def retrieve(
            cls,
            query: str,
            mode: str = "both",  # 检索模式：'milvus', 'es', 'both'
            milvus_collection_names: Optional[List[str]] = None,
            milvus_fields: List[str] = None,
            milvus_expr: str = None,
            milvus_search_params: str = None,
            es_index_names: Optional[List[str]] = None,
            es_fields: List[str] = None,
            es_query: Union[str, Dict] = None,
            top_k: int = 5,
    ) -> List[RetrieverResult]:
        """
        检索服务，支持通过 Milvus 和 Elasticsearch 进行检索。
        :param query: 查询内容。
        :param mode: 检索模式，可选值为 'milvus'、'es' 或 'both'。
        :param milvus_collection_names: Milvus 集合名称列表。
        :param milvus_fields: Milvus 返回的字段列表。
        :param milvus_expr: Milvus条件过滤式
        :param milvus_search_params 索引查询参数
        :param es_index_names: Elasticsearch 索引名称列表。
        :param es_fields: Elasticsearch 返回的字段列表。
        :param es_query: Elasticsearch 查询内容，可以是字符串或字典。
        :param top_k: 返回的最相似结果数量，默认为 5。
        :return: 检索结果字典。
        """

        # 复用客户端
        milvus_client, es_client, model_client = cls._get_clients()

        # 并行执行
        tasks = []
        # 检索模式：仅使用 Milvus
        if mode in ["milvus", "both"]:
            tasks.append(cls._milvus_search(milvus_client, milvus_collection_names, query, top_k, milvus_fields, milvus_expr, milvus_search_params, model_client))
        # 检索模式：仅使用 Elasticsearch
        if mode in ["es", "both"]:
            tasks.append(cls._es_search(es_client, es_index_names, query, top_k, es_fields, es_query))

        # 合并结果
        results = []
        for completed_task in asyncio.as_completed(tasks):
            results.extend(await completed_task)

        # 返回检索结果
        return results

    @classmethod
    async def _milvus_search(cls, milvus_client, milvus_collection_names, query, top_k, milvus_fields, milvus_expr, milvus_search_params, model_client):
        if not milvus_collection_names:
            logger_util.error("未指定 Milvus 集合名称列表")
            raise ValueError("未指定 Milvus 集合名称列表")

        # 获取查询向量
        query_vector = model_client.get_embeddings(query).data[0].embedding

        # 在 Milvus 中进行向量检索
        try:
            milvus_results = milvus_client.search_vectors(  # 自动PCA
                query_vectors=query_vector,
                collection_names=milvus_collection_names,
                top_k=top_k,
                output_fields=milvus_fields,
                expr=milvus_expr,
                search_params=milvus_search_params
            )  # List[Dict]
            # 转换 milvus_results 为统一检索数据结构
            return [cls._convert_milvus_result_to_retriever_result(milvus_result) for milvus_result in milvus_results]
        except Exception as e:
            logger_util.error(f"Milvus 检索失败: {e}")

    @classmethod
    async def _es_search(cls, es_client, es_index_names, query, top_k, es_fields, es_query):
        if not es_index_names:
            logger_util.error("未指定 Elasticsearch 索引名称")
            raise ValueError("未指定 Elasticsearch 索引名称")

        # 构建 Elasticsearch 查询
        if es_query is None:
            es_query = query  # 默认使用简单字符串查询

        try:
            es_results = es_client.search_documents(
                index_names=es_index_names,
                query=es_query,
                size=top_k,
                fields=es_fields,
            )  # List[Dict]
            # 转换 es_results 为统一检索数据结构
            return [cls._convert_es_result_to_retriever_result(es_result) for es_result in es_results]
        except Exception as e:
            logger_util.error(f"Elasticsearch 检索失败: {e}")
    @classmethod
    async def rerank_retrieve(cls):
        # TODO 检索重排序
        pass


async def main():
    # 考虑多个collection
    retrieve_resp = await RetrieverService.retrieve("卡萨帝热水器",
                                                    milvus_collection_names=[
                                                        "c_awsome_08912d305d254ddb9c5244acfaa0116b"],
                                                    milvus_fields=['text', 'title', 'source'],
                                                    es_index_names=["i_awsome_d97cc39f627e488d9f58b166c142a5e1"],
                                                    es_fields=['text', 'metadata.title', 'metadata.source']
                                                    )
    # RetrieverResult
    # 用于表示召回结果的通用类。
    # :param source: 来源（"es" 或 "milvus"）
    # :param name: 集合名称 | 索引名称
    # :param id: 文档 ID | 集合 ID
    # :param score: 相似度分数或相关性分数
    # :param metadata: 元数据（字典形式）
    # :param text: 文本内容
    # :param vector: 向量（仅 Milvus 有，可选）
    for retrieve_result in retrieve_resp:
        print(retrieve_result.metadata)
        print(retrieve_result.to_dict())


if __name__ == '__main__':
    asyncio.run(main())
