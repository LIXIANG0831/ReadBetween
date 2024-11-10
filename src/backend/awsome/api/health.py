from fastapi import HTTPException, APIRouter
from awsome.utils.context import session_getter
from sqlalchemy import text

router = APIRouter(tags=["健康检查"])
@router.get("/health", summary="检查应用运行状态")
async def health_check():
    try:
        with session_getter() as session:
            session.exec(text("SELECT 1"))
            return {"status": "healthy"}
    except Exception:
        raise HTTPException(status_code=500, detail="Database connection failed")