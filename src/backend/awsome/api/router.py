from fastapi import APIRouter
from awsome.api.v1.health import router as health_router

v1_router = APIRouter(prefix='/api/v1')

# 根路由
root_router = APIRouter(prefix='')
root_router.include_router(health_router)
root_router.include_router(v1_router)