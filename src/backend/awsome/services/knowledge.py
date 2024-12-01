from awsome.models.v1.knowledge import KnowledgeCreate, KnowledgeUpdate
from awsome.services.base import BaseService
from awsome.models.dao.knowledge import KnowledgeDao
from awsome.utils.milvus_util import milvus_client
from awsome.services.constant import milvus_default_index_params, milvus_default_fields
from fastapi import HTTPException
import uuid


class KnowledgeService(BaseService):

    @classmethod
    def create_knowledge(cls, knowledge_create: KnowledgeCreate):
        # TODO 同时创建Milvus-Collection
        new_milvus_collection_name = f"c_awsome_{uuid.uuid4().hex}"
        new_elastic_index_name = f"i_awsome_{uuid.uuid4().hex}"
        try:
            # 创建MilvusCollection
            milvus_client.create_collection(new_milvus_collection_name,  # 集合名
                                            milvus_default_fields)  # 属性
            # 创建MilvusIndex
            milvus_client.create_index(new_milvus_collection_name,  # 集合名
                                       "vector",  # 创建索引的属性
                                       milvus_default_index_params)  # 索引参数
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"创建Milvus集合异常: {str(e)}")
        knowledge_create.collection_name = new_milvus_collection_name  # 数据表记录Milvus-CollectionName
        # TODO 同时创建ES索引
        try:



            pass
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"创建ElasticSearch索引异常: {str(e)}")
        knowledge_create.index_name = new_elastic_index_name  # 数据表记录ES-IndexName
        return KnowledgeDao.insert(knowledge_create.name,
                                   knowledge_create.desc,
                                   knowledge_create.model,
                                   knowledge_create.collection_name,
                                   knowledge_create.index_name,
                                   knowledge_create.enable_layout)

    @classmethod
    def delete_knowledge(cls, id):
        try:
            drop_knowledge = KnowledgeDao.select(id)
            drop_collection_name = drop_knowledge.collection_name
            milvus_client.drop_collection(drop_collection_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除Milvus集合异常: {str(e)}")
        KnowledgeDao.delete_by_id(id)
        return True

    @classmethod
    def update_knowledge(cls, knowledge_update: KnowledgeUpdate):
        return KnowledgeDao.update(knowledge_update.id,
                                   knowledge_update.name,
                                   knowledge_update.desc)

    @classmethod
    def list_knowledge_by_page(cls, page, size):
        return KnowledgeDao.select(page=page, page_size=size)

    @classmethod
    def get_knowledge_by_id(cls, id):
        return KnowledgeDao.select(id)
