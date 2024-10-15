from contextlib import contextmanager
from sqlmodel import Session
from utils.logger_client import logger_client
from utils.database_client import database_client


@contextmanager
def session_getter() -> Session:
    """轻量级session context"""
    try:
        session = Session(database_client.engine)
        yield session
    except Exception as e:
        logger_client.info('Session rollback because of exception:{}', e)
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