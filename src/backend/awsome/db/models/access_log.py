from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from awsome.db.models.base import AwsomeDBModel
from sqlalchemy import Column, String
from sqlmodel import Field, DateTime, text
from awsome.utils.context import session_getter
from awsome.utils.logger_client import logger_client
from datetime import datetime

class AccessLogBase(AwsomeDBModel):
    __tablename__ = "access_logs"

    id: Optional[int] = Field(default=None, primary_key=True, index=True, description="唯一标识符")
    ip_address: str = Field(..., sa_column=Column(String(255), index=True), description="请求的IP地址")
    request_method: str = Field(..., sa_column=Column(String(255)), description="HTTP请求方法")
    request_path: str = Field(..., sa_column=Column(String(255)), description="请求的路径")
    # 删除标识
    delete: int = Field(index=False, default=0, description="删除标志")
    # 创建时间
    create_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            index=True,
            server_default=text('CURRENT_TIMESTAMP')
        )
    )
    # 修改时间
    update_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP'),
            onupdate=text('CURRENT_TIMESTAMP')
        )
    )

class AccessLog(AccessLogBase, table=True):
    __table_args__ = {"extend_existing": True} # 允许扩展现有的表

class AccessLogDao(AccessLog):
    @classmethod
    def insert(cls, ip_address: str, request_method: str, request_path: str) -> Optional[AccessLog]:
        with session_getter() as session:
            new_access_log = AccessLog(ip_address=ip_address, request_method=request_method, request_path=request_path)
            try:
                session.add(new_access_log)
                session.commit()
                session.refresh(new_access_log)
                logger_client.info(f"Access log added: {new_access_log}")
                return new_access_log
            except SQLAlchemyError as e:
                session.rollback()  # 发生错误时回滚事务
                logger_client.error(f"Error inserting access log: {e}")
                return None