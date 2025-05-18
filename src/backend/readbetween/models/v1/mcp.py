from typing import Dict, Any

from pydantic import BaseModel, Field


class McpServerConfig(BaseModel):
    type: str
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    url: str | None = None
    headers: dict[str, str] | None = None


class McpServersData(BaseModel):
    mcpServers: Dict[str, McpServerConfig]


class CreateMcpServerResponse(BaseModel):
    mcp_servers: Dict
    tools_detail: Dict[str, Any] | None = None
