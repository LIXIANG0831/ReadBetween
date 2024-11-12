from awsome.db.v1.knowledge import KnowledgeCreate, KnowledgeUpdate
from awsome.services.base import BaseService
from awsome.db.models.knowledge import KnowledgeDao
class KnowledgeService(BaseService):

    @classmethod
    def create_knowledge(cls, knowledge_create: KnowledgeCreate):
        return KnowledgeDao.insert(knowledge_create.name,
                                   knowledge_create.desc,
                                   knowledge_create.model,
                                   knowledge_create.collection_name,
                                   knowledge_create.index_name,
                                   knowledge_create.enable_layout)

    @classmethod
    def delete_knowledge(cls, id):
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
