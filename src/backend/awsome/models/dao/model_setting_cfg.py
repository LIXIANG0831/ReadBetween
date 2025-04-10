import uuid
from typing import Optional
from awsome.models.dao.base import AwsomeDBModel
from sqlalchemy import Column, String
from sqlmodel import Field, DateTime, text
from pydantic import BaseModel
from awsome.models.dao.model_provider_cfg import ModelProviderCfg
from awsome.core.context import session_getter
from datetime import datetime
from awsome.utils.tools import EncryptionTool

encryption_tool = EncryptionTool()


class ModelCfgWithProvider(BaseModel):
    id: str
    # f_model_class: str
    # f_model_name: str
    api_key: str
    base_url: str
    mark: str


class ModelSettingCfgBase(AwsomeDBModel):
    __tablename__ = "model_setting_cfg"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True, description="模型ID")

    provider_id: str = Field(sa_column=Column(String(255), index=True, nullable=False), description="模型供应商ID")
    # f_model_class: str = Field(sa_column=Column(String(255), index=True, nullable=False), description="模型种类")
    # f_model_name: str = Field(sa_column=Column(String(255), index=True, nullable=False), description="模型名称")
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


class ModelSettingCfg(ModelSettingCfgBase, table=True):
    __table_args__ = {"extend_existing": True}  # 允许扩展现有的表


class ModelSettingCfgDao:
    @staticmethod
    def insert(model_cfg: ModelSettingCfg):
        with session_getter() as session:
            session.add(model_cfg)
            session.commit()
            session.refresh(model_cfg)
            return model_cfg

    @staticmethod
    def delete_by_id(id):
        delete_model_cfg = ModelSettingCfgDao.select_one(id)
        if delete_model_cfg is None:
            return None
        with session_getter() as session:
            session.delete(delete_model_cfg)
            session.commit()
            return delete_model_cfg

    @staticmethod
    def select_all():
        with (session_getter() as session):
            results = session.query(ModelSettingCfg, ModelProviderCfg) \
                .join(ModelProviderCfg, ModelSettingCfg.provider_id == ModelProviderCfg.id) \
                .all()

            final_results = []
            for model_cfg, model_provider_cfg in results:
                model_cfg_with_provider = ModelCfgWithProvider(
                    id=model_cfg.id,
                    # f_model_class=model_cfg.f_model_class,
                    # f_model_name=model_cfg.f_model_name,
                    api_key=model_cfg.api_key,
                    base_url=model_cfg.base_url,
                    mark=model_provider_cfg.mark,
                )
                final_results.append(model_cfg_with_provider)
            return final_results

    @staticmethod
    def select_one(id):
        with session_getter() as session:
            return session.query(ModelSettingCfg).filter(ModelSettingCfg.id == id).first()

    @staticmethod
    def select_one_by_model_name(model_name: str):
        with session_getter() as session:
            return session.query(ModelSettingCfg).filter(ModelSettingCfg.f_model_name == model_name).first()

    @staticmethod
    def select_one_with_provider(model_cfg_id: str):
        with session_getter() as session:
            return session.query(ModelSettingCfg.id, ModelSettingCfg.api_key, ModelSettingCfg.base_url, ModelProviderCfg.mark) \
                .join(ModelProviderCfg, ModelSettingCfg.provider_id == ModelProviderCfg.id) \
                .where(ModelSettingCfg.id == model_cfg_id) \
                .first()