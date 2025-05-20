from __future__ import annotations

import time
import uuid
from typing import Optional

from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, text, select, update, JSON, BigInteger

from readbetween.core.context import async_session_getter
from readbetween.models.dao.base import AwsomeDBModel
from readbetween.utils.logger_util import logger_util


class MessageBase(AwsomeDBModel):
    __tablename__ = "messages"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()),
                    primary_key=True,
                    description="消息ID")
    conv_id: str = Field(
        sa_column=Column(
            String(36),
            ForeignKey("conversations.id", ondelete="CASCADE"),
            index=True
        ),
        description="关联会话ID"
    )
    role: str = Field(
        sa_column=Column(String(20), nullable=False),
        description="角色（system/user/assistant/tool）"
    )
    content: str = Field(
        sa_column=Column(Text, nullable=True),
        description="消息内容"
    )
    source: str = Field(
        sa_column=Column(Text, nullable=True),
        description="消息内容"
    )
    tool_calls: Optional[str] = Field(
        sa_column=Column(JSON, nullable=True), default=None, description="模型调用工具信息"
    )
    tool_call_id: str = Field(
        sa_column=Column(String(50), nullable=True,  default=None,),
        description="工具ID"
    )
    timestamp: int = Field(
        default_factory=lambda: int(time.time() * 1000),  # 动态生成毫秒时间戳
        sa_column=Column(BigInteger, nullable=False),
        description="消息时间戳（毫秒）"
    )
    delete: int = Field(
        default=0,
        description="删除标志"
    )


class Message(MessageBase, table=True):
    __table_args__ = {"extend_existing": True}
    conversation: Mapped["Conversation"] = Relationship(
        back_populates="messages",
        sa_relationship=relationship(  # 显式使用SQLAlchemy的relationship
            "Conversation",
            back_populates="messages"
        )
    )


class MessageDao:
    @staticmethod
    async def create_message(conv_id: str, role: str, content: str = None, source: str = None, tool_calls: str = None, tool_call_id: str = None):
        async with async_session_getter() as session:
            new_msg = Message(conv_id=conv_id, role=role, content=content, source=source, tool_calls=tool_calls, tool_call_id=tool_call_id)
            session.add(new_msg)
            await session.commit()
            await session.refresh(new_msg)
            logger_util.info(f"Created message in conversation: {conv_id}")
            return new_msg


    @staticmethod
    async def delete_message(message_id: str):
        """根据消息ID软删除单条消息"""
        async with async_session_getter() as session:
            stmt = update(Message).where(
                Message.id == message_id
            ).values(delete=1)
            await session.execute(stmt)
            await session.commit()
            logger_util.info(f"Soft deleted message: {message_id}")

    @staticmethod
    async def get_conversation_messages(conv_id: str, limit: int = 100):
        async with async_session_getter() as session:
            stmt = select(Message).where(
                Message.conv_id == conv_id,
                Message.delete == 0
            ).order_by(Message.timestamp.asc()).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def delete_conversation_messages(conv_id: str):
        async with async_session_getter() as session:
            stmt = update(Message).where(
                Message.conv_id == conv_id
            ).values(delete=1)
            await session.execute(stmt)
            await session.commit()
            logger_util.info(f"Soft deleted all messages in conversation: {conv_id}")