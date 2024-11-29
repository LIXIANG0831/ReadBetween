from elasticsearch import Elasticsearch
from elasticsearch_dsl import Document, Date, Integer, Text, Keyword, connections, Long, Index
from awsome.settings import get_config
from awsome.utils.logger_client import logger_client


es_hosts = get_config("storage.es.hosts")
es_timeout = get_config("storage.es.timeout")
es_http_auth = get_config("storage.es.http_auth")

# 连接到 Elasticsearch，指定端口和协议
connections.create_connection(
    hosts=es_hosts,  # 指定主机和端口
    timeout=es_timeout,  # 超时时间
    http_auth=es_http_auth  # 校验
)

class Metadata(Document):
    bbox = Text(fields={'keyword': Keyword(ignore_above=256)})
    chunk_index = Long()
    extra = Text(fields={'keyword': Keyword(ignore_above=256)})
    file_id = Long()
    knowledge_id = Text(fields={'keyword': Keyword(ignore_above=256)})
    page = Long()
    source = Text(fields={'keyword': Keyword(ignore_above=256)})
    title = Text(fields={'keyword': Keyword(ignore_above=256)})


class MyDocument(Document):
    # 安装中文分词器
    # elasticsearch-plugin install https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-8.12.0.zip
    text = Text(analyzer='ik_max_word')  # 使用 ik_max_word 中文分词器
    metadata = Metadata()



# 检查连接状态
def check_connection():
    try:
        # 使用 ping 方法检查连接
        if connections.get_connection().ping():
            logger_client.info("Elasticsearch连接正常！")
        else:
            logger_client.error("Elasticsearch连接失败！")
    except Exception as e:
        logger_client.error(f"连接时发生错误: {e}")


def create_index(index_name, index_settings):
    index = Index(index_name)
    index.settings(**index_settings)
    if index.exists():
        index.delete()
    index.create()
    return True




if __name__ == '__main__':
    check_connection()
    index_name = 'test_index_name'
    from awsome.services.constant import es_index_settings

    create_index(index_name, es_index_settings)

    doc = MyDocument(
        meta={'index': index_name},  # 指定索引名称
        metadata=Metadata(
            bbox="some_bbox_value",
            chunk_index=1,
            extra="some_extra_value",
            file_id=123,
            knowledge_id="some_knowledge_id_value",
            page=1,
            source="some_source_value",
            title="some_title_value"
        ),
        text="这是文档的文本内容"
    )

    doc.save()




