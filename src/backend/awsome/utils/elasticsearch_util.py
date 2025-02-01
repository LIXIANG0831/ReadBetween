from elasticsearch import Elasticsearch
from elasticsearch_dsl import connections, Document, Search, Index
from elasticsearch_dsl.connections import add_connection
from threading import Lock
from awsome.settings import get_config
from awsome.utils.logger_util import logger_util
from awsome.models.schemas.es.base import BaseDocument


class ElasticSearchUtil:
    _lock = Lock()  # 线程锁，确保线程安全
    _default_client = None  # 默认客户端

    def __init__(self, es_hosts=None, es_timeout=None, es_http_auth=None):
        """
        初始化并配置全局Elasticsearch连接（仅首次实例化生效）
        """
        if not self.__class__._default_client:
            with self._lock:
                if not self.__class__._default_client:
                    self.__class__.initialize_connection(es_hosts, es_timeout, es_http_auth)

    @classmethod
    def initialize_connection(cls, es_hosts=None, es_timeout=None, es_http_auth=None):
        """
        全局连接初始化方法（可独立调用）
        """
        # 获取配置参数
        es_hosts = es_hosts or get_config("storage.es.hosts")
        es_timeout = es_timeout or get_config("storage.es.timeout")
        es_http_auth = es_http_auth or get_config("storage.es.http_auth")

        try:
            # 创建全局连接（默认连接别名）
            client = Elasticsearch(
                hosts=es_hosts,
                timeout=es_timeout,
                http_auth=es_http_auth
            )
            cls._default_client = client
            add_connection(alias='default', conn=client)
            logger_util.info("Elasticsearch全局连接已建立")
        except Exception as e:
            logger_util.error(f"Elasticsearch连接失败: {e}")
            raise ConnectionError(f"Elasticsearch连接失败: {e}")

    @classmethod
    def get_client(cls):
        """
        获取全局Elasticsearch客户端实例
        """
        if not cls._default_client:
            cls.initialize_connection()
        return cls._default_client

    @classmethod
    def save_document(cls, save_document: BaseDocument):
        """
        保存文档到Elasticsearch（使用全局连接）
        """
        try:
            save_document.save(using='default')  # 显式指定使用默认连接
        except Exception as e:
            logger_util.error(f"保存文档失败: {e}")
            raise RuntimeError(f"保存文档失败: {e}")

    @classmethod
    def delete_index(cls, index_name):
        """
        删除指定索引（使用全局连接）
        """
        try:
            index = Index(index_name, using='default')
            if index.exists():
                index.delete()
                logger_util.info(f"索引 {index_name} 已删除")
            else:
                logger_util.warning(f"索引 {index_name} 不存在")
        except Exception as e:
            logger_util.error(f"删除索引失败: {e}")
            raise RuntimeError(f"删除索引失败: {e}")

    @classmethod
    def search_documents(cls, index_names, query, size=10, fields=None):
        """
        使用全局连接执行搜索
        """
        try:
            s = Search(index=index_names, using='default')

            if isinstance(query, str):
                s = s.query("multi_match", query=query, fields="*")
            elif isinstance(query, dict):
                s = s.update_from_dict(query)
            else:
                raise ValueError("查询内容必须是字符串或字典类型")

            s = s[0:size]
            if fields:
                if isinstance(fields, list):
                    s = s.source(fields)
                elif isinstance(fields, dict) and "excludes" in fields:
                    s = s.source({"excludes": fields["excludes"]})

            response = s.execute()
            return [{
                "id": hit.meta.id,
                "score": hit.meta.score,
                "index_name": hit.meta.index,
                "document": hit.to_dict()
            } for hit in response.hits]
        except Exception as e:
            logger_util.error(f"搜索失败: {e}")
            raise RuntimeError(f"搜索失败: {e}")

    @classmethod
    def delete_documents(cls, index_name, query):
        """
        使用全局连接删除文档
        """
        try:
            es = cls.get_client()
            response = es.delete_by_query(
                index=index_name,
                body=query
            )
            deleted_count = response["deleted"]
            logger_util.info(f"删除成功：{deleted_count}条")
            return {"deleted_count": deleted_count}
        except Exception as e:
            logger_util.error(f"删除文档失败: {e}")
            raise RuntimeError(f"删除文档失败: {e}")

    @classmethod
    def check_connection(cls):
        """
        检查全局连接状态
        """
        try:
            es = cls.get_client()
            if es.ping():
                logger_util.info("连接正常")
                return True
            logger_util.error("连接失败")
            return False
        except Exception as e:
            logger_util.error(f"连接检查异常: {e}")
            return False


if __name__ == '__main__':
    # 使用示例
    es_util = ElasticSearchUtil()  # 首次实例化会初始化连接

    # 后续使用方式任选其一：
    # 方式1：通过类方法直接使用
    # query_str = "卡萨帝热水器"
    # results_2 = ElasticSearchUtil.search_documents(
    #     index_names=["i_awsome_f608273522074e55ba210760a00a6e77"],
    #     query=query_str,
    #     size=5,
    #     # fields={"excludes": ["metadata"]}  # 只返回 text
    # )
    # print(results_2)
    delete_query = {
        "query": {
            "term": {
                "metadata.file_id.keyword": {
                    "value": "1529d06c-1109-46ee-b8af-6711a06085b1"
                }
            }
        }
    }
    result = ElasticSearchUtil.delete_documents("i_awsome_f608273522074e55ba210760a00a6e77", delete_query)
    print(result)
