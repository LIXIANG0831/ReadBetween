from typing import List
from readbetween.utils.local_embedding_manager import LocalEmbedManager
from readbetween.models.dao.model_provider_cfg import ModelProviderCfg
from readbetween.services.model_provider_cfg import ModelProviderCfgService
from readbetween.utils.redis_util import RedisUtil
from readbetween.utils.database_client import DatabaseClient
from readbetween.utils.logger_util import logger_util
from readbetween.config import settings
from readbetween.services.constant import MODEL_SAVE_PATH, SYSTEM_EMBEDDING_NAME, SYSTEM_MODEL_PROVIDER


def init_database():
    database_client = DatabaseClient(settings.storage.mysql.uri)
    redis_client = RedisUtil(settings.storage.redis.uri)
    """初始化数据库"""
    if redis_client.setNX('init_database', '1'):
        try:
            database_client.create_db_and_tables()

            """获取配置文件模型供应商, 写入初始库"""
            default_model_provider_cfg: List[dict] = SYSTEM_MODEL_PROVIDER
            default_model_provider = []
            for model_provider in default_model_provider_cfg:  # 获取系统设置的供应商
                for provider, mark in model_provider.items():
                    logger_util.debug(f"初始化模型供应商:{provider=}|{mark=}")
                    default_model_provider.append(ModelProviderCfg(provider=provider, mark=mark))
            for model_provider in default_model_provider:  # 检查供应商是否已存在
                if ModelProviderCfgService.search_provider(model_provider) is False:  # 供应商已存在
                    logger_util.debug(f"模型供应商:{model_provider.provider}已存在")
                    continue
                ModelProviderCfgService.insert_provider(model_provider)

        except Exception as e:
            logger_util.error(e)
            raise RuntimeError('创建数据库和表错误') from e
        finally:
            redis_client.delete('init_database')


def init_embed_model():
    embedding_model = SYSTEM_EMBEDDING_NAME
    model_dir = MODEL_SAVE_PATH

    lem = LocalEmbedManager()
    lem.initialize(
        model_name=embedding_model,
        model_dir=model_dir
    )
