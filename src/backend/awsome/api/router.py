from fastapi import APIRouter
from awsome.api.health import router as health_router
from awsome.api.v1.chat import router as chat_router
from awsome.api.v1.knowledge import router as knowledge_router
from awsome.api.v1.knowledge_file import router as knowledge_file_router
from awsome.api.v1.model_cfg import router as model_cfg_router


# v1 路由
v1_router = APIRouter(prefix='/api/v1')
v1_router.include_router(chat_router)
v1_router.include_router(knowledge_router)
v1_router.include_router(knowledge_file_router)

# sys 路由
sys_router = APIRouter(prefix='/sys')
sys_router.include_router(model_cfg_router)
sys_router.include_router(health_router)

# 根路由
root_router = APIRouter(prefix='')
root_router.include_router(v1_router)
root_router.include_router(sys_router)