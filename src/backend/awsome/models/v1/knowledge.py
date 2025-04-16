from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from awsome.models.dao import Knowledge
from awsome.models.v1.model_available_cfg import ModelAvailableCfgInfo


class KnowledgeCreate(BaseModel):
    name: str = Field(..., examples=["新建知识库1"], description="知识库名称")
    desc: str = Field(None, examples=["知识库描述信息"], description="知识库描述信息")
    available_model_id: str = Field(None, examples=["xxx-xxx-xxx-xxx"],
                                    description="可用向量化模型ID，None时使用系统内置模型")
    collection_name: str = Field(None, examples=[""], description="collection名称")
    index_name: str = Field(None, examples=[""], description="index名称")
    enable_layout: int = Field(0, examples=[0], description="是否开启布局识别")


class KnowledgeUpdate(BaseModel):
    id: str = Field(..., description="主键ID")
    name: str = Field(None, examples=["新名称1"], description="新更新知识库名称")
    desc: str = Field(None, examples=["新描述1"], description="新更新知识库描述")


class KnowledgeInfo(BaseModel):
    knowledge: Knowledge = Field(..., description="知识库")
    model_cfg: ModelAvailableCfgInfo = Field(..., description="当前会话渠道模型配置")
