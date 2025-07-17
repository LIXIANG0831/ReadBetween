import os
from huggingface_hub import snapshot_download
from huggingface_hub.utils.logging import get_logger


class LocalSTTManager:
    _initialized = False

    def __init__(self):
        if not self._initialized:
            self.logger = get_logger()
            self._initialized = True

    def _prepare_model(self, model_name: str, model_dir: str) -> str:
        """准备模型文件，返回本地路径"""
        model_path = os.path.join(model_dir, model_name)

        if not os.path.exists(model_path):
            self.logger.info(f"开始下载模型: {model_name}")
            try:
                model_path = snapshot_download(
                    model_name,
                    cache_dir=model_dir,
                    revision="master"
                )
                self.logger.info(f"模型下载完成: {model_path}")
            except Exception as e:
                self.logger.error(f"模型下载失败: {str(e)}")
                raise RuntimeError(f"模型下载失败: {str(e)}")
        return model_path

    def initialize(self, model_name: str, model_dir: str = "models"):
        os.makedirs(model_dir, exist_ok=True)
        model_path = self._prepare_model(model_name, model_dir)
