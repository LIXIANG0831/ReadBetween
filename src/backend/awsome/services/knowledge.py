import json

from elasticsearch import Elasticsearch
from awsome.models.v1.knowledge import KnowledgeCreate, KnowledgeUpdate
from awsome.services.base import BaseService
from awsome.models.dao.knowledge import KnowledgeDao
from awsome.utils.elasticsearch_util import ElasticSearchUtil
from awsome.utils.milvus_util import MilvusUtil
from awsome.utils.redis_util import RedisUtil
from awsome.services.constant import milvus_default_index_params, milvus_default_fields_768
from fastapi import HTTPException
import uuid
from awsome.services.constant import redis_default_model_key

# 实例化milvus
milvus_client = MilvusUtil()


# 实例化es
es_client = ElasticSearchUtil()

# 实例化redis
redis_util = RedisUtil()


class KnowledgeService(BaseService):

    @classmethod
    async def create_knowledge(cls, knowledge_create: KnowledgeCreate):
        # TODO 同时创建Milvus-Collection
        new_milvus_collection_name = f"c_awsome_{uuid.uuid4().hex}"
        new_elastic_index_name = f"i_awsome_{uuid.uuid4().hex}"
        # 允许knowledge_create模型为空 为空获取默认模型
        if knowledge_create.model is None or knowledge_create.model == "":
            knowledge_create.model = json.loads(redis_util.get(redis_default_model_key)).get("embedding_name")
        try:
            # 创建MilvusCollection
            milvus_client.create_collection(new_milvus_collection_name,  # 集合名
                                            milvus_default_fields_768)  # 属性
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
                                         knowledge_create.model,
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

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除Milvus集合异常: {str(e)}")
        await KnowledgeDao.delete_by_id(id)
        return True

    @classmethod
    async def update_knowledge(cls, knowledge_update: KnowledgeUpdate):
        return await KnowledgeDao.update(knowledge_update.id,
                                         knowledge_update.name,
                                         knowledge_update.desc)

    @classmethod
    async def list_knowledge_by_page(cls, page, size):
        return await KnowledgeDao.select(page=page, page_size=size)

    @classmethod
    async def get_knowledge_by_id(cls, id):
        return await KnowledgeDao.select(id)
