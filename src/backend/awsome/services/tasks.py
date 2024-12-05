from awsome.models.schemas.es.save_document import SaveDocument
from awsome.models.v1.knowledge_file import KnowledgeFileVectorizeTasks
from awsome.utils.elasticsearch_util import ElasticSearchUtil
from awsome.utils.milvus_util import MilvusUtil
from awsome.utils.minio_util import MinioUtil
from awsome.utils.logger_util import logger_util
from awsome.utils.tools import PdfExtractTool
from awsome.services.constant import (milvus_default_fields,  # 默认字段
                                      milvus_default_index_params  # 默认索引配置
                                      )



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

            """
            插入ES
                - metadata
                    bbox | start_page[chunk片段最小页码] | source | title | chunk_index[分片索引] | extra | file_id | knowledge_id
                - text
            """
            for extra_result in extract_results:

                save_document = SaveDocument()

                save_document.index_name = target_index_name  # ***设置索引名称
                save_document.text = extra_result.get("chunk", "")
                save_document.metadata.bbox = extra_result.get("chunk_bboxes", "")
                save_document.metadata.start_page = extra_result.get("start_page", 0)
                save_document.metadata.source = file_object_name
                save_document.metadata.title = file_name
                save_document.metadata.chunk_index = extra_result.get("chunk_index", 0)
                save_document.metadata.extra = ""
                save_document.metadata.file_id = file_id
                save_document.metadata.knowledge_id = target_kb_id

                # 创建索引
                await es_client.insert_doc_to_index(save_document)

            """
            插入Milvus
            bbox | start_page[chunk片段最小页码] | source | title | chunk_index[分片索引] | extra | file_id | knowledge_id | text | vector | pk[auto_id]
            """
            if not milvus_client.has_collection(target_collection_name):
                logger_util.debug(f"新建集合{target_index_name}")
                milvus_client.create_collection(target_collection_name, milvus_default_fields)
                logger_util.debug(f"完成集合{target_index_name}新建")
            insert_data = [
                {
                    "bbox": str(m_extract_result.get("chunk_bboxes", "")),
                    "start_page": m_extract_result.get("start_page", 0),
                    "source": file_object_name,
                    "title": file_name,
                    "chunk_index": m_extract_result.get("chunk_index", 0),
                    "extra": "",
                    "file_id": file_id,
                    "knowledge_id": target_kb_id,
                    "text": m_extract_result.get("chunk", ""),
                    "vector": [float(i) for i in range(1024)]
                }
                for m_extract_result in extract_results
            ]
            milvus_client.insert_data(target_collection_name, insert_data)
            milvus_client.create_index_on_field(target_collection_name, "vector", milvus_default_index_params)

            # 6.完成向量化修改状态
        except Exception as e:
            # 清除ES索引
            es_client.delete_index(target_index_name)
            # 清除Milvus集合
            milvus_client.drop_collection(target_collection_name)

            file_vectorize_err_msg += f"文件{file_name}解析异常:{e}\n"
            logger_util.exception(file_vectorize_err_msg)
