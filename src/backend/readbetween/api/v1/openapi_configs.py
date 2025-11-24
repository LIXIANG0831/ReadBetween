import json
from typing import List

from fastapi import APIRouter, Query

from readbetween.models.dao.openapi_configs import OpenAPIConfigDao, OpenAPIConfig
from readbetween.models.schemas.response import ResponseModel, resp_200, resp_500, PageModel
from readbetween.models.v1.openapi import OpenAPIConfigCreateResponse, OpenAPIConfigCreateRequest, ToolInfo, \
    OpenAPIConfigInfo, OpenAPIConfigDetail
from readbetween.services.openapi_configs import OpenAPIConfigService
from readbetween.services.tasks import logger_util
from readbetween.utils.function_calling_manager import function_calling_manager

router = APIRouter(prefix="/openapi/configs", tags=["OpenAPI配置管理"])


@router.post(
    "/create",
    summary="创建OpenAPI配置",
    description="上传OpenAPI规范JSON，系统会自动解析并创建对应的API工具"
)
async def create_openapi_config(
        request: OpenAPIConfigCreateRequest
):
    """创建OpenAPI配置并解析工具"""
    try:
        logger_util.info(f"开始创建OpenAPI配置: {request.name}")

        # 调用服务层创建配置
        result = await OpenAPIConfigService.create_openapi_config(
            name=request.name,
            openapi_spec=request.openapi_spec,
            credentials=request.credentials,
            description=request.description
        )

        config = result["config"]
        base_url = result["base_url"]
        tools_count = result["tools_count"]

        # 更新FC统一工具调用器
        openapi_service_configs = {}
        all_openapi_configs: List[OpenAPIConfig] = await OpenAPIConfigDao.get_all_configs()
        for openapi_config in all_openapi_configs:
            openapi_service_configs[openapi_config.name] = {
                "openapi_spec": json.dumps(openapi_config.openapi_spec, ensure_ascii=False)
            }
        await function_calling_manager.update_openapi_services(openapi_service_configs)

        # 获取配置的所有工具信息
        tools = await OpenAPIConfigService.get_config_tools(config.id)
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

        response_data = OpenAPIConfigCreateResponse(
            config_id=config.id,
            config_name=config.name,
            base_url=base_url,
            tools_count=tools_count,
            tools=tools_info
        )

        logger_util.info(f"成功创建OpenAPI配置: {config.name}, ID: {config.id}, 工具数量: {tools_count}")
        return resp_200(response_data)

    except ValueError as e:
        # 业务逻辑错误
        logger_util.warning(f"创建OpenAPI配置业务错误: {str(e)}")
        return resp_500(400, f"创建配置失败: {str(e)}")
    except Exception as e:
        # 系统内部错误
        logger_util.error(f"创建OpenAPI配置系统错误: {str(e)}")
        return resp_500(500, f"服务器内部错误: {str(e)}")


@router.get(
    "/list",
    summary="获取所有OpenAPI配置",
    description="获取系统中所有的OpenAPI配置列表"
)
async def get_all_openapi_configs(
    page: int = None,
    size: int = None
) -> PageModel | ResponseModel:
    """获取所有OpenAPI配置"""
    try:
        if page is not None and size is not None:
            total, result = await OpenAPIConfigService.get_all_configs_with_base_url_paginated(page, size)
        else:
            total, result = await OpenAPIConfigService.get_all_configs()

        return PageModel(total=total, data=result)
    except Exception as e:
        logger_util.error(f"获取OpenAPI配置列表失败: {str(e)}")
        return resp_500(500, f"获取配置列表失败: {str(e)}")


@router.get(
    "/tools/list",
    response_model=PageModel,
    summary="获取OpenAPI配置详情",
    description="根据ID获取OpenAPI配置的详细信息"
)
async def get_openapi_config(
        config_id: str,
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(10, ge=1, le=100, description="每页大小")
) -> ResponseModel | PageModel:
    """获取OpenAPI配置详情"""
    try:
        config_info = await OpenAPIConfigService.get_config_with_base_url(config_id)
        if not config_info:
            return resp_500(404, f"未找到ID为 {config_id} 的配置")

        config = config_info["config"]
        base_url = config_info["base_url"]

        # 分页获取配置的工具
        total, tools = await OpenAPIConfigService.get_config_tools_paginated(config_id, page, size)

        config_detail = OpenAPIConfigDetail(
            id=config.id,
            name=config.name,
            description=config.description,
            base_url=base_url,
            has_credentials=bool(config.credentials),
            created_at=config.created_at,
            updated_at=config.updated_at,
            tools=tools
        )

        return PageModel(total=total, data=config_detail)

    except Exception as e:
        logger_util.error(f"获取OpenAPI配置详情失败: {str(e)}")
        return resp_500(500, f"获取配置详情失败: {str(e)}")


@router.post(
    "/delete",
    summary="删除OpenAPI配置",
    description="删除OpenAPI配置及其所有相关工具"
)
async def delete_openapi_config(config_id: str):
    """删除OpenAPI配置"""
    try:
        success = await OpenAPIConfigService.delete_config(config_id)

        if not success:
            return resp_500(404, f"未找到ID为 {config_id} 的配置")

        return resp_200({
            "config_id": config_id,
            "message": "配置删除成功"
        })

    except Exception as e:
        logger_util.error(f"删除OpenAPI配置失败: {str(e)}")
        return resp_500(500, f"删除配置失败: {str(e)}")


@router.get(
    "/{config_id}/tools",
    response_model=ResponseModel[List[ToolInfo]],
    summary="获取配置的工具列表",
    description="获取指定OpenAPI配置的所有工具列表"
)
async def get_config_tools(config_id: str) -> ResponseModel[List[ToolInfo]]:
    """获取配置的工具列表"""
    try:
        # 验证配置是否存在
        config = await OpenAPIConfigService.get_config(config_id)
        if not config:
            return resp_500(404, f"未找到ID为 {config_id} 的配置")

        tools = await OpenAPIConfigService.get_config_tools(config_id)
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

        return resp_200(tools_info)

    except Exception as e:
        logger_util.error(f"获取配置工具列表失败: {str(e)}")
        return resp_500(500, f"获取工具列表失败: {str(e)}")