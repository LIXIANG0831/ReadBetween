from pydantic import BaseModel, Field


class ModelAvailableCfgAdd(BaseModel):
    setting_id: str = Field(..., examples=["fe0253c8-84e8-418f-8cbf-2605ec520988"], description="模型供应商主键ID")
    # f_model_class: str = Field(..., examples=["llm"], description="模型类型llm/embedding")
    # f_model_name: str = Field(..., examples=["qwen-long"], description="模型名称")
    type: str = Field(..., examples=["llm"], description="模型类型")
    name: str = Field(..., examples=["qwen2.5-72b-instruct"], description="模型名称")
