# schemas/openapi_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class OpenAPIConfigCreateRequest(BaseModel):
    """创建OpenAPI配置请求"""
    name: str = Field(..., description="配置名称", min_length=1, max_length=255)
    openapi_spec: Dict[str, Any] = Field(..., description="OpenAPI规范JSON")
    credentials: Optional[str] = Field(None, description="认证凭据")
    description: Optional[str] = Field(None, description="描述")


class ToolInfo(BaseModel):
    """工具信息"""
    id: str = Field(..., description="工具ID")
    name: str = Field(..., description="工具名称")
    description: Optional[str] = Field(None, description="工具描述")
    method: str = Field(..., description="HTTP方法")
    path: str = Field(..., description="API路径")
    created_at: Optional[datetime] = Field(None, description="创建时间")


class OpenAPIConfigInfo(BaseModel):
    """OpenAPI配置信息"""
    id: str = Field(..., description="配置ID")
    name: str = Field(..., description="配置名称")
    description: Optional[str] = Field(None, description="描述")
    base_url: Optional[str] = Field(None, description="基础URL")
    tools_count: int = Field(..., description="工具数量")
    has_credentials: bool = Field(..., description="是否有认证凭据")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class OpenAPIConfigDetail(BaseModel):
    """OpenAPI配置详情"""
    id: str = Field(..., description="配置ID")
    name: str = Field(..., description="配置名称")
    description: Optional[str] = Field(None, description="描述")
    base_url: Optional[str] = Field(None, description="基础URL")
    has_credentials: bool = Field(..., description="是否有认证凭据")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    tools: List[ToolInfo] = Field(..., description="工具列表")


class OpenAPIConfigCreateResponse(BaseModel):
    """创建OpenAPI配置响应数据"""
    config_id: str = Field(..., description="配置ID")
    config_name: str = Field(..., description="配置名称")
    base_url: Optional[str] = Field(None, description="基础URL")
    tools_count: int = Field(..., description="工具数量")
    tools: List[ToolInfo] = Field(..., description="工具列表")