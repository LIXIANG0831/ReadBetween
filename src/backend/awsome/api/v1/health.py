from fastapi import FastAPI, HTTPException, APIRouter
from awsome.utils.context import session_getter

router = APIRouter(tags=["健康检查"])
@router.get("/health")
async def health_check():
    try:
        with session_getter() as session:
            session.exec("SELECT 1")
            return {"status": "healthy"}
    except Exception:
        raise HTTPException(status_code=500, detail="Database connection failed")