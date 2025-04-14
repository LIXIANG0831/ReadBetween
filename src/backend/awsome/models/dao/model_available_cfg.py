from __future__ import annotations
import uuid
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.orm import relationship

from awsome.core.context import session_getter
from awsome.models.dao.base import AwsomeDBModel
from sqlalchemy import Column, String, ForeignKey
from sqlmodel import Field, DateTime, text, Relationship
from datetime import datetime

from awsome.models.dao.model_provider_cfg import ModelProviderCfg
from awsome.models.dao.model_setting_cfg import ModelSettingCfg


class ModelAvailableCfgBase(AwsomeDBModel):
    __tablename__ = "model_available_cfg"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True, description="可用配置ID")

    setting_id: str = Field(sa_column=Column(String(255), ForeignKey('model_setting_cfg.id', ondelete='CASCADE'),
                                             index=True, nullable=False), description="模型供应商实质化ID")
    # model_setting_cfg: Optional["ModelSettingCfg"] = Relationship(
    #     sa_relationship=relationship("ModelSettingCfg", backref="model_available_cfg")
    # )

    name: str = Field(sa_column=Column(String(255), index=False, nullable=False),
                      description="模型名称")
    type: str = Field(sa_column=Column(String(255), index=False, nullable=False),
                      description="模型类型 | embedding | llm")

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


class ModelAvailableCfg(ModelAvailableCfgBase, table=True):
    __table_args__ = {"extend_existing": True}  # 允许扩展现有的表


class ModelAvailableCfgWithSetting(BaseModel):
    id: str
    name: str
    type: str
    api_key: str
    base_url: str
    mark: str


class ModelAvailableCfgDao:
    @staticmethod
    def insert(model_available_cfg: ModelAvailableCfg):
        with session_getter() as session:
            session.add(model_available_cfg)
            session.commit()
            session.refresh(model_available_cfg)
            return model_available_cfg

    @staticmethod
    def select_all():
        with (session_getter() as session):
            results = session.query(ModelAvailableCfg, ModelSettingCfg, ModelProviderCfg) \
                .join(ModelSettingCfg, ModelAvailableCfg.setting_id == ModelSettingCfg.id) \
                .join(ModelProviderCfg, ModelSettingCfg.provider_id == ModelProviderCfg.id) \
                .all()

            final_results = []
            for model_available_cfg, model_setting_cfg, model_provider_cfg in results:
                model_cfg = ModelAvailableCfgWithSetting(
                    id=model_available_cfg.id,
                    name=model_available_cfg.name,
                    type=model_available_cfg.type,
                    api_key=model_setting_cfg.api_key,
                    base_url=model_setting_cfg.base_url,
                    mark=model_provider_cfg.mark
                )
                final_results.append(model_cfg)
            return final_results

    @staticmethod
    def select_one(id):
        with session_getter() as session:
            return session.query(ModelAvailableCfg).filter(ModelAvailableCfg.id == id).first()

    @staticmethod
    def delete_by_id(id):
        delete_model_cfg = ModelAvailableCfgDao.select_one(id)
        if delete_model_cfg is None:
            return None
        with session_getter() as session:
            session.delete(delete_model_cfg)
            session.commit()
            return delete_model_cfg

    @staticmethod
    def select_cfg_info_by_id(id):
        with session_getter() as session:
                return session.query(ModelAvailableCfg, ModelSettingCfg, ModelProviderCfg) \
                    .join(ModelSettingCfg, ModelAvailableCfg.setting_id == ModelSettingCfg.id) \
                    .join(ModelProviderCfg, ModelSettingCfg.provider_id == ModelProviderCfg.id) \
                    .filter(ModelAvailableCfg.id == id).first()
