from elasticsearch_dsl import Document, Date, Integer, Text, Keyword, connections, Long, Index, Search, analyzer, \
    token_filter, tokenizer, Nested
from awsome.settings import get_config
from awsome.utils.logger_util import logger_util
from awsome.models.schemas.es.base import BaseDocument

es_hosts = get_config("storage.es.hosts")
es_timeout = get_config("storage.es.timeout")
es_http_auth = get_config("storage.es.http_auth")

# 连接到 Elasticsearch，指定端口和协议
connections.create_connection(
    hosts=es_hosts,  # 指定主机和端口
    timeout=es_timeout,  # 超时时间
    http_auth=es_http_auth  # 校验
)


class ElasticSearchUtil:
    @staticmethod
    def insert_doc_to_index(save_document: BaseDocument):
        try:
            save_document.save()
        except Exception as e:
            logger_util.error(f"ES文档上传失败:{e}")
            raise Exception(f"ES文档上传失败:{e}")

    @staticmethod
    def delete_index(index_name):
        try:
            # 检查索引是否存在
            if Index(index_name).exists():
                # 删除索引
                Index(index_name).delete()
                logger_util.info(f"索引{index_name}已删除。")
            else:
                logger_util.warning(f"索引{index_name}不存在，无需删除。")
        except Exception as e:
            logger_util.error(f"删除索引{index_name}时发生错误: {e}")
            raise Exception(f"删除索引{index_name}时发生错误: {e}")

    @staticmethod
    def search_doc_from_index(index_name):
        pass

    @staticmethod
    def delete_doc_from_index():
        pass

    @staticmethod
    def check_connection():
        try:
            # 使用 ping 方法检查连接
            if connections.get_connection().ping():
                logger_util.info("Elasticsearch连接正常！")
            else:
                logger_util.error("Elasticsearch连接失败！")
        except Exception as e:
            logger_util.error(f"连接时发生错误: {e}")
