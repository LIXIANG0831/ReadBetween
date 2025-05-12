import requests

from readbetween.models.dao.model_available_cfg import ModelAvailableCfgDao
from readbetween.models.v1.model_setting_cfg import ModelCfgCreate
from readbetween.services.base import BaseService
from readbetween.models.dao.model_setting_cfg import ModelSettingCfgDao
from readbetween.models.dao.model_setting_cfg import ModelSettingCfg
from readbetween.utils.tools import EncryptionTool

encryption_tool = EncryptionTool()

class ModelCfgService(BaseService):

    @classmethod
    def create_model_cfg(cls, model_cfg_create: ModelCfgCreate):
        model_cfg = ModelSettingCfg(**model_cfg_create.dict())
        return ModelSettingCfgDao.insert(model_cfg)

    @classmethod
    def delete_model_cfg(cls, id):
        # 级联删除可用模型配置
        ModelAvailableCfgDao.delete_by_setting_id(id)
        return ModelSettingCfgDao.delete_by_id(id)

    @classmethod
    def get_model_cfg(cls):
        return ModelSettingCfgDao.select_all()

    @classmethod
    def get_available_model_cfg_by_id(cls, id):
        model_cfg: ModelSettingCfg = ModelSettingCfgDao.select_one(id)
        api_key = encryption_tool.decrypt(model_cfg.api_key)
        base_url = model_cfg.base_url

        headers = {
            'Authorization': f'Bearer {api_key}'
        }

        try:
            response = requests.get(f"{base_url}/models", headers=headers)
            response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
            return response.json()  # 假设响应内容是 JSON 格式
        except requests.RequestException as e:
            print(f"请求出错：{e}")
            return None

    @classmethod
    def get_model_cfg_by_id(cls, model_cfg_id):
        return ModelSettingCfgDao.select_one_with_provider(model_cfg_id)
