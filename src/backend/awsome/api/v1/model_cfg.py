import copy
import json
from copy import deepcopy

from awsome.utils.tools import EncryptionTool
from fastapi import HTTPException, APIRouter, UploadFile, File, BackgroundTasks
from awsome.models.v1.model_cfg import ModelCfgCreate, ModelCfgSetting
from awsome.models.schemas.response import resp_200, resp_500
from awsome.utils.logger_util import logger_util
from awsome.services.model_provider_cfg import ModelProviderCfgService
from awsome.services.model_cfg import ModelCfgService
from awsome.utils.redis_util import RedisUtil

router = APIRouter(tags=["模型配置管理"])

encryption_tool = EncryptionTool()
redis_util = RedisUtil()


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
        model_cfg_create.api_key = encryption_tool.encrypt(model_cfg_create.api_key)  # 加密
        new_model_cfg = ModelCfgService.create_model_cfg(model_cfg_create)
        return resp_200(new_model_cfg)
    except Exception as e:
        logger_util.error(f"创建模型配置异常{e}")
        return resp_500(message=str(e))


@router.post("/model_cfg/delete")
async def delete_model_cfg(id):
    try:
        return resp_200(ModelCfgService.delete_model_cfg(id))
    except Exception as e:
        logger_util.error(f"删除模型配置异常{e}")
        return resp_500(message=str(e))


@router.get("/model_cfg/list")
async def list_model_cfg():
    try:
        model_cfg_list = ModelCfgService.get_model_cfg()
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
        logger_util.error(f"查询模型配置异常{e}")
        return resp_500(message=str(e))


@router.get("/model_cfg/available")
async def list_available_model_cfg(id):
    try:
        model_available = ModelCfgService.get_available_model_cfg_by_id(id)
        return resp_200(data=model_available)
    except Exception as e:
        logger_util.error(f"查询模型可用列表异常{e}")
        return resp_500(message=str(e))


@router.post("/model_cfg/setting")
async def setting_default_model_cfg(model_cfg_setting: ModelCfgSetting):
    try:
        from awsome.services.constant import redis_default_model_key
        # 拼接保存信息
        model_call_info = ModelCfgService.get_model_cfg_by_id(model_cfg_setting.model_cfg_id)
        model_info = {
            "model_cfg_id": model_call_info[0],
            "api_key": model_call_info[1],
            "base_url": model_call_info[2],
            "mark": model_call_info[3],
            "llm_name": model_cfg_setting.llm_name,
            "embedding_name": model_cfg_setting.embedding_name,
        }
        # 检查键是否存在
        if redis_util.exists(redis_default_model_key):
            # 如果键存在，先删除
            delete_result = redis_util.delete(redis_default_model_key)
            if not delete_result:
                raise HTTPException(status_code=500, detail="删除旧的模型配置失败")

        result = redis_util.set(redis_default_model_key, json.dumps(model_info))
        # 检查保存是否成功
        if not result:
            raise HTTPException(status_code=500, detail="保存模型配置到 Redis 失败")

        return resp_200(data=model_info)
    except Exception as e:
        logger_util.error(f"设置系统默认模型异常{e}")
        return resp_500(message=str(e))


@router.get("/model_cfg/default")
async def get_default_model_cfg():
    try:
        from awsome.services.constant import redis_default_model_key
        if redis_util.exists(redis_default_model_key):
            # 如果键存在，先删除
            default_model_cfg_result = redis_util.get(redis_default_model_key)
            if not default_model_cfg_result:
                raise HTTPException(status_code=500, detail="默认模型配置不存在")
            default_model_cfg_dict = json.loads(default_model_cfg_result)
            # 解密api_key
            default_model_cfg_dict["api_key"] = encryption_tool.obscure(
                encryption_tool.decrypt(
                    encrypted_password=default_model_cfg_dict["api_key"]
                )
            )
            return resp_200(data=default_model_cfg_dict)
        else:
            return resp_500(message=f"未设置默认模型配置")
    except Exception as e:
        logger_util.error(f"设置系统默认模型异常{e}")
        return resp_500(message=str(e))
