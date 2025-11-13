import { request } from '@/utils/request';

/**
 * 获取OpenAPI工具列表
 * @param params - 查询参数包括page和size
 * @param options - 可选的请求配置
 * @returns Promise
 */
export async function getOpenApiConfigsList(
  params: {
    page: number;
    size: number;
  },
  options?: { [key: string]: any },
) {
  return request<Api.OpenApiConfigsList>('/api/v1/openapi/configs/list', {
    method: 'GET',
    params,
    ...(options || {}),
  });
}

/**
 * 获取OpenAPI工具详情信息
 * @param params - 查询参数包括config_id, page和size
 * @param options - 可选的请求配置
 * @returns Promise
 */
export async function getOpenApiConfigToolsList(
  params: {
    config_id: string;
    page: number;
    size: number;
  },
  options?: { [key: string]: any },
) {
  return request<Api.OpenApiConfigToolsList>('/api/v1/openapi/configs/tools/list', {
    method: 'GET',
    params,
    ...(options || {}),
  });
}

/**
 * 删除OpenAPI配置
 * @param config_id - 配置ID
 * @param options - 可选的请求配置
 * @returns Promise
 */
export async function deleteOpenApiConfig(
  config_id: string,
  options?: { [key: string]: any },
) {
  return request<any>('/api/v1/openapi/configs/delete', {
    method: 'POST',
    params: { config_id },
    ...(options || {}),
  });
}

/**
 * 创建OpenAPI配置
 * @param data - 创建配置的数据
 * @param options - 可选的请求配置
 * @returns Promise
 */
export async function createOpenApiConfig(
  data: Api.CreateOpenApiConfigData,
  options?: { [key: string]: any },
) {
  return request<Api.CreateOpenApiConfigResponse>('/api/v1/openapi/configs/create', {
    method: 'POST',
    data,
    ...(options || {}),
  });
}
