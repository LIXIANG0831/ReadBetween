import json
from fastapi import APIRouter
from readbetween.models.schemas.response import resp_200, resp_500
from readbetween.models.v1.mcp import McpServersData, CreateMcpServerResponse
from readbetween.services.constant import RedisMCPServerKey, RedisMCPServerDetailKey
from readbetween.utils.function_calling_manager import function_calling_manager
from readbetween.utils.logger_util import logger_util
from readbetween.utils.redis_util import RedisUtil

router = APIRouter(tags=["MCP管理"])
redis_client = RedisUtil()


@router.post("/mcp/create")
async def create_mcp_server(data: McpServersData):
    try:
        # 将数据转换为 JSON 字符串
        data_json = json.dumps(data.dict(exclude_none=True), ensure_ascii=False)
        redis_client.delete(RedisMCPServerKey)
        redis_client.delete(RedisMCPServerDetailKey)

        # Deprecated 启用MCP客户端 启用统一FC客户端
        # 使用单例管理器初始化 MCP 客户端
        # mcp_client = await mcp_client_manager.initialize_client(data.dict().get("mcpServers", {}))
        # tools = await mcp_client.get_all_tools()
        # 重命名 tools 的 key
        # tools = {
        #     mcp_client.server_id_to_name.get(server_id, server_id): tool_list
        #     for server_id, tool_list in tools.items()
        # }

        # 更新FC统一工具调用器
        await function_calling_manager.update_mcp_servers(data.dict().get("mcpServers", {}))
        tool_manager = function_calling_manager.get_tool_manager()
        if tool_manager:
            # 构建与之前格式兼容的工具信息
            tools = {}
            for server_name, server_config in data.dict().get("mcpServers", {}).items():
                # 获取该服务器对应的工具
                server_tools = tool_manager.get_tools_by_sources({server_name: server_config})

                # 转换为与之前兼容的格式
                server_tool_dict = {}
                for tool_def in server_tools:
                    prefixed_name = tool_def['function']['name']
                    _, original_name = tool_manager.tool_mapping[prefixed_name]
                    server_tool_dict[original_name] = {
                        "description": tool_def['function']['description'],
                        "parameters": tool_def['function']['parameters'],
                        "prefixed_name": prefixed_name  # 使用工具名称作为 prefixed_name
                    }

                tools[server_name] = server_tool_dict

            logger_util.debug(f"工具信息:{tools}")
        else:
            tools = {}
            logger_util.info("工具管理器未初始化")

        redis_client.set(RedisMCPServerKey, data_json)
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
