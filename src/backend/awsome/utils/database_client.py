from typing import TYPE_CHECKING
from awsome.settings import get_config
from awsome.utils.logger_client import logger_client
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


class DatabaseClient:
    """数据库服务类，用于管理数据库连接和操作。"""

    def __init__(self, database_url: str):
        """初始化数据库服务。

        Args:
            database_url (str): 数据库连接字符串。
        """
        self.database_url = database_url
        self.engine = self._create_engine()

    def _create_engine(self) -> 'Engine':
        """创建数据库引擎。

        Returns:
            Engine: 数据库引擎实例。
        """
        if self.database_url and self.database_url.startswith('sqlite'):
            # 对于 SQLite 数据库，设置连接参数以允许多线程访问
            connect_args = {'check_same_thread': False}
        else:
            connect_args = {}
        # 创建数据库引擎
        return create_engine(self.database_url, connect_args=connect_args, pool_size=100, max_overflow=20, pool_pre_ping=True)

    def __enter__(self):
        """进入上下文时创建数据库会话。

        Returns:
            Session: 数据库会话实例。
        """
        self._session = Session(self.engine)
        return self._session

    def __exit__(self, exc_type, exc_value, traceback):
        """退出上下文时处理会话的提交或回滚。

        Args:
            exc_type: 异常类型。
            exc_value: 异常值。
            traceback: 异常回溯。
        """
        if exc_type is not None:  # 如果发生了异常
            logger_client.error(f'Session rollback because of exception: {exc_type.__name__} {exc_value}')
            self._session.rollback()  # 回滚事务
        else:
            self._session.commit()  # 提交事务
        self._session.close()  # 关闭会话

    def get_session(self):
        """获取数据库会话。

        Yields:
            Session: 数据库会话实例。
        """
        with Session(self.engine) as session:
            yield session

    def create_db_and_tables(self):
        """创建数据库和表。"""
        logger_client.debug('创建数据库和表')

        # 遍历所有表并尝试创建
        for table in SQLModel.metadata.sorted_tables:
            try:
                table.create(self.engine, checkfirst=True)  # 创建表，如果已存在则跳过
            except OperationalError as oe:
                logger_client.warning(f'Table {table} already exists, skipping. Exception: {oe}')  # 表已存在的警告
            except Exception as exc:
                logger_client.error(f'Error creating table {table}: {exc}')  # 记录创建表时的错误
                raise RuntimeError(f'Error creating table {table}') from exc  # 抛出运行时异常

        logger_client.debug('创建数据库和表成功')  # 记录成功创建数据库和表的信息


database_url = get_config("storage.mysql.uri")
database_client: 'DatabaseClient' = DatabaseClient(database_url)