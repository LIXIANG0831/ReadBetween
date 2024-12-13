import uuid
from typing import Optional
from awsome.models.dao.base import AwsomeDBModel
from sqlalchemy import Column, String, INT, select
from sqlmodel import Field, DateTime, text
from awsome.core.context import session_getter, async_session_getter
from awsome.utils.logger_util import logger_util
from datetime import datetime
from fastapi import HTTPException



class KnowledgeBase(AwsomeDBModel):
    __tablename__ = "knowledge"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True, description="主键ID")
    name: Optional[str] = Field(sa_column=Column(String(255), index=True, nullable=False), description="知识库名称")
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
    async def insert(cls, name, desc, model, collection_name, index_name, enable_layout):
        async with async_session_getter() as session:
            new_knowledge = Knowledge(name=name, desc=desc, model=model, collection_name=collection_name,
                                      index_name=index_name,
                                      enable_layout=enable_layout)
            session.add(new_knowledge)
            await session.commit()
            await session.refresh(new_knowledge)
            logger_util.info(f"Insert Knowledge: {name}")
            return new_knowledge

    @classmethod
    async def delete_by_id(cls, kb_id):
        async with (async_session_getter() as session):
            stmt = select(Knowledge).filter(Knowledge.id == kb_id)
            delete_knowledge = await session.execute(stmt)
            delete_knowledge = delete_knowledge.scalar_one_or_none()
            if delete_knowledge:
                delete_knowledge.delete = 1
                await session.commit()
                logger_util.info(f"Deleted Knowledge with id: {kb_id}")
            else:
                raise HTTPException(status_code=404, detail="Knowledge not found")

    @classmethod
    async def update(cls, kb_id, name, desc):
        async with async_session_getter() as session:
            query_stmt = select(Knowledge).where(Knowledge.id == kb_id)
            update_knowledge = await session.execute(query_stmt)
            update_knowledge = update_knowledge.scalar_one_or_none()
            if update_knowledge:
                if name is not None:
                    update_knowledge.name = name
                if desc is not None:
                    update_knowledge.desc = desc
                await session.commit()
                await session.refresh(update_knowledge)
                logger_util.info(f"Updated Knowledge with id: {kb_id}")
                return update_knowledge
            else:
                raise HTTPException(status_code=404, detail="Knowledge not found")

    @classmethod
    async def select(cls, kb_id=None, page=None, page_size=None):
        async with (async_session_getter() as session):
            stmt = select(Knowledge).where(Knowledge.delete == 0)
            if kb_id is not None:  # 查特定记录
                knowledge = await session.execute(stmt.filter(Knowledge.id == kb_id))
                knowledge = knowledge.scalar_one_or_none()
                return knowledge
            else:  # 分页查询全部
                if page is not None and page_size is not None:
                    offset = (page - 1) * page_size
                    result = await session.execute(stmt.offset(offset).limit(page_size))
                else:
                    result = await session.execute(stmt)

                all_knowledge = result.scalars().all()
                logger_util.info("Fetched all Knowledge entries.")
                return all_knowledge
