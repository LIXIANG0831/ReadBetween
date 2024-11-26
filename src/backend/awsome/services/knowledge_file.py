from awsome.services.base import BaseService
class KnowledgeFileService(BaseService):

    """
    查询文件列表通过知识库ID
    """
    @classmethod
    def select_file_list_by_kb_id(cls):
        pass

    """
    删除文件及已向量化内容
    """
    @classmethod
    def delete_file_by_id(cls):
        # 1. 文件是否已经向量化？
        pass

    """
    根据知识库ID上传文件到知识库
    """
    @classmethod
    def upload_file_to_kb(cls):
        pass

    """
    开启文件向量化
    """
    @classmethod
    def start_embedding_by_id(cls):
        pass