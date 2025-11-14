from __future__ import annotations

import uuid
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship, select, update
from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime, func
from datetime import datetime

from readbetween.core.context import async_session_getter
from readbetween.models.dao.base import AwsomeDBModel
from readbetween.utils.logger_util import logger_util

if TYPE_CHECKING:
    from .conversation import Conversation
    from .openapi_tools import OpenAPITool

class ConversationToolLinkBase(AwsomeDBModel):
    __tablename__ = "conversation_tool_link"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="链接ID"
    )
    conversation_id: str = Field(
        sa_column=Column(
            String(36),
            ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        ),
        description="会话ID"
    )
    openapi_tool_id: str = Field(
        sa_column=Column(
            String(36),
            ForeignKey("openapi_tools.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        ),
        description="OpenAPI工具ID"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, nullable=False, server_default=func.now()),
        description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now()),
        description="更新时间"
    )


class ConversationToolLink(ConversationToolLinkBase, table=True):
    __table_args__ = {"extend_existing": True}

    conversation: Mapped["Conversation"] = Relationship(
        back_populates="tool_links",
        sa_relationship=relationship(
            "Conversation",
            back_populates="tool_links",
            lazy="selectin"
        )
    )

    openapi_tool: Mapped["OpenAPITool"] = Relationship(
        back_populates="conversation_links",
        sa_relationship=relationship(
            "OpenAPITool",
            back_populates="conversation_links",
            lazy="selectin"
        )
    )


class ConversationToolLinkDao:
    @staticmethod
    async def create_link(conversation_id: str, openapi_tool_id: str) -> Optional[ConversationToolLink]:
        async with async_session_getter() as session:
            # 检查是否已存在链接
            stmt = select(ConversationToolLink).where(
                ConversationToolLink.conversation_id == conversation_id,
                ConversationToolLink.openapi_tool_id == openapi_tool_id
            )
            result = await session.execute(stmt)
            existing_link = result.scalar_one_or_none()

            if existing_link:
                return existing_link

            # 创建新链接
            new_link = ConversationToolLink(
                conversation_id=conversation_id,
                openapi_tool_id=openapi_tool_id
            )
            session.add(new_link)
            await session.commit()
            await session.refresh(new_link)
            logger_util.info(f"Created tool link: conversation {conversation_id} -> tool {openapi_tool_id}")
            return new_link

    @staticmethod
    async def create_links(conversation_id: str, openapi_tool_ids: List[str]) -> List[ConversationToolLink]:
        async with async_session_getter() as session:
            links = []

            for tool_id in openapi_tool_ids:
                # 检查是否已存在链接
                stmt = select(ConversationToolLink).where(
                    ConversationToolLink.conversation_id == conversation_id,
                    ConversationToolLink.openapi_tool_id == tool_id
                )
                result = await session.execute(stmt)
                existing_link = result.scalar_one_or_none()

                if existing_link:
                    links.append(existing_link)
                    continue

                # 创建新链接
                new_link = ConversationToolLink(
                    conversation_id=conversation_id,
                    openapi_tool_id=tool_id
                )
                session.add(new_link)
                links.append(new_link)

            await session.commit()

            # 刷新所有新创建的链接对象
            for link in links:
                await session.refresh(link)

            logger_util.info(f"Created {len(links)} tool links for conversation {conversation_id}")
            return links

    @staticmethod
    async def delete_link(conversation_id: str, openapi_tool_id: str) -> bool:
        async with async_session_getter() as session:
            stmt = select(ConversationToolLink).where(
                ConversationToolLink.conversation_id == conversation_id,
                ConversationToolLink.openapi_tool_id == openapi_tool_id
            )
            result = await session.execute(stmt)
            link = result.scalar_one_or_none()

            if not link:
                return False

            await session.delete(link)
            await session.commit()
            logger_util.info(f"Deleted tool link: conversation {conversation_id} -> tool {openapi_tool_id}")
            return True

    @staticmethod
    async def delete_links(conversation_id: str, openapi_tool_ids: List[str]) -> int:
        async with async_session_getter() as session:
            stmt = select(ConversationToolLink).where(
                ConversationToolLink.conversation_id == conversation_id,
                ConversationToolLink.openapi_tool_id.in_(openapi_tool_ids)
            )
            result = await session.execute(stmt)
            links = result.scalars().all()

            delete_count = 0
            for link in links:
                await session.delete(link)
                delete_count += 1

            await session.commit()
            logger_util.info(f"Deleted {delete_count} tool links from conversation {conversation_id}")
            return delete_count

    @staticmethod
    async def get_conversation_tools(conversation_id: str) -> List[OpenAPITool]:
        async with async_session_getter() as session:
            stmt = select(OpenAPITool).join(
                ConversationToolLink,
                ConversationToolLink.openapi_tool_id == OpenAPITool.id
            ).where(
                ConversationToolLink.conversation_id == conversation_id
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_conversation_tool_definitions(conversation_id: str) -> List[Dict[str, Any]]:
        async with async_session_getter() as session:
            stmt = select(OpenAPITool.tool_definition).join(
                ConversationToolLink,
                ConversationToolLink.openapi_tool_id == OpenAPITool.id
            ).where(
                ConversationToolLink.conversation_id == conversation_id
            )
            result = await session.execute(stmt)
            return [row[0] for row in result.all()]

    @staticmethod
    async def get_conversation_tool_ids(conversation_id: str) -> List[str]:
        async with async_session_getter() as session:
            stmt = select(ConversationToolLink.openapi_tool_id).where(
                ConversationToolLink.conversation_id == conversation_id
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def is_tool_linked_to_conversation(conversation_id: str, openapi_tool_id: str) -> bool:
        async with async_session_getter() as session:
            stmt = select(ConversationToolLink).where(
                ConversationToolLink.conversation_id == conversation_id,
                ConversationToolLink.openapi_tool_id == openapi_tool_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    @staticmethod
    async def delete_all_conversation_links(conversation_id: str) -> int:
        async with async_session_getter() as session:
            stmt = select(ConversationToolLink).where(
                ConversationToolLink.conversation_id == conversation_id
            )
            result = await session.execute(stmt)
            links = result.scalars().all()

            delete_count = 0
            for link in links:
                await session.delete(link)
                delete_count += 1

            await session.commit()
            logger_util.info(f"Deleted all {delete_count} tool links for conversation {conversation_id}")
            return delete_count

    @staticmethod
    async def get_conversation_links(conversation_id: str) -> List[ConversationToolLink]:
        async with async_session_getter() as session:
            stmt = select(ConversationToolLink).where(
                ConversationToolLink.conversation_id == conversation_id
            )
            result = await session.execute(stmt)
            return result.scalars().all()