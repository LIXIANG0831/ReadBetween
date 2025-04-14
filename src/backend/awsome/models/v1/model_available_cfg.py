from pydantic import BaseModel, Field


class ModelAvailableCfgAdd(BaseModel):
    setting_id: str = Field(..., examples=["fe0253c8-84e8-418f-8cbf-2605ec520988"], description="模型供应商主键ID")
    # f_model_class: str = Field(..., examples=["llm"], description="模型类型llm/embedding")
    # f_model_name: str = Field(..., examples=["qwen-long"], description="模型名称")
    type: str = Field(..., examples=["llm"], description="模型类型")
    name: str = Field(..., examples=["qwen2.5-72b-instruct"], description="模型名称")


class ModelAvailableCfgInfo(BaseModel):
    type: str = Field(..., examples=["llm"], description="模型类型")
    name: str = Field(..., examples=["qwen2.5-72b-instruct"], description="模型名称")
    api_key: str = Field(..., examples=["sk-fe0253c8-84e8-418f-8cbf-2605ec520988"], description="API key")
    base_url: str = Field(..., examples=["https://dashscope.aliyuncs.com/compatible-mode/v1"], description="Base URL")
    mark: str = Field(..., examples=["openai"], description="供应商标识")
