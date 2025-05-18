from fastapi import APIRouter
from readbetween.api.health import router as health_router
from readbetween.api.v1.chat import router as chat_router
from readbetween.api.v1.knowledge import router as knowledge_router
from readbetween.api.v1.knowledge_file import router as knowledge_file_router
from readbetween.api.v1.model_setting_cfg import router as model_setting_cfg_router
from readbetween.api.v1.model_available_cfg import router as model_available_cfg_router
from readbetween.api.v1.voice import router as voice_router
from readbetween.api.v1.memory import router as memory_router
from readbetween.api.v1.mcp import router as mcp_router


# v1 路由
v1_router = APIRouter(prefix='/api/v1')
v1_router.include_router(chat_router)
v1_router.include_router(knowledge_router)
v1_router.include_router(knowledge_file_router)
v1_router.include_router(voice_router)
v1_router.include_router(memory_router)
v1_router.include_router(mcp_router)

# sys 路由
sys_router = APIRouter(prefix='/sys')
sys_router.include_router(model_setting_cfg_router)
sys_router.include_router(model_available_cfg_router)
sys_router.include_router(health_router)

# 根路由
root_router = APIRouter(prefix='')
root_router.include_router(v1_router)
root_router.include_router(sys_router)