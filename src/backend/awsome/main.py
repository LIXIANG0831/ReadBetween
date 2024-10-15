from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from contextlib import asynccontextmanager
from settings import get_config
from core.init_app import init_database


@asynccontextmanager
async def _LIFESPAN(app: FastAPI):
    init_database()
    yield  # yield 前为程序启动前 后为程序关闭后


_EXCEPTION_HANDLERS = {

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

    from api.router import v1_router
    app.include_router(v1_router)

    return app


app = create_app()

if __name__ == '__main__':
    import uvicorn

    port = get_config("app.port")  # 运行端口
    uvicorn.run(app, host='0.0.0.0', port=port, workers=1)
