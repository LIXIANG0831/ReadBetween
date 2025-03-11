// @ts-ignore
/* eslint-disable */
import { request } from '@/utils/request';

export async function queryMemory(
    body: Api.queryMemoryParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/api/v1/memory/query', {
      method: 'POST',
      data: body,
      ...(options || {}),
    });
  }
