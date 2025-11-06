from typing import List, Dict, Any
from readbetween.core.context import async_session_getter
from readbetween.models.dao.conversation_tool_link import ConversationToolLinkDao
from readbetween.models.dao.openapi_tools import OpenAPIToolDao
from readbetween.models.dao.conversation import Conversation


class ConversationToolLinkService:
    """会话工具绑定服务"""

    @staticmethod
    async def bind_tools_to_conversation(conversation_id: str, tool_ids: List[str]) -> Dict[str, Any]:
        """将工具绑定到会话"""
        # 验证会话存在
        async with async_session_getter() as session:
            from sqlmodel import select
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise ValueError(f"会话不存在: {conversation_id}")

        # 验证工具存在
        tools = await OpenAPIToolDao.get_tools_by_ids(tool_ids)
        if len(tools) != len(tool_ids):
            raise ValueError("部分工具不存在")

        # 绑定工具
        bindings = await ConversationToolLinkDao.create_links(conversation_id, tool_ids)

        return {
            "conversation_id": conversation_id,
            "bound_tools": len(bindings),
            "message": f"成功绑定 {len(bindings)} 个工具到会话"
        }

    @staticmethod
    async def unbind_tools_from_conversation(conversation_id: str, tool_ids: List[str]) -> Dict[str, Any]:
        """从会话解绑工具"""
        unbind_count = await ConversationToolLinkDao.delete_links(conversation_id, tool_ids)

        return {
            "conversation_id": conversation_id,
            "unbound_tools": unbind_count,
            "message": f"成功从会话解绑 {unbind_count} 个工具"
        }

    @staticmethod
    async def get_conversation_tools(conversation_id: str) -> List[Dict[str, Any]]:
        """获取会话绑定的工具列表"""
        tools = await ConversationToolLinkDao.get_conversation_tools(conversation_id)
        return [
            {
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "method": tool.method,
                "path": tool.path,
                "config_name": tool.openapi_config.name
            }
            for tool in tools
        ]

    @staticmethod
    async def get_conversation_tool_definitions(conversation_id: str) -> List[Dict[str, Any]]:
        """获取会话绑定的工具定义（LLM格式）"""
        return await ConversationToolLinkDao.get_conversation_tool_definitions(conversation_id)

    @staticmethod
    async def clear_conversation_tools(conversation_id: str) -> Dict[str, Any]:
        """清空会话的所有工具绑定"""
        delete_count = await ConversationToolLinkDao.delete_all_conversation_links(conversation_id)

        return {
            "conversation_id": conversation_id,
            "cleared_tools": delete_count,
            "message": f"成功清空 {delete_count} 个工具绑定"
        }

    @staticmethod
    async def get_available_tools_for_conversation(conversation_id: str) -> Dict[str, Any]:
        """获取会话可用的工具（已绑定和未绑定）"""
        # 获取已绑定的工具
        bound_tools = await ConversationToolLinkDao.get_conversation_tools(conversation_id)
        bound_tool_ids = {tool.id for tool in bound_tools}

        # 获取所有可用工具
        all_tools = await OpenAPIToolDao.get_all_tools()

        # 分类
        bound_tools_list = []
        available_tools_list = []

        for tool in all_tools:
            tool_info = {
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "method": tool.method,
                "path": tool.path,
                "config_name": tool.openapi_config.name
            }

            if tool.id in bound_tool_ids:
                bound_tools_list.append(tool_info)
            else:
                available_tools_list.append(tool_info)

        return {
            "bound_tools": bound_tools_list,
            "available_tools": available_tools_list,
            "total_bound": len(bound_tools_list),
            "total_available": len(available_tools_list)
        }
