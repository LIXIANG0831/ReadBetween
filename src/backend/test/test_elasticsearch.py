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

# 元数据基类
class Metadata(Document):
    bbox = Text(fields={'keyword': Keyword(ignore_above=256)})
    chunk_index = Long()
    extra = Text(analyzer='ik_max_word', fields={'keyword': Keyword(ignore_above=256)})
    file_id = Long()
    knowledge_id = Text(fields={'keyword': Keyword(ignore_above=256)})
    page = Long()
    source = Text(analyzer='ik_max_word', fields={'keyword': Keyword(ignore_above=256)})
    title = Text(analyzer='ik_max_word', fields={'keyword': Keyword(ignore_above=256)})


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

    def save(self, **kwargs):  # 保存文档之前设置_index属性
        if hasattr(self, 'index_name'):
            self._index = Index(self.index_name)
        super(BaseDocument, self).save(**kwargs)

# 检查连接状态
def check_connection():
    try:
        # 使用 ping 方法检查连接
        if connections.get_connection().ping():
            logger_util.info("Elasticsearch连接正常！")
        else:
            logger_util.error("Elasticsearch连接失败！")
    except Exception as e:
        logger_util.error(f"连接时发生错误: {e}")


if __name__ == '__main__':
    check_connection()
    # index_name = 'test_index_name'

    poems = [
        {"title": "七律·长征",
         "text": "红军不怕远征难，万水千山只等闲。五岭逶迤腾细浪，乌蒙磅礴走泥丸。金沙水拍云崖暖，大渡桥横铁索寒。更喜岷山千里雪，三军过后尽开颜。"},
        {"title": "念奴娇·昆仑",
         "text": "横空出世，莽昆仑，阅尽人间春色。飞起玉龙三百万，搅得周天寒彻。夏日消溶，江河横溢，人或为鱼鳖。千秋功罪，谁人曾与评说？而今我谓昆仑：不要这高，不要这多雪。安得倚天抽宝剑，把汝裁为三截？一截遗欧，一截赠美，一截还东国。太平世界，环球同此凉热。"},
        {"title": "清平乐·六盘山",
         "text": "天高云淡，望断南飞雁。不到长城非好汉，屈指行程二万。六盘山上高峰，红旗漫卷西风。今日长缨在手，何时缚住苍龙？"},
        {"title": "六言诗·给彭德怀同志", "text": "山高路远坑深，大军纵横驰奔。谁敢横刀立马？唯我彭大将军！"},
        {"title": "沁园春·雪",
         "text": "北国风光，千里冰封，万里雪飘。望长城内外，惟余莽莽；大河上下，顿失滔滔。山舞银蛇，原驰蜡象，欲与天公试比高。须晴日，看红装素裹，分外妖娆。江山如此多娇，引无数英雄竞折腰。惜秦皇汉武，略输文采；唐宗宋祖，稍逊风骚。一代天骄，成吉思汗，只识弯弓射大雕。俱往矣，数风流人物，还看今朝。"},
        {"title": "忆秦娥·娄山关",
         "text": "西风烈，长空雁叫霜晨月。霜晨月，马蹄声碎，喇叭声咽。雄关漫道真如铁，而今迈步从头越。从头越，苍山如海，残阳如血。"},
        {"title": "十六字令三首",
         "text": "山，快马加鞭未下鞍。惊回首，离天三尺三。\n山，倒海翻江卷巨澜。奔腾急，万马战犹酣。\n山，刺破青天锷未残。天欲堕，赖以拄其间。"},
        {"title": "菩萨蛮·黄鹤楼",
         "text": "茫茫九派流中国，沉沉一线穿南北。烟雨莽苍苍，龟蛇锁大江。\n黄鹤知何去？剩有游人处。把酒酹滔滔，心潮逐浪高！"},
        {"title": "西江月·秋收起义",
         "text": "军叫工农革命，旗号镰刀斧头。匡庐一带不停留，要向潇湘直进。\n地主重重压迫，农民个个同仇。秋收时节暮云愁，霹雳一声暴动。"},
        {"title": "卜算子·咏梅",
         "text": "风雨送春归，飞雪迎春到。已是悬崖百丈冰，犹有花枝俏。\n俏也不争春，只把春来报。待到山花烂漫时，她在丛中笑。"}
    ]

    # 插入文档
    # for poem in poems:
    #     doc = BaseDocument()
    #     # doc.index_name = "wcwcnm"  # 设置索引名称
    #     doc.metadata = Metadata(
    #         bbox="some_bbox_value",
    #         chunk_index=1,
    #         extra="some_extra_value",
    #         file_id=123,
    #         knowledge_id="some_knowledge_id_value",
    #         page=1,
    #         source="some_source_value",
    #         title=poem.get('title', '')
    #     ),
    #     doc.text = poem.get('text', '')
    #
    #     doc.save()

    # 检索内容
    s = Search(index='test_index_name').query("match", text="梅花")
    response = s.execute()
    for hit in response.hits:
        print(hit.meta.id) # 文档id
        print(hit.metadata[0].title, "\n", hit.text)  # 打印文档的title和text字段
        print('\n')
