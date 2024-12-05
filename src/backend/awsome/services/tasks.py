from awsome.models.v1.knowledge_file import KnowledgeFileVectorizeTasks
from awsome.utils.elasticsearch_util import ElasticSearchUtil
from awsome.utils.milvus_util import MilvusUtil
from awsome.utils.minio_util import MinioUtil
from awsome.utils.logger_util import logger_util
from awsome.utils.tools import PdfExtractTool


async def bg_text_vectorize(knowledge_file_vectorize_task: KnowledgeFileVectorizeTasks):
    file_vectorize_err_msg = ""  # 记录异常信息
    try:
        # 实例化minio_client
        minio_client = MinioUtil()
        # 实例化milvus
        milvus_client = MilvusUtil()
        # 实例化es
        es_client = ElasticSearchUtil()
    except Exception as e:
        file_vectorize_err_msg += f"实例化异常:{e}\n"
        logger_util.exception(file_vectorize_err_msg)

    target_kb_id = knowledge_file_vectorize_task.target_kb_id  # target_knowledge_id
    target_collection_name = knowledge_file_vectorize_task.collection_name  # milvus_collection_name
    target_index_name = knowledge_file_vectorize_task.index_name  # es_index_name
    enable_layout_flag = knowledge_file_vectorize_task.enable_layout  # 是否开启布局识别

    for file_info in knowledge_file_vectorize_task.file_info_list:
        file_save_path = file_info["file_save_path"]
        file_name = file_info["file_name"]
        file_id = file_info["file_id"]
        file_object_name = file_info["file_object_name"]
        try:
            if file_save_path == "": raise Exception("文件下载失败")

            # TODO 没有对separator进行支持
            # 文档切片向量化 组织数据结构
            extract_results = []
            if enable_layout_flag == 1:  # 布局识别
                pass
            elif enable_layout_flag == 0:  # 不进行布局识别
                # 实例化pdf工具
                pdf_extractor = PdfExtractTool(file_save_path,
                                               chunk_size=knowledge_file_vectorize_task.chunk_size,
                                               repeat_size=knowledge_file_vectorize_task.repeat_size)
                extract_results = await pdf_extractor.extract()  # pdf切片结果返回

            # TODO 组织ES结果创建索引插入
            """
            插入ES
                - metadata
                    bbox | start_page[chunk片段最小页码] | source | title | chunk_index | extra | file_id | knowledge_id
                - text
            """

            """
            插入Milvus
            bbox | start_page[chunk片段最小页码] | source | title | chunk_index | extra | field_id | knowledge_id | text | vector | pk[auto_id]
            """

            # 6.完成向量化修改状态
        except Exception as e:
            file_vectorize_err_msg += f"文件{file_name}解析异常:{e}\n"
            logger_util.exception(file_vectorize_err_msg)
