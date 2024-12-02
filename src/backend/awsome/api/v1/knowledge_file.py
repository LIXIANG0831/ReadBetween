import os
import tempfile
from pathlib import Path
from fastapi import HTTPException, APIRouter, UploadFile, File, BackgroundTasks
from awsome.models.v1.knowledge_file import KnowledgeFileExecute
from awsome.settings import get_config
from awsome.utils.minio_util import MinioUtil
from awsome.models.schemas.response import resp_200, resp_500
from awsome.utils.logger_util import logger_util
from awsome.services.knowledge_file import KnowledgeFileService
from awsome.services.knowledge import KnowledgeService
# 实例化minio
minio_client = MinioUtil()
router = APIRouter(tags=["知识库文件管理"])


@router.post("/knowledge_file/upload")
async def upload_knowledge_file(file: UploadFile = File(...)):
    try:
        default_bucket_name = get_config("storage.minio.default_bucket")
        if minio_client.bucket_exists(default_bucket_name) is False:  # 检查桶存在
            minio_client.create_bucket(default_bucket_name)

        file_name = file.filename  # 文件名
        ext = Path(file_name).suffix  # 获取带点文件后缀

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)  # 临时保存文件
        tmp_file.write(await file.read())
        tmp_file.close()
        tmp_file_path = tmp_file.name

        if os.path.getsize(tmp_file_path) == 0:
            raise ValueError("临时文件为空，无法上传。")

        tmp_file_name = Path(tmp_file_path).name
        object_name = f"knowledge_file/{tmp_file_name}"
        minio_client.upload_file(tmp_file_path, object_name)

        os.remove(tmp_file_path)  # 删除临时文件

        file_path = minio_client.get_presigned_url(object_name)

        upload_file_info = {
            "file_name": file_name,
            "object_name": object_name,
            "file_path": file_path
        }

        return resp_200(data=upload_file_info)
    except Exception as e:
        logger_util.error(f"上传文件失败: {e}")
        return resp_500(message=str(e))


@router.post("/knowledge_file/execute")
async def execute_knowledge_file(knowledge_file_execute: KnowledgeFileExecute,
                                 background_tasks: BackgroundTasks):

    file_object_names = knowledge_file_execute.file_object_names
    target_kb_id = knowledge_file_execute.kb_id
    if knowledge_file_execute.auto is False:
        # 不进行自动解析
        # TODO 需要实现单个文件开启解析接口
        return resp_200(KnowledgeFileService.upload_files_to_kb(file_object_names, target_kb_id))
    else:
        # TODO auto为True 启动后台任务自动解析
        background_tasks.add_task()
        # 1.找到kb_id对应collection_name
        # 2.自身切片
        # 3.自身向量化 组织数据结构
        # 4.插入milvus
        pass


@router.get("/knowledge_file/list")
async def list_knowledge_files(kb_id: str, page: int = 1, size: int = 10):
    try:
        return resp_200(KnowledgeFileService.select_files_list_by_kb_id(kb_id, page, size))
    except Exception as e:
        logger_util.error(f"查询知识库文件列表异常: {e}")
        return resp_500(message=str(e))


@router.post("/knowledge_file/delete")
async def delete_knowledge_file(id: str):
    pass