import { request } from '@/utils/request';

/**
 * 创建新的会话。
 * @param {CreateConversationParams} data - 会话的创建参数。
 * @param {any} [options] - 可选的请求配置。
 * @returns {Promise<Api.Success>} - 成功响应。
 */
export async function createConversation(
  data: Api.CreateConversationParams,
  options?: { [key: string]: any },
) {
  return request<Api.Success>('/api/v1/conversation/create', {
    method: 'POST',
    data,
    ...(options || {}),
  });
}

/**
 * 删除指定的会话。
 * @param {DeleteConversationParams} params - 包含会话ID的参数。
 * @param {any} [options] - 可选的请求配置。
 * @returns {Promise<Api.Success>} - 成功响应。
 */
export async function deleteConversation(
  params: Api.DeleteConversationParams,
  options?: { [key: string]: any },
) {
  return request<Api.Success>('/api/v1/conversation/delete', {
    method: 'POST',
    params,
    ...(options || {}),
  });
}

/**
 * 更新指定的会话。
 * @param {UpdateConversationParams} data - 会话的更新参数。
 * @param {any} [options] - 可选的请求配置。
 * @returns {Promise<Api.Success>} - 成功响应。
 */
export async function updateConversation(
  data: Api.UpdateConversationParams,
  options?: { [key: string]: any },
) {
  return request<Api.Success>('/api/v1/conversation/update', {
    method: 'POST',
    data,
    ...(options || {}),
  });
}

/**
 * 列出所有会话。
 * @param {ListConversationsParams} [params] - 可选的分页参数。
 * @param {any} [options] - 可选的请求配置。
 * @returns {Promise<Api.Success>} - 成功响应。
 */
export async function listConversations(
  params?: Api.ListConversationsParams,
  options?: { [key: string]: any },
) {
  return request<Api.Success>('/api/v1/conversation/list', {
    method: 'GET',
    params,
    ...(options || {}),
  });
}

/**
 * 在指定的会话中发送消息。
 * @param {SendMessageParams} data - 消息的发送参数。
 * @param {any} [options] - 可选的请求配置。
 * @returns {Promise<Api.Success>} - 成功响应。
 */
export async function sendMessage(
  data: Api.SendMessageParams,
  options?: { [key: string]: any },
) {
  const apiUrl = 'http://localhost:8080/api/v1/conversation/messages/send'; // 你的 API endpoint
  const headers = {
    'Content-Type': 'application/json',
    ...(options?.headers || {}), // 合并 options 中的 headers (如果存在)
  };

  return fetch(apiUrl, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(data),
    ...(options || {}), // 合并其他 options，例如 signal, mode, 等等 (小心覆盖 fetch 的配置)
  });
}

/**
 * 获取指定会话的消息历史。
 * @param {GetMessageHistoryParams} params - 包含会话ID和可选限制的参数。
 * @param {any} [options] - 可选的请求配置。
 * @returns {Promise<Api.Success>} - 成功响应。
 */
export async function getMessageHistory(
  params: Api.GetMessageHistoryParams,
  options?: { [key: string]: any },
) {
  return request<Api.Success>('/api/v1/conversation/messages/history', {
    method: 'GET',
    params,
    ...(options || {}),
  });
}

/**
 * 清除指定会话的消息历史。
 * @param {ClearMessageHistoryParams} params - 包含会话ID的参数。
 * @param {any} [options] - 可选的请求配置。
 * @returns {Promise<Api.Success>} - 成功响应。
 */
export async function clearMessageHistory(
  params: Api.ClearMessageHistoryParams,
  options?: { [key: string]: any },
) {
  return request<Api.Success>('/api/v1/conversation/messages/clear', {
    method: 'POST',
    params,
    ...(options || {}),
  });
}

/**
 * 与模型进行对话。
 * @param {ChatRequestParams} data - 对话的参数。
 * @param {any} [options] - 可选的请求配置。
 * @returns {Promise<Api.Success>} - 成功响应。
 */
export async function chat(
  data: Api.ChatRequestParams,
  options?: { [key: string]: any },
) {
  return request<Api.Success>('/api/v1/chat', {
    method: 'POST',
    data,
    ...(options || {}),
  });
}