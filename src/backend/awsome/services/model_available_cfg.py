from awsome.models.dao.model_available_cfg import ModelAvailableCfgDao, ModelAvailableCfg
from awsome.services.base import BaseService


class ModelAvailableCfgService(BaseService):
    @classmethod
    def add_model_available_cfg(cls, model_available_cfg_add):
        model_available_cfg_add = ModelAvailableCfg(**model_available_cfg_add.dict())
        return ModelAvailableCfgDao.insert(model_available_cfg_add)

    @classmethod
    def delete_model_available_cfg(cls, id):
        return ModelAvailableCfgDao.delete_by_id(id)

    @classmethod
    def get_model_available_cfg_list(cls):
        return ModelAvailableCfgDao.select_all()