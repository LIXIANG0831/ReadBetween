import json

from readbetween.core.init_app import redis_client
from readbetween.models.dao.model_available_cfg import ModelAvailableCfgDao
from readbetween.models.v1.knowledge import KnowledgeCreate, KnowledgeUpdate, KnowledgeInfo
from readbetween.models.v1.model_available_cfg import ModelAvailableCfgInfo
from readbetween.services.base import BaseService
from readbetween.models.dao.knowledge import KnowledgeDao, Knowledge
from readbetween.utils.elasticsearch_util import ElasticSearchUtil
from readbetween.utils.milvus_util import MilvusUtil
from readbetween.utils.redis_util import RedisUtil
from readbetween.services.constant import milvus_default_index_params, milvus_default_fields_768, milvus_default_fields_1024, \
    PrefixRedisKnowledge, System_Embedding_Name
from fastapi import HTTPException
import uuid
from readbetween.services.constant import redis_default_model_key
from readbetween.models.schemas.response import PageModel

# 实例化milvus
milvus_client = MilvusUtil()

# 实例化redis
redis_util = RedisUtil()

# 实例化es
es_client = ElasticSearchUtil()


class KnowledgeService(BaseService):

    @classmethod
    async def create_knowledge(cls, knowledge_create: KnowledgeCreate):
        # TODO 同时创建Milvus-Collection
        new_milvus_collection_name = f"c_awsome_{uuid.uuid4().hex}"
        new_elastic_index_name = f"i_awsome_{uuid.uuid4().hex}"
        try:
            # 创建MilvusCollection
            milvus_client.create_collection(new_milvus_collection_name,  # 集合名
                                            milvus_default_fields_1024)  # 属性
            # 创建MilvusIndex
            milvus_client.create_index_on_field(new_milvus_collection_name,  # 集合名
                                                "vector",  # 创建索引的属性
                                                milvus_default_index_params)  # 索引参数
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"创建Milvus集合异常: {str(e)}")

        # 数据表记录Milvus-CollectionName
        knowledge_create.collection_name = new_milvus_collection_name

        try:
            # 上传文件时自动创建ES索引
            pass
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"创建ElasticSearch索引异常: {str(e)}")

        # 数据表记录ES-IndexName
        knowledge_create.index_name = new_elastic_index_name

        return await KnowledgeDao.insert(knowledge_create.name,
                                         knowledge_create.desc,
                                         knowledge_create.available_model_id,
                                         knowledge_create.collection_name,
                                         knowledge_create.index_name,
                                         knowledge_create.enable_layout)

    @classmethod
    async def delete_knowledge(cls, id):
        try:
            drop_knowledge = await KnowledgeDao.select(id)

            # 删除MilvusCollection
            drop_collection_name = drop_knowledge.collection_name
            milvus_client.delete_collection(drop_collection_name)

            # ES索引存在 同步删除ES索引
            drop_es_index_name = drop_knowledge.index_name
            es_client.delete_index(drop_es_index_name)

            # 拼接 Redis Key
            know_info_key = f"{PrefixRedisKnowledge}{id}"
            redis_client.delete(know_info_key)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除Milvus集合异常: {str(e)}")
        await KnowledgeDao.delete_by_id(id)
        return True

    @classmethod
    async def update_knowledge(cls, knowledge_update: KnowledgeUpdate):
        # 拼接 Redis Key
        know_info_key = f"{PrefixRedisKnowledge}{knowledge_update.id}"
        redis_client.delete(know_info_key)
        return await KnowledgeDao.update(knowledge_update.id,
                                         knowledge_update.name,
                                         knowledge_update.desc)

    @classmethod
    async def list_knowledge_by_page(cls, page, size):
        total = await KnowledgeDao.cnt_knowledge_total()
        page_data = await KnowledgeDao.select(page=page, page_size=size)
        return PageModel(total=total, data=page_data)

    @classmethod
    async def get_knowledge_by_id(cls, id):
        return await KnowledgeDao.select(id)

    @classmethod
    async def get_knowledge_info(cls, target_kb_id):
        # 拼接 Redis Key
        know_info_key = f"{PrefixRedisKnowledge}{target_kb_id}"
        if redis_client.exists(know_info_key):  # 缓存存在 直接返回
            conv_info_from_redis = json.loads(redis_client.get(know_info_key))
            return KnowledgeInfo(
                knowledge=Knowledge.parse_obj(conv_info_from_redis.get("knowledge", {})),
                model_cfg=ModelAvailableCfgInfo.parse_obj(conv_info_from_redis.get("model_cfg", {}))
            )

        knowledge: Knowledge = await KnowledgeDao.select(target_kb_id)
        if knowledge.available_model_id:
            available, setting, provider = ModelAvailableCfgDao.select_cfg_info_by_id(knowledge.available_model_id)
            knowledge_info = KnowledgeInfo(
                knowledge=knowledge,
                model_cfg=ModelAvailableCfgInfo(
                    type=available.type,
                    name=available.name,
                    api_key=setting.api_key,
                    base_url=setting.base_url,
                    mark=provider.mark
                )
            )
        else:
            knowledge_info = KnowledgeInfo(
                knowledge=knowledge,
                model_cfg=ModelAvailableCfgInfo(
                    type="embedding",
                    name=System_Embedding_Name,
                    api_key="",
                    base_url="",
                    mark="system"
                )
            )
        # 加入缓存 不过期
        redis_util.set(know_info_key, knowledge_info.model_dump_json())

        return knowledge_info
