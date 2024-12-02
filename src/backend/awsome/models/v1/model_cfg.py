from pydantic import BaseModel, Field

from awsome.models.dao.model_cfg import ModelCfg
from awsome.models.dao.model_provider_cfg import ModelProviderCfg


class ModelCfgCreate(BaseModel):
    provider_id: str = Field(..., examples=["fe0253c8-84e8-418f-8cbf-2605ec520988"], description="模型供应商主键ID")
    f_model_class: str = Field(..., examples=["llm"], description="模型类型llm/embedding")
    f_model_name: str = Field(..., examples=["qwen-long"], description="模型名称")
    api_key: str = Field(..., examples=["sk-fe0253c8-84e8-418f-8cbf-2605ec520988"], description="API key")
    base_url: str = Field(..., examples=["https://dashscope.aliyuncs.com/compatible-mode/v1"], description="Base URL")


