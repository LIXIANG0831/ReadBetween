from fastapi import HTTPException, APIRouter
from redis import Redis

from awsome.core.context import session_getter
from sqlalchemy import text

from awsome.settings import get_config

router = APIRouter(tags=["健康检查"])
@router.get("/health", summary="检查应用运行状态")
async def health_check():
    """
    检查数据库连接
    """
    try:
        with session_getter() as session:
            session.exec(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database connection failed") from e

    """
    检查 Redis 连接
    """
    try:
        redis_uri = get_config("storage.redis.uri")
        redis_client = Redis.from_url(redis_uri)

        # 尝试执行 PING 命令
        if not redis_client.ping():
            raise Exception("Redis connection failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Redis connection failed") from e

    return {"status": "healthy"}
