from typing import List

from awsome.models.dao.model_provider_cfg import ModelProviderCfg
from awsome.services.model_provider_cfg import ModelProviderCfgService
from awsome.utils.redis_util import RedisUtil
from awsome.utils.database_client import database_client
from awsome.settings import get_config
from awsome.utils.logger_util import logger_util

redis_client = RedisUtil()

def init_database():
    """初始化数据库"""
    if redis_client.setNX('init_database', '1'):
        try:
            database_client.create_db_and_tables()

            """获取配置文件模型供应商, 写入初始库"""
            default_model_provider_cfg: List[dict] = get_config("system.default_model_provider")
            default_model_provider = []
            for model_provider in default_model_provider_cfg:
                for provider, mark in model_provider.items():
                    default_model_provider.append(ModelProviderCfg(provider=provider, mark=mark))
            ModelProviderCfgService.batch_insert_provider(default_model_provider)

        except Exception as e:
            logger_util.error(e)
            raise RuntimeError('创建数据库和表错误') from e
        finally:
            redis_client.delete('init_database')
