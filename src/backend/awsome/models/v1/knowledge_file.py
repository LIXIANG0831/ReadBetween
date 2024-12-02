from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class UploadFileInfo(BaseModel):
    file_name: str = Field(..., examples=["测试.pdf"], description="数据库保存的文件名，用于前端展示")
    object_name: str = Field(..., examples=["knowledge_file/tmp_xsad13.pdf"], description="OSS Object Name")
    file_path: str = Field(..., examples=["https://base_url:port?xxxyyyzzzz"], description="OSS 预签名URL")


class KnowledgeFileExecute(BaseModel):
    auto: bool = Field(True, examples=[True], description="是否自动开始向量化"),
    file_object_names: List[UploadFileInfo] = Field([], examples=[[UploadFileInfo(file_name="测试文档1.docs", object_name="knowledge_file/tmp_1.docs", file_path="URL"), UploadFileInfo(file_name="测试文档2.pdf", object_name="knowledge_file/tmp_2.pdf", file_path="URL")]], description="上传文件信息")
    kb_id: str = Field(..., examples=["63f2d428-af28-4977-ae68-364b9bec6d96"], description="所上传知识库主键ID")

