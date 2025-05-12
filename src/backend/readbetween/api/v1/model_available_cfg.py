import copy

from readbetween.models.v1.model_available_cfg import ModelAvailableCfgAdd
from readbetween.services.model_available_cfg import ModelAvailableCfgService
from fastapi import APIRouter
from readbetween.models.schemas.response import resp_200, resp_500
from readbetween.utils.logger_util import logger_util
from readbetween.utils.tools import EncryptionTool

router = APIRouter(tags=["模型可用配置管理"])

encryption_tool = EncryptionTool()

@router.post("/model_available_cfg/add")
async def add_model_available_cfg(model_available_cfg_add: ModelAvailableCfgAdd):
    try:
        new_model_available_cfg = ModelAvailableCfgService.add_model_available_cfg(model_available_cfg_add)
        return resp_200(data=new_model_available_cfg)
    except Exception as e:
        logger_util.error(f"创建可用模型配置异常: {e}")
        return resp_500(message=str(e))


@router.post("/model_available_cfg/delete")
async def delete_model_available_cfg(id):
    try:
        return resp_200(await ModelAvailableCfgService.delete_model_available_cfg(id))
    except Exception as e:
        logger_util.error(f"删除可用模型配置异常: {e}")
        return resp_500(message=str(e))


@router.get("/model_available_cfg/list")
async def list_model_available_cfg():
    try:
        model_cfg_list = ModelAvailableCfgService.get_model_available_cfg_list()
        model_cfg_list_resp = []
        for model_cfg in model_cfg_list:
            model_cfg_copy = copy.deepcopy(model_cfg)
            # 解密
            model_cfg_copy.api_key = encryption_tool.decrypt(model_cfg.api_key)
            # 设置秘钥混淆
            model_cfg_copy.api_key = encryption_tool.obscure(model_cfg_copy.api_key)

            model_cfg_list_resp.append(model_cfg_copy)
        return resp_200(model_cfg_list_resp)
    except Exception as e:
        logger_util.error(f"获取可用模型配置列表异常: {e}")
        return resp_500(message=str(e))

