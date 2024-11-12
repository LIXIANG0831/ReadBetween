from pydantic import BaseModel, field_validator
from typing import Optional, List
from pydantic_core.core_schema import ValidationInfo
from awsome.db.models.base import AwsomeDBModel
from sqlalchemy import Column, String, Boolean
from sqlmodel import Field


class KnowledgeBase(AwsomeDBModel):
    __tablename__ = "knowledge"

    id: Optional[int] = Field(default=None, primary_key=True, index=True, description="主键ID")
    name: Optional[str] = Field(..., sa_column=Column(String(255), index=True), description="知识库名称")
    desc: Optional[str] = Field(default=None, sa_column=Column(String(255), index=False), description="知识库描述")
    model: Optional[str] = Field(default=None, sa_column=Column(String(255)), description="向量化模型")
    collection_name: Optional[str] = Field(default=None, sa_column=Column(String(255)), description="Collection 名称")
    index_name: Optional[str] = Field(default=None, sa_column=Column(String(255)), description="Index 名称")
    enable_layout: Optional[bool] = Field(default=False, sa_column=Column(Boolean), description="是否启用布局识别")
