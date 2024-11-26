import uuid
from typing import Optional
from awsome.models.dao.base import AwsomeDBModel
from sqlalchemy import Column, String, INT
from sqlmodel import Field, DateTime, text
from awsome.utils.context import session_getter
from awsome.utils.logger_client import logger_client
from datetime import datetime
from fastapi import HTTPException


class KnowledgeFileBase(AwsomeDBModel):
    __tablename__ = "knowledge_file"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True, description="主键ID")
    kb_id: str = Field(sa_column=Column(String(255), index=True, nullable=False), description="知识库ID")
    name: Optional[str] = Field(sa_column=Column(String(255), index=True, nullable=False), description="文件名")
    md5: Optional[str] = Field(sa_column=Column(String(255), nullable=False), description="文件md5")
    object_name: Optional[str] = Field(sa_column=Column(String(255), nullable=False), description="MinIO Object Name")
    status: int = Field(default=0, sa_column=Column(INT, nullable=False), description="是否完成向量化")
    extra: Optional[str] = Field(sa_column=Column(String(255), nullable=True), description="冗余字段")
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


class KnowledgeFile(KnowledgeFileBase, table=True):
    __table_args__ = {"extend_existing": True}  # 允许扩展现有的表


class KnowledgeFileDao(KnowledgeFile):
    @classmethod
    def insert(cls):
        pass

    @classmethod
    def select_by_kb_id(cls):
        pass

    @classmethod
    def delete_by_kb_id(cls):
        pass

    @classmethod
    def delete_by_id(cls):
        pass
