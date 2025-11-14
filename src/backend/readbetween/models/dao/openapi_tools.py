from __future__ import annotations

import uuid
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship, select, update, desc
from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime, func
from datetime import datetime

from readbetween.core.context import async_session_getter
from readbetween.models.dao.base import AwsomeDBModel
from readbetween.utils.logger_util import logger_util

if TYPE_CHECKING:
    from .openapi_configs import OpenAPIConfig
    from .conversation_tool_link import ConversationToolLink


class OpenAPIToolBase(AwsomeDBModel):
    __tablename__ = "openapi_tools"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="OpenAPI工具ID"
    )
    openapi_config_id: str = Field(
        sa_column=Column(
            String(36),
            ForeignKey("openapi_configs.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        ),
        description="关联的OpenAPI配置ID"
    )
    name: str = Field(
        sa_column=Column(String(255), nullable=False),
        description="工具名称"
    )
    description: Optional[str] = Field(
        sa_column=Column(Text, nullable=True),
        default=None,
        description="工具描述"
    )
    method: str = Field(
        sa_column=Column(String(10), nullable=False),
        description="HTTP方法"
    )
    path: str = Field(
        sa_column=Column(String(500), nullable=False),
        description="API路径"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        sa_column=Column(JSON, nullable=True),
        default=None,
        description="参数定义"
    )
    tool_definition: Dict[str, Any] = Field(
        sa_column=Column(JSON, nullable=False),
        description="完整的工具定义(LLM格式)"
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


class OpenAPITool(OpenAPIToolBase, table=True):
    __table_args__ = {"extend_existing": True}

    openapi_config: Mapped["OpenAPIConfig"] = Relationship(
        back_populates="tools",
        sa_relationship=relationship(
            "OpenAPIConfig",
            back_populates="tools",
            lazy="selectin"
        )
    )

    conversation_links: Mapped[List["ConversationToolLink"]] = Relationship(
        back_populates="openapi_tool",
        sa_relationship=relationship(
            "ConversationToolLink",
            back_populates="openapi_tool",
            cascade="all, delete-orphan",
            lazy="selectin"
        )
    )


class OpenAPIToolDao:
    @staticmethod
    async def create_tool(
            openapi_config_id: str,
            name: str,
            method: str,
            path: str,
            tool_definition: Dict[str, Any],
            description: Optional[str] = None,
            parameters: Optional[Dict[str, Any]] = None
    ) -> OpenAPITool:
        async with async_session_getter() as session:
            new_tool = OpenAPITool(
                openapi_config_id=openapi_config_id,
                name=name,
                description=description,
                method=method,
                path=path,
                parameters=parameters,
                tool_definition=tool_definition
            )
            session.add(new_tool)
            await session.commit()
            await session.refresh(new_tool)
            logger_util.info(f"Created OpenAPI tool: {name} for config: {openapi_config_id}")
            return new_tool

    @staticmethod
    async def get_tool(tool_id: str) -> Optional[OpenAPITool]:
        async with async_session_getter() as session:
            stmt = select(OpenAPITool).where(OpenAPITool.id == tool_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_tool_by_name_and_config(name: str, openapi_config_id: str) -> Optional[OpenAPITool]:
        async with async_session_getter() as session:
            stmt = select(OpenAPITool).where(
                OpenAPITool.name == name,
                OpenAPITool.openapi_config_id == openapi_config_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_tools_by_config(openapi_config_id: str) -> List[OpenAPITool]:
        async with async_session_getter() as session:
            stmt = select(OpenAPITool).where(
                OpenAPITool.openapi_config_id == openapi_config_id
            ).order_by(OpenAPITool.created_at.asc())
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_all_tools() -> List[OpenAPITool]:
        async with async_session_getter() as session:
            stmt = select(OpenAPITool).order_by(OpenAPITool.created_at.desc())
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_tools_by_ids(tool_ids: List[str]) -> List[OpenAPITool]:
        async with async_session_getter() as session:
            stmt = select(OpenAPITool).where(OpenAPITool.id.in_(tool_ids))
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def delete_tools_by_config(openapi_config_id: str) -> int:
        async with async_session_getter() as session:
            stmt = select(OpenAPITool).where(OpenAPITool.openapi_config_id == openapi_config_id)
            result = await session.execute(stmt)
            tools = result.scalars().all()

            delete_count = 0
            for tool in tools:
                await session.delete(tool)
                delete_count += 1

            await session.commit()
            logger_util.info(f"Deleted {delete_count} tools for config: {openapi_config_id}")
            return delete_count

    @staticmethod
    async def delete_tool(tool_id: str) -> bool:
        async with async_session_getter() as session:
            stmt = select(OpenAPITool).where(OpenAPITool.id == tool_id)
            result = await session.execute(stmt)
            tool = result.scalar_one_or_none()

            if not tool:
                return False

            await session.delete(tool)
            await session.commit()
            logger_util.info(f"Deleted OpenAPI tool: {tool_id}")
            return True

    @staticmethod
    async def batch_create_tools(tools_data: List[Dict[str, Any]]) -> List[OpenAPITool]:
        async with async_session_getter() as session:
            tools = []
            for tool_data in tools_data:
                tool = OpenAPITool(**tool_data)
                session.add(tool)
                tools.append(tool)

            await session.commit()

            # 刷新所有新创建的工具对象
            for tool in tools:
                await session.refresh(tool)

            logger_util.info(f"Batch created {len(tools)} OpenAPI tools")
            return tools

    @staticmethod
    async def get_tools_by_config_paginated(
            config_id: str,
            page: int = 1,
            size: int = 20
    ) -> Dict[str, Any]:
        """获取配置的分页工具列表"""
        async with async_session_getter() as session:
            # 计算偏移量
            offset = (page - 1) * size

            # 查询总数
            count_stmt = select(func.count(OpenAPITool.id)).where(
                OpenAPITool.openapi_config_id == config_id
            )
            count_result = await session.execute(count_stmt)
            total = count_result.scalar()

            # 查询分页数据
            stmt = (
                select(OpenAPITool)
                .where(OpenAPITool.openapi_config_id == config_id)
                .order_by(desc(OpenAPITool.created_at))
                .offset(offset)
                .limit(size)
            )
            result = await session.execute(stmt)
            tools = result.scalars().all()

            return {
                "tools": tools,
                "total": total,
            }