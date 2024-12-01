import uuid
from typing import Optional
from awsome.models.dao.base import AwsomeDBModel
from sqlalchemy import Column, String, INT
from sqlmodel import Field, DateTime, text
from awsome.utils.context import session_getter
from awsome.utils.logger_util import logger_util
from datetime import datetime
from fastapi import HTTPException


class KnowledgeFileBase(AwsomeDBModel):
    __tablename__ = "knowledge_file"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True, description="主键ID")
    kb_id: str = Field(sa_column=Column(String(255), index=True, nullable=False), description="知识库ID")
    name: Optional[str] = Field(sa_column=Column(String(255), index=True, nullable=False), description="文件名")
    md5: Optional[str] = Field(sa_column=Column(String(255), nullable=False), description="文件md5")
    object_name: Optional[str] = Field(sa_column=Column(String(255), nullable=False), description="MinIO Object Name")
    status: int = Field(default=0, sa_column=Column(INT, nullable=False), description="是否完成向量化, 0/1/-1/未完成/完成/异常失败")
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
    def batch_insert(cls, file_insert_list):
        with session_getter() as session:
            session.add_all(file_insert_list)
            session.commit()
            for file in file_insert_list:  # 刷新得到主键ID
                session.refresh(file)
            return file_insert_list

    @classmethod
    def select_by_kb_id(cls, kb_id: str, page: int = None, size: int = None):
        with session_getter() as session:
            query = session.query(KnowledgeFile).where(KnowledgeFile.kb_id == kb_id, KnowledgeFile.delete == 0)
            if page is not None and size is not None:
                offset = (page - 1) * size
                all_knowledge_files = query.offset(offset).limit(size).all()
            else:
                all_knowledge_files = query.all()
            return all_knowledge_files
    @classmethod
    def delete_by_kb_id(cls):
        pass

    @classmethod
    def delete_by_id(cls):
        pass
