from elasticsearch_dsl import Document, Date, Integer, Text, Keyword, connections, Long, Index, Search, analyzer, \
    token_filter, tokenizer, Nested
from awsome.settings import get_config
from awsome.utils.logger_util import logger_util

es_hosts = get_config("storage.es.hosts")
es_timeout = get_config("storage.es.timeout")
es_http_auth = get_config("storage.es.http_auth")

# 连接到 Elasticsearch，指定端口和协议
connections.create_connection(
    hosts=es_hosts,  # 指定主机和端口
    timeout=es_timeout,  # 超时时间
    http_auth=es_http_auth  # 校验
)


class ElasticSearchClient:
    @staticmethod
    async def insert_doc_to_index():
        pass

    @staticmethod
    def delete_index(index_name):
        pass

    @staticmethod
    def search_doc_from_index():
        pass

    @staticmethod
    def delete_doc_from_index():
        pass
