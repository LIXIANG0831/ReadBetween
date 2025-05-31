from readbetween.services.constant import SYSTEM_EMBEDDING_NAME, MODEL_SAVE_PATH
from readbetween.utils.local_embedding_manager import LocalEmbedManager
from functools import lru_cache
from readbetween.config import Settings
from readbetween.utils.logger_util import logger_util


@lru_cache()
def get_settings() -> Settings:
    logger_util.debug("[LRU_CACHE] 正在加载配置...")  # 仅在第一次调用时打印
    return Settings()


def get_local_embed_manager():
    embedding_model = SYSTEM_EMBEDDING_NAME
    model_dir = MODEL_SAVE_PATH

    lem = LocalEmbedManager()
    lem.initialize(
        model_name=embedding_model,
        model_dir=model_dir
    )

    return lem
