// @ts-ignore
/* eslint-disable */
import { request } from '@/utils/request';

/** 上传知识库文件 Upload Knowledge File POST /api/v1/knowledge_file/upload */
export async function uploadKnowledgeFile(
    // 请求体参数
    data: Api.UploadKnowledgeFileParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/api/v1/knowledge_file/upload', {
      method: 'POST',
      data,
      headers: {
        'Content-Type': 'multipart/form-data', // 显式设置请求头
      },
      ...(options || {}),
    });
  }

  /** 执行知识库文件 Execute Knowledge File POST /api/v1/knowledge_file/execute */
export async function executeKnowledgeFile(
    // 请求体参数
    data: Api.ExecuteKnowledgeFileParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/api/v1/knowledge_file/execute', {
      method: 'POST',
      data,
      ...(options || {}),
    });
  }

  /** 列出知识库文件 List Knowledge Files GET /api/v1/knowledge_file/list */
export async function listKnowledgeFiles(
    // 查询参数
    params: Api.ListKnowledgeFilesParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/api/v1/knowledge_file/list', {
      method: 'GET',
      params: {
        ...params,
      },
      ...(options || {}),
    });
  }

  /** 删除知识库文件 Delete Knowledge File POST /api/v1/knowledge_file/delete */
export async function deleteKnowledgeFile(
    // 查询参数
    params: Api.DeleteKnowledgeFileParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/api/v1/knowledge_file/delete', {
      method: 'POST',
      params: {
        ...params,
      },
      ...(options || {}),
    });
  }