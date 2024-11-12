import uuid
from typing import Optional
from awsome.db.models.base import AwsomeDBModel
from sqlalchemy import Column, String, INT
from sqlmodel import Field, DateTime, text
from awsome.utils.context import session_getter
from awsome.utils.logger_client import logger_client
from datetime import datetime
from fastapi import HTTPException


class KnowledgeBase(AwsomeDBModel):
    __tablename__ = "knowledge"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True, description="主键ID")
    name: Optional[str] = Field(..., sa_column=Column(String(255), index=True), description="知识库名称")
    desc: Optional[str] = Field(default=None, sa_column=Column(String(255), index=False), description="知识库描述")
    model: Optional[str] = Field(default=None, sa_column=Column(String(255)), description="向量化模型")
    collection_name: Optional[str] = Field(default=None, sa_column=Column(String(255)), description="Collection 名称")
    index_name: Optional[str] = Field(default=None, sa_column=Column(String(255)), description="Index 名称")
    enable_layout: Optional[int] = Field(default=0, sa_column=Column(INT), description="是否启用布局识别")
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


class Knowledge(KnowledgeBase, table=True):
    __table_args__ = {"extend_existing": True}  # 允许扩展现有的表


class KnowledgeDao(Knowledge):
    @classmethod
    def insert(cls, name, desc, model, collection_name, index_name, enable_layout):
        with session_getter() as session:
            new_knowledge = Knowledge(name=name, desc=desc, model=model, collection_name=collection_name,
                                      index_name=index_name,
                                      enable_layout=enable_layout)
            session.add(new_knowledge)
            session.commit()
            session.refresh(new_knowledge)
            logger_client.info(f"Insert Knowledge: {name}")
            return new_knowledge

    @classmethod
    def delete_by_id(cls, id):
        with session_getter() as session:
            delete_knowledge = session.query(Knowledge).filter(Knowledge.id == id).first()
            if delete_knowledge:
                delete_knowledge.delete = 1
                session.commit()
                logger_client.info(f"Deleted Knowledge with id: {id}")
            else:
                raise HTTPException(status_code=404, detail="Knowledge not found")

    @classmethod
    def update(cls, id, name, desc):
        with session_getter() as session:
            update_knowledge = session.query(Knowledge).filter(Knowledge.id == id).first()
            if update_knowledge:
                if name is not None:
                    update_knowledge.name = name
                if desc is not None:
                    update_knowledge.desc = desc
                session.commit()
                session.refresh(update_knowledge)
                logger_client.info(f"Updated Knowledge with id: {id}")
                return update_knowledge
            else:
                raise HTTPException(status_code=404, detail="Knowledge not found")

    @classmethod
    def select(cls, id=None, page=None, page_size=None):
        with session_getter() as session:
            if id is not None:  # 查特定记录
                knowledge = session.query(Knowledge).where(Knowledge.delete == 0).filter(Knowledge.id == id).first()
                return knowledge
            else:  # 分页查询全部
                query = session.query(Knowledge).where(Knowledge.delete == 0)
                if page is not None and page_size is not None:
                    # 计算偏移量
                    offset = (page - 1) * page_size
                    all_knowledge = query.offset(offset).limit(page_size).all()
                else:
                    all_knowledge = query.all()
                logger_client.info("Fetched all Knowledge entries.")
                return all_knowledge
