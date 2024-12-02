from awsome.utils.tools import EncryptionTool
from fastapi import HTTPException, APIRouter, UploadFile, File, BackgroundTasks
from awsome.models.v1.model_cfg import ModelCfgCreate
from awsome.models.schemas.response import resp_200, resp_500
from awsome.utils.logger_util import logger_util
from awsome.services.model_provider_cfg import ModelProviderCfgService
from awsome.services.model_cfg import ModelCfgService

router = APIRouter(tags=["模型配置管理"])


@router.get("/model_cfg/providers")
async def get_model_cfg_providers():
    try:
        providers = ModelProviderCfgService.select_providers()
        return resp_200(providers)
    except Exception as e:
        logger_util.error(f"获取模型供应商异常{e}")
        return resp_500(message=str(e))


@router.post("/model_cfg/create")
async def create_model_cfg(model_cfg_create: ModelCfgCreate):
    try:
        model_cfg_create.api_key = EncryptionTool.decrypt(model_cfg_create.api_key) # 加密
        new_model_cfg = ModelCfgService.create_model_cfg(model_cfg_create)
        return resp_200(new_model_cfg)
    except Exception as e:
        logger_util.error(f"创建模型配置异常{e}")
        return resp_500(message=str(e))


@router.post("/model_cfg/delete")
async def create_model_cfg(id):
    try:
        return resp_200(ModelCfgService.delete_model_cfg(id))
    except Exception as e:
        logger_util.error(f"删除模型配置异常{e}")
        return resp_500(message=str(e))

@router.get("/model_cfg/list")
async def create_model_cfg():
    try:
        model_cfg_list = ModelCfgService.get_model_cfg()
        return resp_200(model_cfg_list)
    except Exception as e:
        logger_util.error(f"查询模型配置异常{e}")
        return resp_500(message=str(e))