// @ts-ignore
/* eslint-disable */
import { request } from '@/utils/request';

/** 创建知识库 Create Knowledge POST /api/v1/knowledge/create */
export async function createKnowledge(
  // 请求体参数
  body: Api.KnowledgeCreate,
  options?: { [key: string]: any },
) {
  return request<Api.Success>('/api/v1/knowledge/create', {
    method: 'POST',
    data: body,
    ...(options || {}),
  });
}

/** 删除知识库 Delete Knowledge POST /api/v1/knowledge/delete */
export async function deleteKnowledge(
  // 查询参数
  params: { id: string },
  options?: { [key: string]: any },
) {
  return request<Api.Success>('/api/v1/knowledge/delete', {
    method: 'POST',
    params: {
      ...params,
    },
    ...(options || {}),
  });
}

/** 更新知识库 Update Knowledge POST /api/v1/knowledge/update */
export async function updateKnowledge(
  // 请求体参数
  body: Api.KnowledgeUpdate,
  options?: { [key: string]: any },
) {
  return request<Api.Success>('/api/v1/knowledge/update', {
    method: 'POST',
    data: body,
    ...(options || {}),
  });
}

/** 根据 ID 获取知识库 Get Knowledge By Id GET /api/v1/knowledge/one */
export async function getKnowledgeById(
  // 查询参数
  params: { kb_id: string },
  options?: { [key: string]: any },
) {
  return request<any>('/api/v1/knowledge/one', {
    method: 'GET',
    params: {
      ...params,
    },
    ...(options || {}),
  });
}

/** 分页获取知识库列表 List Knowledge By Page GET /api/v1/knowledge/list */
export async function listKnowledge(
  // 查询参数
  params?: Api.KnowledgeListParams,
  options?: { [key: string]: any },
) {
  return request<any>('/api/v1/knowledge/list', {
    method: 'GET',
    params: {
      ...params,
    },
    ...(options || {}),
  });
}