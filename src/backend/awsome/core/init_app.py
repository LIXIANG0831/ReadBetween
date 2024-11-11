from awsome.services.redis_client import redis_client
from awsome.services.database_client import database_client
from awsome.utils.logger_client import logger_client


def init_database():
    """初始化数据库"""
    if redis_client.setNX('init_database', '1'):
        try:
            database_client.create_db_and_tables()
        except Exception as e:
            logger_client.error(e)
            raise RuntimeError('创建数据库和表错误') from e
        finally:
            redis_client.delete('init_database')
