from elasticsearch_dsl import Document, Date, Integer, Text, Keyword, connections, Long, Index, Search, analyzer, \
    token_filter, tokenizer, Nested
from awsome.settings import get_config
from awsome.utils.logger_util import logger_util
from awsome.models.schemas.es.base import BaseDocument


class ElasticSearchUtil:
    def __init__(self, es_hosts=None, es_timeout=None, es_http_auth=None):
        """
        初始化 Elasticsearch 连接。
        :param es_hosts: Elasticsearch 主机列表，默认从配置文件中获取。
        :param es_timeout: 连接超时时间，默认从配置文件中获取。
        :param es_http_auth: HTTP 认证信息，默认从配置文件中获取。
        """
        # 如果未传入参数，则从配置文件中获取默认值
        es_hosts = es_hosts or get_config("storage.es.hosts")
        es_timeout = es_timeout or get_config("storage.es.timeout")
        es_http_auth = es_http_auth or get_config("storage.es.http_auth")

        # 连接到 Elasticsearch
        try:
            connections.create_connection(
                hosts=es_hosts,  # 指定主机和端口
                timeout=es_timeout,  # 超时时间
                http_auth=es_http_auth  # 校验
            )
            logger_util.info("Elasticsearch连接已建立。")
        except Exception as e:
            logger_util.error(f"Elasticsearch连接失败: {e}")
            raise Exception(f"Elasticsearch连接失败: {e}")

    def save_document(self, save_document: BaseDocument):
        """
        将文档保存到 Elasticsearch 索引中。
        :param save_document: 要保存的文档对象。
        """
        try:
            save_document.save()
        except Exception as e:
            logger_util.error(f"保存文档失败: {e}")
            raise Exception(f"保存文档失败: {e}")

    def delete_index(self, index_name):
        """
        删除指定的 Elasticsearch 索引。
        :param index_name: 要删除的索引名称。
        """
        try:
            # 检查索引是否存在
            if Index(index_name).exists():
                # 删除索引
                Index(index_name).delete()
                logger_util.info(f"索引 {index_name} 已删除。")
            else:
                logger_util.warning(f"索引 {index_name} 不存在，无需删除。")
        except Exception as e:
            logger_util.error(f"删除索引 {index_name} 时发生错误: {e}")
            raise Exception(f"删除索引 {index_name} 时发生错误: {e}")

    def search_documents(self, index_names, query, size=10, fields=None):
        """
        在指定的索引中搜索文档，并支持返回字段过滤。
        :param index_names: 索引名称列表，支持从多个索引中检索。
        :param query: 查询内容，可以是简单的字符串或复杂的查询字典。
        :param size: 返回结果的数量，默认为10。
        :param fields: 返回字段过滤，可以是一个字段列表或排除字段字典。
        :return: 查询结果列表。
        """
        try:
            # 创建搜索对象
            s = Search(index=index_names)

            # 构建查询
            if isinstance(query, str):
                # 如果查询是字符串，使用 multi_match 查询在所有字段中搜索
                s = s.query("multi_match", query=query, fields="*")
            elif isinstance(query, dict):
                # 如果查询是字典，直接使用 raw DSL
                s = s.update_from_dict(query)
            else:
                raise ValueError("查询内容必须是字符串或字典类型")

            # 设置返回结果数量
            s = s[0:size]

            # 设置字段过滤
            if fields:
                if isinstance(fields, list):
                    # 包含指定字段
                    s = s.source(fields)
                elif isinstance(fields, dict) and "excludes" in fields:
                    # 排除指定字段
                    s = s.source({"excludes": fields["excludes"]})

            # 执行查询
            response = s.execute()

            # 提取结果
            results = [hit.to_dict() for hit in response.hits]
            logger_util.info(f"查询成功，返回结果数量: {len(results)}")
            return results
        except Exception as e:
            logger_util.error(f"在索引 {index_name} 中搜索文档时发生错误: {e}")
            raise Exception(f"在索引 {index_name} 中搜索文档时发生错误: {e}")

    def delete_documents(self, index_name, query):
        """
        根据查询条件删除指定索引中的文档。
        :param index_name: 索引名称。
        :param query: 查询条件，用于指定要删除的文档。
        :return: 删除结果。
        """
        try:
            # 创建删除查询对象
            s = Search(index=index_name)
            s = s.query(query)

            # 执行删除操作
            response = s.delete()

            # 提取删除结果
            deleted_count = response["deleted"]
            logger_util.info(f"成功删除 {deleted_count} 条文档。")
            return {"deleted_count": deleted_count}
        except Exception as e:
            logger_util.error(f"在索引 {index_name} 中删除文档时发生错误: {e}")
            raise Exception(f"在索引 {index_name} 中删除文档时发生错误: {e}")

    def check_connection(self):
        """
        检查 Elasticsearch 连接是否正常。
        """
        try:
            # 使用 ping 方法检查连接
            if connections.get_connection().ping():
                logger_util.info("Elasticsearch连接正常！")
            else:
                logger_util.error("Elasticsearch连接失败！")
        except Exception as e:
            logger_util.error(f"连接时发生错误: {e}")


if __name__ == '__main__':
    es_util = ElasticSearchUtil()
    query_dict = {  # match 查询必须嵌套在 query 字段下
        "query": {
            "match": {
                "text": "热水器"
            }
        }
    }
    results_1 = es_util.search_documents(
        index_names=["i_awsome_fba56f730a124d5895db003677734978"],
        query=query_dict,
        size=5,
        fields=["metadata.title", "text"]  # 只返回title text
    )
    print(results_1)

    query_str = "热水器"
    results_2 = es_util.search_documents(
        index_names=["i_awsome_fba56f730a124d5895db003677734978"],
        query=query_str,
        size=5,
        fields={"excludes": ["metadata"]}  # 只返回 text
    )
    print(results_2)