from fastapi import HTTPException, APIRouter, Depends
from redis import Redis
from readbetween.config import Settings
from readbetween.core.dependencies import get_settings
from readbetween.utils.logger_util import logger_util
from readbetween.core.context import session_getter
from sqlalchemy import text

router = APIRouter(tags=["健康检查"])


@router.get("/health", summary="检查应用运行状态")
async def health_check(settings: Settings = Depends(get_settings)):
    """
    检查 MySQL 数据库连接
    """
    try:
        with session_getter() as session:
            session.exec(text("SELECT 1"))
    except Exception as e:
        logger_util.exception(str(e))
        raise HTTPException(status_code=500, detail="Database connection failed") from e

    """
    检查 Redis 连接
    """
    try:
        redis_uri = settings.storage.redis.uri
        redis_client = Redis.from_url(redis_uri)

        # 尝试执行 PING 命令
        if not redis_client.ping():
            raise Exception("Redis connection failed")
    except Exception as e:
        logger_util.exception(str(e))
        raise HTTPException(status_code=500, detail="Redis connection failed") from e

    return {"status": "healthy"}


@router.get("/app_info", summary="应用信息")
async def get_app_info(settings: Settings = Depends(get_settings)):
    """
    获取平台信息
    """
    try:
        all_settings_dict = settings.model_dump()
        return all_settings_dict
    except Exception as e:
        logger_util.exception(str(e))
        raise HTTPException(status_code=500, detail="获取应用信息失败") from e
