from typing import List

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

    @classmethod
    def select_files_list_by_kb_id(cls, kb_id: str, page: int, size: int):
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
