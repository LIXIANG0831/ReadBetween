from pydantic import BaseModel, Field

from awsome.models.dao.model_cfg import ModelCfg
from awsome.models.dao.model_provider_cfg import ModelProviderCfg


class ModelCfgCreate(BaseModel):
    provider_id: str = Field(..., examples=["fe0253c8-84e8-418f-8cbf-2605ec520988"], description="模型供应商主键ID")
    # f_model_class: str = Field(..., examples=["llm"], description="模型类型llm/embedding")
    # f_model_name: str = Field(..., examples=["qwen-long"], description="模型名称")
    api_key: str = Field(..., examples=["sk-fe0253c8-84e8-418f-8cbf-2605ec520988"], description="API key")
    base_url: str = Field(..., examples=["https://dashscope.aliyuncs.com/compatible-mode/v1"], description="Base URL")


class ModelCfgSetting(BaseModel):
    model_cfg_id: str = Field(..., examples=["7168786f-96d8-4a27-9bbc-106fb2180ffd"], description="模型配置ID")
    llm_name: str = Field(..., examples=["gemini-2.0-flash-exp"], description="默认LLM模型")
    embedding_name: str = Field(..., examples=["text-embedding-004"], description="默认embedding模型")
