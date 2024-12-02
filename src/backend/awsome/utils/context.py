from contextlib import contextmanager
from sqlmodel import Session
from awsome.utils.database_client import database_client
from awsome.utils.logger_util import logger_util
import asyncio
import aiofiles


@contextmanager
def session_getter() -> Session:
    """轻量级session context"""
    try:
        session = Session(database_client.engine)
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
