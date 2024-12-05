from elasticsearch_dsl import Document, Text, Keyword, Long, Index, analyzer, \
    token_filter, tokenizer, Nested


# 元数据基类
class Metadata(Document):
    bbox = Text(fields={'keyword': Keyword(ignore_above=256)})
    chunk_index = Long()
    extra = Text(analyzer='ik_max_word', fields={'keyword': Keyword(ignore_above=256)})
    file_id = Text(fields={'keyword': Keyword(ignore_above=256)})
    knowledge_id = Text(fields={'keyword': Keyword(ignore_above=256)})
    start_page = Long()
    source = Text(analyzer='ik_max_word', fields={'keyword': Keyword(ignore_above=256)})
    title = Text(analyzer='ik_max_word', fields={'keyword': Keyword(ignore_above=256)})

    def __init__(self, **kwargs):
        super(Metadata, self).__init__(**kwargs)
        self.bbox = kwargs.get('bbox', '')
        self.chunk_index = kwargs.get('chunk_index', 0)
        self.extra = kwargs.get('extra', '')
        self.file_id = kwargs.get('file_id', 0)
        self.knowledge_id = kwargs.get('knowledge_id', '')
        self.start_page = kwargs.get('start_page', 0)
        self.source = kwargs.get('source', '')
        self.title = kwargs.get('title', '')


# 文档基类
class BaseDocument(Document):
    # 定义字段
    metadata = Nested(Metadata)
    text = Text(analyzer='ik_max_word')  # 使用 ik_max_word 中文分词器

    # 指定IK分词器
    class DocType:
        analyzer = analyzer(
            'ik_max_word',
            tokenizer=tokenizer('ik_max_word'),
            filter=[token_filter('ik_max_word')]
        )

    class Index:
        name = 'default_index_name'  # 默认索引名称

    def __init__(self, **kwargs):
        super(BaseDocument, self).__init__(**kwargs)
        self.metadata = kwargs.get('metadata', Metadata())
        self.text = kwargs.get('text', '')

    def save(self, **kwargs):  # 保存文档之前设置_index属性
        if hasattr(self, 'index_name'):
            self._index = Index(self.index_name)
        super(BaseDocument, self).save(**kwargs)
