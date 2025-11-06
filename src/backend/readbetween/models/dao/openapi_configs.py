from __future__ import annotations

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship, select, update, desc
from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime, func
from datetime import datetime

from readbetween.core.context import async_session_getter
from readbetween.models.dao.base import AwsomeDBModel
from readbetween.models.dao.openapi_tools import OpenAPITool
from readbetween.utils.logger_util import logger_util


class OpenAPIConfigBase(AwsomeDBModel):
    __tablename__ = "openapi_configs"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="OpenAPI配置ID"
    )
    name: str = Field(
        sa_column=Column(String(255), nullable=False),
        description="OpenAPI配置名称"
    )
    openapi_spec: Dict[str, Any] = Field(
        sa_column=Column(JSON, nullable=False),
        description="OpenAPI规范JSON"
    )
    credentials: Optional[str] = Field(
        sa_column=Column(Text, nullable=True),
        default=None,
        description="认证凭据"
    )
    description: Optional[str] = Field(
        sa_column=Column(Text, nullable=True),
        default=None,
        description="描述"
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


class OpenAPIConfig(OpenAPIConfigBase, table=True):
    __table_args__ = {"extend_existing": True}

    tools: Mapped[List["OpenAPITool"]] = Relationship(
        back_populates="openapi_config",
        sa_relationship=relationship(
            "OpenAPITool",
            back_populates="openapi_config",
            cascade="all, delete-orphan"
        )
    )


class OpenAPIConfigDao:
    @staticmethod
    async def create_config(
            name: str,
            openapi_spec: Dict[str, Any],
            credentials: Optional[str] = None,
            base_url: Optional[str] = None,
            description: Optional[str] = None
    ) -> OpenAPIConfig:
        async with async_session_getter() as session:
            new_config = OpenAPIConfig(
                name=name,
                openapi_spec=openapi_spec,
                credentials=credentials,
                base_url=base_url,
                description=description
            )
            session.add(new_config)
            await session.commit()
            await session.refresh(new_config)
            logger_util.info(f"Created OpenAPI config: {name}")
            return new_config

    @staticmethod
    async def get_config(config_id: str) -> Optional[OpenAPIConfig]:
        async with async_session_getter() as session:
            stmt = select(OpenAPIConfig).where(OpenAPIConfig.id == config_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_config_by_name(name: str) -> Optional[OpenAPIConfig]:
        async with async_session_getter() as session:
            stmt = select(OpenAPIConfig).where(OpenAPIConfig.name == name)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_all_configs() -> List[OpenAPIConfig]:
        async with async_session_getter() as session:
            stmt = select(OpenAPIConfig).order_by(OpenAPIConfig.created_at.desc())
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def update_config(
            config_id: str,
            name: Optional[str] = None,
            credentials: Optional[str] = None,
            base_url: Optional[str] = None,
            description: Optional[str] = None
    ) -> Optional[OpenAPIConfig]:
        async with async_session_getter() as session:
            # 先检查配置是否存在
            stmt = select(OpenAPIConfig).where(OpenAPIConfig.id == config_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if not config:
                return None

            # 构建更新字段
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if credentials is not None:
                update_data["credentials"] = credentials
            if base_url is not None:
                update_data["base_url"] = base_url
            if description is not None:
                update_data["description"] = description

            if update_data:
                stmt = update(OpenAPIConfig).where(
                    OpenAPIConfig.id == config_id
                ).values(**update_data)
                await session.execute(stmt)
                await session.commit()

                # 重新查询获取更新后的对象
                stmt = select(OpenAPIConfig).where(OpenAPIConfig.id == config_id)
                result = await session.execute(stmt)
                updated_config = result.scalar_one_or_none()

                logger_util.info(f"Updated OpenAPI config: {config_id}")
                return updated_config

            return config

    @staticmethod
    async def delete_config(config_id: str) -> bool:
        async with async_session_getter() as session:
            stmt = select(OpenAPIConfig).where(OpenAPIConfig.id == config_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if not config:
                return False

            await session.delete(config)
            await session.commit()
            logger_util.info(f"Deleted OpenAPI config: {config_id}")
            return True

    @staticmethod
    async def get_configs_paginated(
            page: int = 1,
            size: int = 20
    ) -> Dict[str, Any]:
        """获取分页的配置列表"""
        async with async_session_getter() as session:
            # 计算偏移量
            offset = (page - 1) * size

            # 查询总数
            count_stmt = select(func.count(OpenAPIConfig.id))
            count_result = await session.execute(count_stmt)
            total = count_result.scalar()

            # 查询分页数据
            stmt = (
                select(OpenAPIConfig)
                .order_by(desc(OpenAPIConfig.created_at))
                .offset(offset)
                .limit(size)
            )
            result = await session.execute(stmt)
            configs = result.scalars().all()

            return {
                "configs": configs,
                "total": total,
            }