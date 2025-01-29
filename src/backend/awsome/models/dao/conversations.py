from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from .messages import Message
    from .conversation_knowledge_link import ConversationKnowledgeLink, ConversationKnowledgeLinkDao

import uuid

from sqlalchemy.orm import Mapped, relationship, selectinload
from sqlmodel import Field, Relationship
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, text, select

from awsome.core.context import async_session_getter
from awsome.models.dao.base import AwsomeDBModel
from awsome.models.dao.knowledge import Knowledge
from awsome.utils.logger_util import logger_util

from .conversation_knowledge_link import ConversationKnowledgeLink, ConversationKnowledgeLinkDao


class ConversationBase(AwsomeDBModel):
    __tablename__ = "conversations"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True, description="会话ID")
    title: Optional[str] = Field(sa_column=Column(String(255), index=True), description="对话标题")
    model: str = Field(sa_column=Column(String(50), nullable=False), default="gpt-3.5-turbo", description="使用模型")
    system_prompt: str = Field(sa_column=Column(Text), default="你是一个有用的助手", description="系统提示词")
    temperature: float = Field(default=0.7, ge=0, le=2, description="生成温度")
    delete: int = Field(default=0, index=True, description="删除标志")
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


class Conversation(ConversationBase, table=True):
    __table_args__ = {"extend_existing": True}
    messages: Mapped[List["Message"]] = Relationship(
        back_populates="conversation",
        sa_relationship=relationship(  # 显式使用SQLAlchemy的relationship
            "Message",  # 使用字符串形式指定目标模型
            back_populates="conversation",
            lazy="selectin",
            cascade="all, delete-orphan"
        )
    )

    knowledge_links: Mapped[List["ConversationKnowledgeLink"]] = Relationship(
        back_populates="conversation",
        sa_relationship=relationship(
            "ConversationKnowledgeLink",
            back_populates="conversation",
            lazy="selectin",
            cascade="all, delete-orphan"
        )
    )

    @property
    def knowledge_bases(self) -> List["Knowledge"]:
        return [
            link.knowledge
            for link in self.knowledge_links
            if link.knowledge.delete == 0
        ]


class ConversationDao:
    @staticmethod
    async def create(**kwargs):
        async with async_session_getter() as session:
            new_conv = Conversation(**kwargs)
            session.add(new_conv)
            await session.commit()
            await session.refresh(new_conv)
            logger_util.info(f"Created conversation: {new_conv.id}")
            return new_conv

    @staticmethod
    async def get(conv_id: str):
        async with async_session_getter() as session:
            stmt = select(Conversation).where(
                Conversation.id == conv_id,
                Conversation.delete == 0
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def list_with_kb(page: int = 1, page_size: int = 20):
        async with async_session_getter() as session:
            offset = (page - 1) * page_size
            stmt = (
                select(Conversation)
                .where(Conversation.delete == 0)
                .options(
                    selectinload(Conversation.knowledge_links).selectinload(ConversationKnowledgeLink.knowledge)
                )
                .order_by(Conversation.updated_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def list(page: int = 1, page_size: int = 20):
        async with async_session_getter() as session:
            offset = (page - 1) * page_size
            stmt = select(Conversation).where(
                Conversation.delete == 0
            ).order_by(Conversation.updated_at.desc()).offset(offset).limit(page_size)
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def soft_delete(conv_id: str):
        async with async_session_getter() as session:
            stmt = select(Conversation).where(
                Conversation.id == conv_id,
                Conversation.delete == 0
            )
            result = await session.execute(stmt)
            conv = result.scalar_one_or_none()
            if conv:
                conv.delete = 1
                await session.commit()
                logger_util.info(f"Soft deleted conversation: {conv_id}")
                return True
            return False

    @staticmethod
    async def update(conv_id: str, title: Optional[str] = None, system_prompt: Optional[str] = None,
                     temperature: Optional[float] = None, knowledge_base_ids: Optional[List[str]] = None):

        async with async_session_getter() as session:
            stmt = select(Conversation).where(
                Conversation.id == conv_id,
                Conversation.delete == 0
            )
            result = await session.execute(stmt)
            conv = result.scalar_one_or_none()

            if conv:
                if title is not None:
                    conv.title = title
                if system_prompt is not None:
                    conv.system_prompt = system_prompt
                if temperature is not None:
                    conv.temperature = temperature

                conv.updated_at = datetime.utcnow()  # 更新更新时间
                await session.commit()
                await session.refresh(conv)

            if knowledge_base_ids is not None:
                # 先删除所有旧关联（硬删除）
                await ConversationKnowledgeLinkDao.delete(conv_id)

                # 创建新关联
                for kb_id in knowledge_base_ids:
                    await ConversationKnowledgeLinkDao.create(conv_id, kb_id)

            logger_util.info(f"Updated conversation: {conv_id}")

            return None

    @classmethod
    async def one_with_kb(cls, conv_id: str):
        async with async_session_getter() as session:
            stmt = (
                select(Conversation)
                .where(
                    Conversation.id == conv_id,
                    Conversation.delete == 0
                )
                .options(
                    selectinload(Conversation.knowledge_links)
                    .selectinload(ConversationKnowledgeLink.knowledge)
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
