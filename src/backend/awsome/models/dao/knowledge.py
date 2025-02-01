from __future__ import annotations
import uuid
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy.orm import Mapped, relationship

from awsome.models.dao.base import AwsomeDBModel
from sqlalchemy import Column, String, INT, select, func
from sqlmodel import Field, DateTime, text, Relationship
from awsome.core.context import session_getter, async_session_getter
from awsome.utils.logger_util import logger_util
from datetime import datetime
from fastapi import HTTPException

if TYPE_CHECKING:
    from .conversation_knowledge_link import ConversationKnowledgeLink
    from .conversations import Conversation

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

    conversation_links: Mapped[List["ConversationKnowledgeLink"]] = Relationship(
        back_populates="knowledge",
        sa_relationship=relationship(
            "ConversationKnowledgeLink",
            back_populates="knowledge"
        )
    )

    @property
    def conversations(self) -> List["Conversation"]:
        return [
            link.conversation
            for link in self.conversation_links
            if link.delete == 0 and link.conversation.delete == 0
        ]


class KnowledgeDao:
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
            stmt = select(Knowledge).where(Knowledge.delete == 0).order_by(Knowledge.create_time.desc())
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

    @classmethod
    async def cnt_knowledge_total(cls):
        async with (async_session_getter() as session):
            # 构造查询语句，统计满足条件的记录总数
            stmt = select(func.count()).select_from(Knowledge).where(Knowledge.delete == 0)

            # 执行查询并获取结果
            result = await session.execute(stmt)
            total_count = result.scalar()  # 获取总数

            logger_util.info(f"Total count of Knowledge entries: {total_count}")
            return total_count

    @classmethod
    async def get_many(cls, knowledge_base_ids: List[str]) -> List[Knowledge]:
        """
        批量获取多个知识库记录
        :param knowledge_base_ids: 知识库ID列表
        :return: 知识库对象列表
        """
        async with async_session_getter() as session:
            # 构建查询语句：ID在列表中且未被删除
            stmt = (
                select(Knowledge)
                .where(Knowledge.id.in_(knowledge_base_ids))
                .where(Knowledge.delete == 0)
            )

            try:
                result = await session.execute(stmt)
                knowledge_list = result.scalars().all()

                # 验证是否找到所有请求的ID
                found_ids = {kb.id for kb in knowledge_list}
                missing_ids = set(knowledge_base_ids) - found_ids

                if missing_ids:
                    logger_util.warning(f"未找到的知识库ID: {missing_ids}")

                return knowledge_list

            except Exception as e:
                logger_util.error(f"批量获取知识库失败: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"数据库查询错误: {str(e)}"
                )