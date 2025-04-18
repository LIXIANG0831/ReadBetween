from typing import TYPE_CHECKING
from readbetween.settings import get_config
from readbetween.utils.logger_util import logger_util
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


class DatabaseClient:
    """数据库服务类，用于管理数据库连接和操作。"""

    # 类级别引擎，只创建一次
    engine: 'Engine' = None
    async_engine: 'AsyncEngine' = None

    def __init__(self, database_url: str):
        """初始化数据库服务。

        Args:
            database_url (str): 数据库连接字符串。
        """
        self.database_url = database_url
        self.async_database_url = self.database_url.replace("pymysql","aiomysql")  # 支持异步的数据库链接

        # 检查类级别引擎是否已创建，如果未创建则创建
        if DatabaseClient.engine is None:
            DatabaseClient.engine = self._create_class_engine(self.database_url)
            logger_util.debug("创建类级别同步数据库引擎")  # 记录引擎创建

        if DatabaseClient.async_engine is None:
            DatabaseClient.async_engine = self._create_class_async_engine(self.async_database_url)
            logger_util.debug("创建类级别异步数据库引擎")  # 记录异步引擎创建


    @classmethod
    def _create_class_engine(cls, database_url: str) -> 'Engine':
        """创建类级别的数据库引擎 (同步)。

        Returns:
            Engine: 数据库引擎实例。
        """
        if database_url and database_url.startswith('sqlite'):
            # 对于 SQLite 数据库，设置连接参数以允许多线程访问
            connect_args = {'check_same_thread': False}
        else:
            connect_args = {}
        # 创建数据库引擎
        return create_engine(database_url, connect_args=connect_args, pool_size=100, max_overflow=20, pool_pre_ping=True)

    @classmethod
    def _create_class_async_engine(cls, async_database_url: str) -> 'AsyncEngine':
        """创建类级别的异步数据库引擎。

        Returns:
            AsyncEngine: 异步数据库引擎实例。
        """
        # 创建异步数据库引擎, echo=True 可以在控制台输出SQL语句
        return create_async_engine(async_database_url, echo=False) # 生产环境建议关闭 echo=False

    def __enter__(self):
        """进入上下文时创建数据库会话。

        Returns:
            Session: 数据库会话实例。
        """
        self._session = Session(DatabaseClient.engine) # 使用类级别引擎
        return self._session

    def __exit__(self, exc_type, exc_value, traceback):
        """退出上下文时处理会话的提交或回滚。

        Args:
            exc_type: 异常类型。
            exc_value: 异常值。
            traceback: 异常回溯。
        """
        if exc_type is not None:  # 如果发生了异常
            logger_util.error(f'Session rollback because of exception: {exc_type.__name__} {exc_value}')
            self._session.rollback()  # 回滚事务
        else:
            self._session.commit()  # 提交事务
        self._session.close()  # 关闭会话

    def get_session(self):
        """获取数据库会话。

        Yields:
            Session: 数据库会话实例。
        """
        with Session(DatabaseClient.engine) as session:  # 使用类级别引擎
            yield session

    def create_db_and_tables(self):
        """创建数据库和表。"""
        logger_util.debug('检查并创建数据表')

        # 遍历所有表并尝试创建
        for table in SQLModel.metadata.sorted_tables:
            logger_util.debug(f'检查 {table} 中...')
            try:
                table.create(DatabaseClient.engine, checkfirst=True)  # 使用类级别引擎创建表，如果已存在则跳过
            except OperationalError as oe:
                logger_util.warning(f'Table {table} already exists, skipping. Exception: {oe}')  # 表已存在的警告
            except Exception as exc:
                logger_util.error(f'建表异常 {table}: {exc}')  # 记录创建表时的错误
                raise RuntimeError(f'建表异常 {table}') from exc  # 抛出运行时异常

        logger_util.debug('创建数据库表成功')  # 记录成功创建数据库和表的信息


database_url = get_config("storage.mysql.uri")
database_client: 'DatabaseClient' = DatabaseClient(database_url)