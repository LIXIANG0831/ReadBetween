from __future__ import annotations
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Column, DateTime, text, select, update
from sqlalchemy.orm import Mapped, relationship

from awsome.core.context import async_session_getter
from awsome.models.dao.base import AwsomeDBModel
from sqlmodel import Field, Relationship

from awsome.models.dao.knowledge import Knowledge
from awsome.utils.logger_util import logger_util


if TYPE_CHECKING:
    from .conversations import Conversation
    from .knowledge import Knowledge


class ConversationKnowledgeLinkBase(AwsomeDBModel):
    __tablename__ = "conversation_knowledge_link"

    conversation_id: str = Field(..., foreign_key="conversations.id", primary_key=True)
    knowledge_base_id: str = Field(..., foreign_key="knowledge.id", primary_key=True)

    created_at: datetime = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP')
        ),
        description="创建时间"
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP'),
            onupdate=text('CURRENT_TIMESTAMP')
        ),
        description="更新时间"
    )


class ConversationKnowledgeLink(ConversationKnowledgeLinkBase, table=True):
    __table_args__ = {"extend_existing": True}

    conversation: Mapped["Conversation"] = Relationship(
        back_populates="knowledge_links",
        sa_relationship=relationship(
            "Conversation",
            back_populates="knowledge_links",
            lazy="selectin"
        )
    )

    knowledge: Mapped["Knowledge"] = Relationship(
        back_populates="conversation_links",
        sa_relationship=relationship(
            "Knowledge",
            back_populates="conversation_links",
            lazy="selectin"
        )
    )


class ConversationKnowledgeLinkDao:
    @staticmethod
    async def create(conversation_id: str, knowledge_id: str) -> ConversationKnowledgeLink:
        async with async_session_getter() as session:
            new_conv_kb_link = ConversationKnowledgeLink(conversation_id=conversation_id, knowledge_base_id=knowledge_id)
            session.add(new_conv_kb_link)
            await session.commit()
            await session.refresh(new_conv_kb_link)
            logger_util.info(f"Created ConversationKnowledgeLink: {new_conv_kb_link.conversation_id}")
            return new_conv_kb_link

    @staticmethod
    async def delete(conv_id: str):
        async with async_session_getter() as session:
            # 查询要删除的记录
            stmt = select(ConversationKnowledgeLink).where(
                ConversationKnowledgeLink.conversation_id == conv_id
            )
            result = await session.execute(stmt)
            links_to_delete = result.scalars().all()

            # 如果有记录，执行删除
            if links_to_delete:
                for link in links_to_delete:
                    await session.delete(link)
                await session.commit()
                logger_util.info(f"Hard deleted all conversation_knowledge_link for conversation_id: {conv_id}")
            else:
                logger_util.warning(
                    f"No conversation_knowledge_link found for deletion with conversation_id: {conv_id}")

    @classmethod
    async def get_active_links(cls, conv_id: str):
        """获取会话所有有效知识库关联"""
        async with async_session_getter() as session:
            stmt = select(ConversationKnowledgeLink).where(
                ConversationKnowledgeLink.conversation_id == conv_id
            )
            result = await session.execute(stmt)
            return result.scalars().all()


    @classmethod
    async def get_attached_knowledge(cls, conv_id: str) -> List[Knowledge]:
        """获取会话关联的所有有效知识库"""
        links = await cls.get_active_links(conv_id)
        return [link.knowledge for link in links if link.knowledge.delete == 0]
