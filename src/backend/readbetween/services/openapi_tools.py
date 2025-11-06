from typing import List, Optional, Dict, Any
from readbetween.core.context import async_session_getter
from readbetween.models.dao.openapi_tools import OpenAPITool, OpenAPIToolDao


class OpenAPIToolService:
    """OpenAPI工具服务"""

    @staticmethod
    async def get_all_tools() -> List[OpenAPITool]:
        """获取所有可用的工具"""
        return await OpenAPIToolDao.get_all_tools()

    @staticmethod
    async def get_tool(tool_id: str) -> Optional[OpenAPITool]:
        """获取工具详情"""
        return await OpenAPIToolDao.get_tool(tool_id)

    @staticmethod
    async def get_tools_by_config(config_id: str) -> List[OpenAPITool]:
        """获取指定配置的所有工具"""
        return await OpenAPIToolDao.get_tools_by_config(config_id)

    @staticmethod
    async def search_tools(keyword: str) -> List[OpenAPITool]:
        """搜索工具"""
        async with async_session_getter() as session:
            from sqlmodel import select
            stmt = select(OpenAPITool).where(
                OpenAPITool.name.contains(keyword) |
                OpenAPITool.description.contains(keyword)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_tool_definitions(tool_ids: List[str]) -> List[Dict[str, Any]]:
        """获取多个工具的定义（LLM格式）"""
        tools = await OpenAPIToolDao.get_tools_by_ids(tool_ids)
        return [tool.tool_definition for tool in tools]