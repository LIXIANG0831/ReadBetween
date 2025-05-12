from contextlib import contextmanager
from contextlib import asynccontextmanager
from sqlmodel import Session
from sqlalchemy.ext.asyncio import AsyncSession
from readbetween.utils.database_client import DatabaseClient
from readbetween.utils.logger_util import logger_util
import aiofiles
from readbetween.config import settings

database_client = DatabaseClient(settings.storage.mysql.uri)


@asynccontextmanager
async def async_session_getter() -> AsyncSession:
    """异步上下文管理器，用于创建和管理异步数据库会话。

    Yields:
        AsyncSession: 异步数据库会话实例。
    """
    session = AsyncSession(database_client.async_engine)
    try:
        yield session
    except Exception as e:
        logger_util.info('Async session rollback because of exception: %s', e)
        await session.rollback()
        raise
    finally:
        await session.close()
        logger_util.info('Async session closed')


@contextmanager
def session_getter() -> Session:
    """轻量级session context"""
    session = Session(database_client.engine)
    try:
        yield session
    except Exception as e:
        logger_util.info('Session rollback because of exception:{}', e)
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def file_open(file_name, mode):
    f = open(file_name, mode)
    try:
        yield f
    finally:
        f.close()


async def async_file_open(file_name, mode='rb'):
    """
    异步打开文件并返回文件对象。

    参数:
        file_name (str): 要打开的文件名称。
        mode (str): 打开文件的模式，默认为 'r'。

    返回:
        aiofiles.File: 打开的文件对象。
    """
    try:
        # 记录日志，尝试打开文件
        logger_util.info(f"尝试以模式 {mode} 打开文件 {file_name}")
        async with aiofiles.open(file_name, mode) as file:
            yield file
    except Exception as e:
        # 记录日志，打开文件失败
        logger_util.error(f"打开文件 {file_name} 失败：{e}")
        raise
    finally:
        # 记录日志，文件已关闭
        logger_util.info(f"文件 {file_name} 已关闭")
