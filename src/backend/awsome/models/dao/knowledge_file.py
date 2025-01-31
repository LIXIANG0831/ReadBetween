import uuid
from typing import Optional, List
from awsome.models.dao.base import AwsomeDBModel
from sqlalchemy import Column, String, INT, select, bindparam, Integer
from sqlmodel import Field, DateTime, text
from awsome.core.context import session_getter, async_session_getter
from datetime import datetime

from awsome.utils.logger_util import logger_util


class KnowledgeFileBase(AwsomeDBModel):
    __tablename__ = "knowledge_file"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True, description="主键ID")
    kb_id: str = Field(sa_column=Column(String(255), index=True, nullable=False), description="知识库ID")
    name: Optional[str] = Field(sa_column=Column(String(255), index=True, nullable=False), description="文件名")
    md5: Optional[str] = Field(sa_column=Column(String(255), nullable=False), description="文件md5")
    object_name: Optional[str] = Field(sa_column=Column(String(255), nullable=False), description="MinIO Object Name")
    status: int = Field(default=0, sa_column=Column(INT, nullable=False),
                        description="是否完成向量化, 0/1/-1/未完成/完成/异常失败")
    extra: Optional[str] = Field(sa_column=Column(String(255), nullable=True),
                                 description="为空未开始向量化|不为空为向量化异常信息")
    # 删除标识
    delete: int = Field(default=0, sa_column=Column(Integer, nullable=False), description="删除标志")
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


class KnowledgeFileDao:
    @staticmethod
    def insert():
        pass

    @staticmethod
    def batch_insert(file_insert_list):
        with session_getter() as session:
            session.add_all(file_insert_list)
            session.commit()
            for file in file_insert_list:  # 刷新得到主键ID
                session.refresh(file)
            return file_insert_list

    @staticmethod
    def select_by_kb_id(kb_id: str, page: int = None, size: int = None):
        with session_getter() as session:
            query = session.query(KnowledgeFile).where(KnowledgeFile.kb_id == kb_id, KnowledgeFile.delete == 0).order_by(KnowledgeFile.create_time.desc())
            if page is not None and size is not None:
                offset = (page - 1) * size
                all_knowledge_files = query.offset(offset).limit(size).all()
            else:
                all_knowledge_files = query.all()
            return all_knowledge_files

    @staticmethod
    async def delete_by_kb_id(kb_id: str):
        async with async_session_getter() as session:
            query_stmt = select(KnowledgeFile).where(KnowledgeFile.kb_id == bindparam('kb_id', value=kb_id))
            results = await session.execute(query_stmt)
            delete_files: List[KnowledgeFile] = results.scalars().all()
            # 软删除
            for file in delete_files:
                file.delete = 1
            await session.commit()
            logger_util.info(f"Deleted Knowledge_files with Knowledge_id: {kb_id}")

    @staticmethod
    def delete_by_id():
        pass

    @staticmethod
    def select_by_file_id(file_id: str):
        with session_getter() as session:
            query = session.query(KnowledgeFile).where(KnowledgeFile.id == file_id, KnowledgeFile.delete == 0)
            file_info = query.all()
            return file_info

    @staticmethod
    def update_file(file_info: KnowledgeFile):
        with session_getter() as session:
            # 查询数据库中对应的记录
            file = session.query(KnowledgeFile).filter(KnowledgeFile.id == file_info.id,
                                                       KnowledgeFile.delete == 0).first()
            if file:
                file.status = file_info.status
                file.extra = file_info.extra or None
                session.commit()
                return file
            else:
                raise Exception("记录不存在")
