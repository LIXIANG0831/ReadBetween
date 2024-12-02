from awsome.models.v1.model_cfg import ModelCfgCreate
from awsome.services.base import BaseService
from awsome.models.dao.model_cfg import ModelCfgDao
from awsome.models.dao.model_cfg import ModelCfg


class ModelCfgService(BaseService):

    @classmethod
    def create_model_cfg(cls, model_cfg_create: ModelCfgCreate):
        model_cfg = ModelCfg(**model_cfg_create.dict())
        return ModelCfgDao.insert(model_cfg)

    @classmethod
    def delete_model_cfg(cls, id):
        return ModelCfgDao.delete_by_id(id)

    @classmethod
    def get_model_cfg(cls):
        return ModelCfgDao.select_all()
