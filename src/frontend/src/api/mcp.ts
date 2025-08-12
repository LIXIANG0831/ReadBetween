import { request } from '@/utils/request';

/**
 * 创建MCP服务器。
 * @param {McpServersData} data - MCP服务器的创建数据。
 * @param {any} [options] - 可选的请求配置。
 * @returns {Promise<any>} - 成功响应。
 */
export async function createMcpServer(
  data: Api.McpServersData,
  options?: { [key: string]: any },
) {
  return request<any>('/api/v1/mcp/create', {
    method: 'POST',
    data,
    ...(options || {}),
  });
}

/**
 * 获取MCP服务器详细信息。
 * @param {any} [options] - 可选的请求配置。
 * @returns {Promise<any>} - 成功响应。
 */
export async function getMcpDetailInfo(
  options?: { [key: string]: any },
) {
  return request<any>('/api/v1/mcp/detail_info', {
    method: 'GET',
    ...(options || {}),
  });
}