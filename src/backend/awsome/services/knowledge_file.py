from typing import List

from awsome.models.dao.knowledge import KnowledgeDao
from awsome.models.dao.knowledge_file import KnowledgeFile
from awsome.models.v1.knowledge_file import UploadFileInfo
from awsome.services.base import BaseService
from awsome.utils.minio_util import MinioUtil
from awsome.models.dao.knowledge_file import KnowledgeFileDao

minio_client = MinioUtil()


class KnowledgeFileService(BaseService):
    """
    分页查询文件列表通过知识库ID
    """
    # TODO 数据库查询接口修改为异步
    @classmethod
    async def select_files_list_by_kb_id(cls, kb_id: str, page: int = None, size: int = None):
        if size is None and page is None:
            # 查询全部
            return KnowledgeFileDao.select_by_kb_id(kb_id)
        else:
            # 分页查询
            return KnowledgeFileDao.select_by_kb_id(kb_id, page, size)

    """
    删除文件及已向量化内容
    """
    @classmethod
    def delete_file_by_id(cls):
        # 1. 文件是否已经向量化？
        pass

    """
    开启文件向量化
    """
    @classmethod
    def start_embedding_by_id(cls):
        pass

    """
    根据知识库ID上传文件到知识库
    """
    @classmethod
    def upload_files_to_kb(cls, file_object_names: List[UploadFileInfo], target_kb_id):
        file_insert_list = []
        for file_object in file_object_names:
            kb_id = target_kb_id
            name = file_object.file_name  # 原始文件名
            md5 = minio_client.get_object_md5(file_object.object_name)
            object_name = file_object.object_name
            new_knowledge_file = KnowledgeFile(kb_id=kb_id, name=name, md5=md5, object_name=object_name)
            file_insert_list.append(new_knowledge_file)

        return KnowledgeFileDao.batch_insert(file_insert_list)

    """
    查询上传文件
    """
    @classmethod
    def select_by_file_id(cls, file_id: str):
        return KnowledgeFileDao.select_by_file_id(file_id)


    @classmethod
    def update_file(cls, file_info: KnowledgeFile):
        return KnowledgeFileDao.update_file(file_info)


    @classmethod
    async def delete_by_kb_id(cls, kb_id):
        return await KnowledgeFileDao.delete_by_kb_id(kb_id)
