from typing import List
from readbetween.utils.local_embedding_manager import LocalEmbedManager
from readbetween.models.dao.model_provider_cfg import ModelProviderCfg
from readbetween.services.model_provider_cfg import ModelProviderCfgService
from readbetween.utils.local_tts_manager import LocalTTSManager
from readbetween.utils.redis_util import RedisUtil
from readbetween.utils.database_client import DatabaseClient
from readbetween.utils.logger_util import logger_util
from readbetween.config import settings
from readbetween.services.constant import (MODEL_SAVE_PATH,
                                           BUILT_IN_EMBEDDING_NAME, BUILT_IN_STT_NAME, BUILT_IN_TTS_NAME,
                                           SYSTEM_MODEL_PROVIDER)
from readbetween.utils.thread_pool_executor_util import ThreadPoolExecutorUtil


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


def init_built_in_model():
    model_dir = MODEL_SAVE_PATH
    embedding_model = BUILT_IN_EMBEDDING_NAME
    tts_model = BUILT_IN_TTS_NAME
    stt_model = BUILT_IN_STT_NAME

    # 内置嵌入模型管理器
    lem = LocalEmbedManager()
    # 内置TTS模型管理器
    ltm = LocalTTSManager()
    # 内置STT模型管理器
    lsm = LocalTTSManager()

    # 初始化线程池
    thread_pool = ThreadPoolExecutorUtil(max_workers=3)
    # 提交任务
    thread_pool.submit_task(lem.initialize, model_name=embedding_model, model_dir=model_dir)
    thread_pool.submit_task(ltm.initialize, model_name=tts_model, model_dir=model_dir)
    thread_pool.submit_task(lsm.initialize, model_name=stt_model, model_dir=model_dir)
    thread_pool.wait_for_all()
    # 关闭线程池
    thread_pool.shutdown()

