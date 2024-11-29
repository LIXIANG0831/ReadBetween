from typing import List

from awsome.services.base import BaseService
from awsome.models.dao.model_provider_cfg import ModelProviderCfgDao, ModelProviderCfg


class ModelProviderCfgService(BaseService):

    """
    批量插入模型供应商配置
    """
    @classmethod
    def batch_insert_provider(cls, model_provider_list: List[ModelProviderCfg]):
        return ModelProviderCfgDao.batch_insert(model_provider_list)
