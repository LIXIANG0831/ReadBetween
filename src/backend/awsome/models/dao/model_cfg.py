import uuid
from typing import Optional
from awsome.models.dao.base import AwsomeDBModel
from sqlalchemy import Column, String, INT
from sqlmodel import Field, DateTime, text
from awsome.utils.context import session_getter
from awsome.utils.logger_client import logger_util
from datetime import datetime
from fastapi import HTTPException


class ModelCfgBase(AwsomeDBModel):
    __tablename__ = "model_cfg"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True, description="模型ID")

    provider_id: str = Field(sa_column=Column(String(255), index=True, nullable=False), description="模型供应商ID")
    model_class: str = Field(sa_column=Column(String(255), index=True, nullable=False), description="模型种类")
    model_name: str = Field(sa_column=Column(String(255), index=True, nullable=False), description="模型名称")
    api_key: str = Field(sa_column=Column(String(255), index=False, nullable=False), description="模型API_KEY")
    base_url: str = Field(sa_column=Column(String(255), index=False, nullable=True), description="模型BASE_URL")

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


class ModelCfg(ModelCfgBase, table=True):
    __table_args__ = {"extend_existing": True}  # 允许扩展现有的表
