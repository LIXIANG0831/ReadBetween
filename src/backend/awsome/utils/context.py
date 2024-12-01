from contextlib import contextmanager
from sqlmodel import Session
from awsome.utils.database_client import database_client
from awsome.utils.logger_util import logger_util


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
