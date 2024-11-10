from fastapi import APIRouter
from awsome.api.health import router as health_router
from awsome.api.v1.chat import router as chat_router

# v1 路由
v1_router = APIRouter(prefix='/api/v1')
v1_router.include_router(chat_router)

# 根路由
root_router = APIRouter(prefix='')
root_router.include_router(health_router)
root_router.include_router(v1_router)