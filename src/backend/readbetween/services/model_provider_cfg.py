from typing import List

from readbetween.services.base import BaseService
from readbetween.models.dao.model_provider_cfg import ModelProviderCfgDao, ModelProviderCfg


class ModelProviderCfgService(BaseService):

    @classmethod
    def batch_insert_provider(cls, model_provider_list: List[ModelProviderCfg]):
        return ModelProviderCfgDao.batch_insert(model_provider_list)

    @classmethod
    def search_provider(cls, model_provider):
        return ModelProviderCfgDao.search(model_provider)

    @classmethod
    def insert_provider(cls, model_provider):
        return ModelProviderCfgDao.insert(model_provider)

    @classmethod
    def select_providers(cls):
        return ModelProviderCfgDao.select_all()
