import os
import tempfile
from pathlib import Path
from typing import List

from fastapi import HTTPException, APIRouter, UploadFile, File, BackgroundTasks

from awsome.models.dao.knowledge import Knowledge
from awsome.models.dao.knowledge_file import KnowledgeFile
from awsome.models.v1.knowledge_file import KnowledgeFileExecute, KnowledgeFileVectorizeTasks
from awsome.services.tasks import celery_text_vectorize #bg_text_vectorize
from awsome.settings import get_config
from awsome.utils.minio_util import MinioUtil
from awsome.models.schemas.response import resp_200, resp_500
from awsome.utils.logger_util import logger_util
from awsome.services.knowledge_file import KnowledgeFileService
from awsome.services.knowledge import KnowledgeService
from awsome.utils.thread_pool_executor_util import ThreadPoolExecutorUtil

router = APIRouter(tags=["知识库文件管理"])

# 实例化minio
minio_client = MinioUtil()
thread_pool_util = ThreadPoolExecutorUtil()


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
        # TODO 上传前使用minio_client校验是否存在当前文件 存在则特殊处理
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
        logger_util.error(f"上传文件失败:{e}")
        return resp_500(message=str(e))


@router.post("/knowledge_file/execute")
async def execute_knowledge_file(knowledge_file_execute: KnowledgeFileExecute,
                                 background_tasks: BackgroundTasks):
    try:
        file_object_names = knowledge_file_execute.file_object_names
        target_kb_id = knowledge_file_execute.kb_id
        # 校验target_kb_id是否存在
        is_kb_exist: Knowledge = KnowledgeService.get_knowledge_by_id(target_kb_id)
        if not is_kb_exist:
            raise Exception(f"知识库{target_kb_id}不存在")
        # 上传文件列表到对应知识库
        enable_layout_flag = is_kb_exist.enable_layout
        result: List[KnowledgeFile] = KnowledgeFileService.upload_files_to_kb(file_object_names, target_kb_id)
        if knowledge_file_execute.auto is False:
            # 不进行自动解析
            # TODO 需要实现单个文件开启解析接口 同时判断是否开启布局识别
            return resp_200(result)
        else:
            # TODO auto为True 启动后台任务自动解析
            # 根据kb_id获取collection_name/index_name
            target_knowledge = KnowledgeService.get_knowledge_by_id(target_kb_id)
            target_collection_name = target_knowledge.collection_name
            target_index_name = target_knowledge.index_name

            def batch_download_files_from_minio(submit_file: KnowledgeFile):
                file_name = submit_file.name
                file_id = submit_file.id
                file_object_name = submit_file.object_name
                try:
                    file_save_path = minio_client.download_file_to_temp(file_object_name)
                    final_result = {
                        "file_save_path": file_save_path,
                        "file_name": file_name,
                        "file_id": file_id,
                        "file_object_name": file_object_name,
                    }
                    return final_result
                except Exception as e:
                    final_result = {
                        "file_save_path": "",
                        "file_name": file_name,
                        "file_id": file_id,
                        "file_object_name": file_object_name
                    }
                    logger_util.error(f"下载文件{file_id}到本地异常:{e}")
                    return final_result

            futures = []
            for file in result:
                # 提交下载任务到线程池
                future = thread_pool_util.submit_task(batch_download_files_from_minio, file)
                futures.append(future)

            thread_pool_util.wait_for_all()  # 等待任务完成

            file_info_list = []
            for future in futures:  # 收集异步执行结果
                file_info_list.append(future.result())

            # 构建后台任务所需参数
            new_task = KnowledgeFileVectorizeTasks(target_kb_id=target_kb_id,
                                                   index_name=target_index_name,
                                                   collection_name=target_collection_name,
                                                   file_info_list=file_info_list,
                                                   chunk_size=knowledge_file_execute.chunk_size,
                                                   repeat_size=knowledge_file_execute.repeat_size,
                                                   separator=knowledge_file_execute.separator,
                                                   enable_layout=enable_layout_flag)

            # Desperate 后台执行任务
            # background_tasks.add_task(bg_text_vectorize, new_task)

            # celery执行任务
            new_task_dict = new_task.dict()
            celery_text_vectorize.delay(new_task_dict)

            return resp_200(result)
    except Exception as e:
        logger_util.error(f"知识库文件解析异常:{e}")
        return resp_500(message=f"知识库文件解析异常:{e}")


@router.get("/knowledge_file/list")
async def list_knowledge_files(kb_id: str, page: int = 1, size: int = 10):
    try:
        return resp_200(KnowledgeFileService.select_files_list_by_kb_id(kb_id, page, size))
    except Exception as e:
        logger_util.error(f"查询知识库文件列表异常:{e}")
        return resp_500(message=str(e))


@router.post("/knowledge_file/delete")
async def delete_knowledge_file(id: str):
    pass
