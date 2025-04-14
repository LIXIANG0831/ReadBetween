from __future__ import annotations
import uuid
from typing import Optional, List
from awsome.models.dao.base import AwsomeDBModel
from sqlalchemy import Column, String
from sqlmodel import Field, DateTime, text

from awsome.core.context import session_getter
from datetime import datetime


class ModelProviderCfgBase(AwsomeDBModel):
    __tablename__ = "model_provider_cfg"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True, description="模型供应商ID")

    provider: str = Field(sa_column=Column(String(255), index=True, nullable=False), description="模型供应商")
    mark: str = Field(sa_column=Column(String(255), index=True, nullable=False), description="模型识别标识")

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


class ModelProviderCfg(ModelProviderCfgBase, table=True):
    __table_args__ = {"extend_existing": True}  # 允许扩展现有的表


class ModelProviderCfgDao:

    @staticmethod
    def select_all():
        with session_getter() as session:
            return session.query(ModelProviderCfg).all()

    @staticmethod
    def batch_insert(model_provider_list: List[ModelProviderCfg]):
        with session_getter() as session:
            session.add_all(model_provider_list)
            session.commit()
            for model_provider in model_provider_list:  # 刷新得到主键ID
                session.refresh(model_provider)
            return model_provider_list

    @staticmethod
    def search(model_provider: ModelProviderCfg):
        with session_getter() as session:
            provider = session.query(ModelProviderCfg).filter(ModelProviderCfg.provider == model_provider.provider).first()
            if provider is None:
                return True
            return False

    @staticmethod
    def insert(model_provider: ModelProviderCfg):
        with session_getter() as session:
            session.add(model_provider)
            session.commit()
            session.refresh(model_provider)
            return model_provider