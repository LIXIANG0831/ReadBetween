# app/models/vectorizer.py
import os
from typing import List
import torch
from modelscope import snapshot_download, Tasks
from modelscope.pipelines import pipeline
from modelscope.utils.logger import get_logger


class LocalEmbedManager:
    _instance = None
    _initialized = False

    # 单例模式
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.logger = get_logger()
            self.pipeline = None
            self._initialized = True

    def initialize(self, model_name: str, model_dir: str = "models"):
        """初始化模型（支持依赖注入）"""
        if self.pipeline:
            # self.logger.warning("模型已初始化，跳过重复加载")
            return

        os.makedirs(model_dir, exist_ok=True)
        model_path = self._prepare_model(model_name, model_dir)

        try:
            self.pipeline = pipeline(
                task=Tasks.sentence_embedding,
                model=model_path,
                device="cuda:0" if torch.cuda.is_available() else "cpu"
            )
            self.logger.info(f"模型加载成功，设备: {self.pipeline.device}")
        except Exception as e:
            self.logger.error(f"模型加载失败: {str(e)}")
            raise RuntimeError(f"模型加载失败: {str(e)}")

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

    def embed(self, inputs: List[str]) -> List[List[float]]:
        """执行向量化推理"""
        if not self.pipeline:
            raise RuntimeError("模型未初始化")

        try:
            result = self.pipeline(input={"source_sentence": inputs})
            return result["text_embedding"].tolist()
        except Exception as e:
            self.logger.error(f"推理失败: {str(e)}")
            raise RuntimeError(f"推理失败: {str(e)}")