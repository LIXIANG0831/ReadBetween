from readbetween.models.dao.model_available_cfg import ModelAvailableCfgDao, ModelAvailableCfg
from readbetween.services.base import BaseService


class ModelAvailableCfgService(BaseService):
    @classmethod
    def add_model_available_cfg(cls, model_available_cfg_add):
        model_available_cfg_add = ModelAvailableCfg(**model_available_cfg_add.dict())
        return ModelAvailableCfgDao.insert(model_available_cfg_add)

    @classmethod
    async def delete_model_available_cfg(cls, id):
        from readbetween.models.dao.conversation import ConversationDao
        from readbetween.models.dao.knowledge import KnowledgeDao
        # 删除关联该模型的会话
        await ConversationDao.delete_by_available_id(id)
        # 删除关联该模型的知识库
        await KnowledgeDao.delete_by_available_id(id)
        return await ModelAvailableCfgDao.delete_by_id(id)

    @classmethod
    def get_model_available_cfg_list(cls):
        return ModelAvailableCfgDao.select_all()