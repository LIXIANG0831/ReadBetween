from typing import List, Optional, Dict, Any
from readbetween.models.dao.openapi_configs import OpenAPIConfig, OpenAPIConfigDao
from readbetween.models.dao.openapi_tools import OpenAPITool, OpenAPIToolDao
from readbetween.models.v1.openapi import OpenAPIConfigInfo, ToolInfo
from readbetween.utils.logger_util import logger_util
from openapi_spec_validator import validate
from openapi_llm.client.config import create_client_config


class OpenAPIConfigService:
    """OpenAPI配置服务"""

    @staticmethod
    async def create_openapi_config(
            name: str,
            openapi_spec: Dict[str, Any],
            credentials: Optional[str] = None,
            description: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建OpenAPI配置并解析工具"""
        try:
            # 验证OpenAPI规范
            validate(openapi_spec)
        except Exception as e:
            logger_util.error(f"OpenAPI Schema 异常: {e}")
            raise ValueError(f"OpenAPI Schema 异常: {str(e)}")
        try:

            # 从 spec 中提取 base_url
            base_url = OpenAPIConfigService._extract_base_url(openapi_spec)
            if not base_url:
                raise ValueError("无法从OpenAPI规范中提取有效的base_url")

            logger_util.info(f"从OpenAPI规范提取base_url: {base_url}")

            # 创建配置
            config = await OpenAPIConfigDao.create_config(
                name=name,
                openapi_spec=openapi_spec,
                credentials=credentials,
                description=description
            )

            # 解析并创建工具
            tools_count = await OpenAPIConfigService._parse_and_create_tools(config.id, openapi_spec)

            return {
                "config": config,
                "base_url": base_url,
                "tools_count": tools_count,
                "message": f"成功创建OpenAPI配置，解析出 {tools_count} 个工具"
            }

        except Exception as e:
            logger_util.error(f"创建OpenAPI配置失败: {e}")
            raise ValueError(f"创建OpenAPI配置失败: {str(e)}")

    @staticmethod
    def _extract_base_url(openapi_spec: Dict[str, Any]) -> Optional[str]:
        """从OpenAPI规范中提取base_url"""
        try:
            # 方法1: 从 servers 字段获取
            servers = openapi_spec.get('servers', [])
            if servers:
                server_url = servers[0].get('url', '')
                if server_url:
                    # 处理变量替换
                    server_url = OpenAPIConfigService._resolve_server_url(server_url, servers[0])
                    return server_url.rstrip('/')

            # 方法2: 从 host, basePath 等旧版本字段获取 (OpenAPI 2.0)
            host = openapi_spec.get('host')
            if host:
                schemes = openapi_spec.get('schemes', ['https'])
                base_path = openapi_spec.get('basePath', '')
                return f"{schemes[0]}://{host}{base_path}".rstrip('/')

            # 方法3: 如果都没有，尝试从info.title生成一个测试URL（不推荐）
            logger_util.warning("无法从OpenAPI规范中提取base_url，使用默认值")
            return None

        except Exception as e:
            logger_util.error(f"提取base_url失败: {e}")
            return None

    @staticmethod
    def _resolve_server_url(server_url: str, server_info: Dict[str, Any]) -> str:
        """解析服务器URL中的变量"""
        try:
            # 处理变量替换，例如 {version} -> v1
            variables = server_info.get('variables', {})
            for var_name, var_config in variables.items():
                default_value = var_config.get('default', '')
                if f"{{{var_name}}}" in server_url:
                    server_url = server_url.replace(f"{{{var_name}}}", default_value)
            return server_url
        except Exception as e:
            logger_util.warning(f"解析服务器URL变量失败: {e}")
            return server_url

    @staticmethod
    async def _parse_and_create_tools(config_id: str, openapi_spec: Dict[str, Any]) -> int:
        """解析OpenAPI规范并创建工具"""
        try:
            # 使用openapi-llm解析工具定义
            config = create_client_config(openapi_spec.__str__())
            tool_definitions = config.get_tool_definitions()

            tools_data = []
            for tool_def in tool_definitions:
                if isinstance(tool_def, dict) and 'function' in tool_def:
                    tool_name = tool_def['function'].get('name', '')
                    method, path = OpenAPIConfigService._extract_method_and_path(tool_name, openapi_spec)

                    tools_data.append({
                        "openapi_config_id": config_id,
                        "name": tool_name,
                        "description": tool_def['function'].get('description', ''),
                        "method": method,
                        "path": path,
                        "parameters": tool_def['function'].get('parameters', []),
                        "tool_definition": tool_def
                    })

            # 批量创建工具
            if tools_data:
                tools = await OpenAPIToolDao.batch_create_tools(tools_data)
                return len(tools)
            return 0

        except Exception as e:
            logger_util.error(f"解析OpenAPI工具失败: {e}")
            raise ValueError(f"解析OpenAPI工具失败: {str(e)}")

    @staticmethod
    def _extract_method_and_path(tool_name, openapi_spec: Dict[str, Any]) -> tuple[str, str]:
        """OpenAPI规范中提取HTTP方法和路径"""
        try:
            paths = openapi_spec.get('paths', {})
            for path, methods in paths.items():
                if not isinstance(methods, dict):
                    continue
                for method, operation in methods.items():
                    if isinstance(operation, dict) and operation.get('operationId') == tool_name:
                        return method.upper(), path
        except Exception as e:
            print(f"提取方法和路径失败: {e}")
            return "POST", "/unknown"

    @staticmethod
    async def get_config_with_base_url(config_id: str) -> Optional[Dict[str, Any]]:
        """获取OpenAPI配置及其base_url"""
        config = await OpenAPIConfigDao.get_config(config_id)
        if not config:
            return None

        base_url = OpenAPIConfigService._extract_base_url(config.openapi_spec)

        return {
            "config": config,
            "base_url": base_url
        }

    @staticmethod
    async def get_all_configs_with_base_url() -> List[Dict[str, Any]]:
        """获取所有OpenAPI配置及其base_url"""
        configs = await OpenAPIConfigDao.get_all_configs()

        result = []
        for config in configs:
            base_url = OpenAPIConfigService._extract_base_url(config.openapi_spec)
            result.append({
                "config": config,
                "base_url": base_url
            })

        return result

    @staticmethod
    async def get_config(config_id: str) -> Optional[OpenAPIConfig]:
        """获取OpenAPI配置"""
        return await OpenAPIConfigDao.get_config(config_id)

    @staticmethod
    async def get_all_configs() -> tuple[Any, List[OpenAPIConfig]]:
        """获取所有OpenAPI配置"""
        total = await OpenAPIConfigDao.get_all_configs_total()
        all_openapi_configs = await OpenAPIConfigDao.get_all_configs()
        result = [
            OpenAPIConfigInfo(
                id=openapi_config.id,
                name=openapi_config.name,
                description=openapi_config.description,
                # base_url=openapi_config.
                tools_count=len(openapi_config.tools),
                has_credentials=bool(openapi_config.credentials),
                created_at=openapi_config.created_at,
                updated_at=openapi_config.updated_at
            )
            for openapi_config in all_openapi_configs
        ]
        OpenAPIConfigInfo
        return total, result

    @staticmethod
    async def update_config(
            config_id: str,
            name: Optional[str] = None,
            credentials: Optional[str] = None,
            description: Optional[str] = None
    ) -> Optional[OpenAPIConfig]:
        """更新OpenAPI配置"""
        return await OpenAPIConfigDao.update_config(
            config_id=config_id,
            name=name,
            credentials=credentials,
            description=description
        )

    @staticmethod
    async def delete_config(config_id: str) -> bool:
        """删除OpenAPI配置（级联删除相关工具）"""
        return await OpenAPIConfigDao.delete_config(config_id)

    @staticmethod
    async def get_config_tools(config_id: str) -> List[OpenAPITool]:
        """获取配置的所有工具"""
        return await OpenAPIToolDao.get_tools_by_config(config_id)

    @staticmethod
    async def get_all_configs_with_base_url_paginated(
            page: int,
            size: int
    ) -> tuple[Any, list[OpenAPIConfigInfo]]:
        """获取分页的OpenAPI配置及其base_url"""
        try:
            # 获取分页配置
            paginated_result = await OpenAPIConfigDao.get_configs_paginated(page, size)

            configs = paginated_result["configs"]
            total = paginated_result["total"]

            result_configs = []
            for config in configs:
                base_url = OpenAPIConfigService._extract_base_url(config.openapi_spec)
                tools = await OpenAPIConfigService.get_config_tools(config.id)

                result_configs.append(OpenAPIConfigInfo(
                    id=config.id,
                    name=config.name,
                    description=config.description,
                    base_url=base_url,
                    tools_count=len(tools),
                    has_credentials=bool(config.credentials),
                    created_at=config.created_at,
                    updated_at=config.updated_at
                ))

            return total, result_configs

        except Exception as e:
            logger_util.error(f"获取分页OpenAPI配置失败: {e}")
            raise ValueError(f"获取配置列表失败: {str(e)}")

    @staticmethod
    async def get_config_tools_paginated(
            config_id: str,
            page: int = 1,
            size: int = 20
    ) -> tuple[Any, list[ToolInfo]]:
        """获取配置的分页工具列表"""
        try:
            # 验证配置是否存在
            config = await OpenAPIConfigDao.get_config(config_id)
            if not config:
                raise ValueError(f"未找到ID为 {config_id} 的配置")

            # 获取分页工具
            paginated_result = await OpenAPIToolDao.get_tools_by_config_paginated(
                config_id=config_id,
                page=page,
                size=size
            )

            tools = paginated_result["tools"]
            total = paginated_result["total"]

            # 获取配置的所有工具
            tools_info = [
                ToolInfo(
                    id=tool.id,
                    name=tool.name,
                    description=tool.description,
                    method=tool.method,
                    path=tool.path,
                    created_at=tool.created_at
                )
                for tool in tools
            ]

            return total, tools_info

        except ValueError:
            raise
        except Exception as e:
            logger_util.error(f"获取配置工具分页列表失败: {e}")
            raise ValueError(f"获取工具列表失败: {str(e)}")