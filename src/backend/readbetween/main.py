from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from contextlib import asynccontextmanager
from core.init_app import init_database, init_built_in_model
from middleware import log_access
import os

from readbetween.utils.mcp_client import mcp_client_manager


@asynccontextmanager
async def _LIFESPAN(app: FastAPI):
    # 初始化数据库
    init_database()
    # 加载本地嵌入模型
    init_built_in_model()

    yield  # yield 前为程序启动前 后为程序关闭后

    # 清理MCP客户端
    await mcp_client_manager.cleanup()



_EXCEPTION_HANDLERS = {
    # 添加自定义异常处理器
}


def create_app():
    """Create the FastAPI app and include the router."""
    app = FastAPI(
        default_response_class=ORJSONResponse,
        exception_handlers=_EXCEPTION_HANDLERS,
        lifespan=_LIFESPAN,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Deprecated 全局记录用户操作
    # app.middleware("http")(log_access)

    from api.router import root_router
    app.include_router(root_router)

    return app


app = create_app()

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv("APP__PORT", 8080)), workers=1)
