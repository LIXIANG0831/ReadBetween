import json
from fastapi import APIRouter, HTTPException
from readbetween.models.schemas.response import resp_200, resp_500
from readbetween.models.v1.mcp import McpServersData, CreateMcpServerResponse
from readbetween.services.constant import RedisMCPServerKey, RedisMCPServerDetailKey
from readbetween.utils.logger_util import logger_util
from readbetween.utils.redis_util import RedisUtil
from readbetween.utils.mcp_client import MCPClient

router = APIRouter(tags=["MCP管理"])
redis_client = RedisUtil()


@router.post("/mcp/create")
async def create_mcp_server(data: McpServersData):
    try:
        # 将数据转换为 JSON 字符串
        data_json = json.dumps(data.dict(exclude_none=True), ensure_ascii=False)
        redis_client.delete(RedisMCPServerKey)
        redis_client.set(RedisMCPServerKey, data_json)

        mcp_client = MCPClient(data.dict().get("mcpServers", {}))
        await mcp_client.initialize_sessions()
        tools = await mcp_client.get_all_tools()
        await mcp_client.cleanup()
        redis_client.delete(RedisMCPServerDetailKey)
        redis_client.set(RedisMCPServerDetailKey, json.dumps(tools, ensure_ascii=False))

        return resp_200(data=CreateMcpServerResponse(
            mcp_servers=data.dict(exclude_none=True),
            tools_detail=tools,
        ))
    except Exception as e:
        logger_util.error(f"create_mcp_server error: {e}")
        return resp_500(message=str(e))


@router.get("/mcp/detail_info")
async def get_mcp_detail_info():
    try:
        redis_mcp_servers = redis_client.get(RedisMCPServerKey)
        redis_tools_detail = redis_client.get(RedisMCPServerDetailKey)
        if redis_mcp_servers is None or redis_tools_detail is None:
            return resp_200()

        mcp_servers_dict = json.loads(redis_mcp_servers)
        tools_detail_dict = json.loads(redis_tools_detail)

        return resp_200(data=CreateMcpServerResponse(
            mcp_servers=mcp_servers_dict,
            tools_detail=tools_detail_dict,
        ))
    except Exception as e:
        logger_util.error(f"get_mcp_detail_info error: {e}")
        return resp_500(message=str(e))
