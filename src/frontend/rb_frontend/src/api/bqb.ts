// @ts-ignore
/* eslint-disable */
import { request } from '@/utils/request';

/** 点踩BQB 点踩BQB GET /api/emoji/dislike */
export async function bqbDislikes(
  // 叠加生成的Param类型 (非body参数swagger默认没有生成对象)
  params: Api.bqbDislikesParams,
  options?: { [key: string]: any },
) {
  return request<Api.Success>('/api/emoji/dislike', {
    method: 'GET',
    params: {
      ...params,
    },
    ...(options || {}),
  });
}

/** 点赞BQB 点赞BQB GET /api/emoji/like */
export async function bqbLikes(
  // 叠加生成的Param类型 (非body参数swagger默认没有生成对象)
  params: Api.bqbLikesParams,
  options?: { [key: string]: any },
) {
  return request<Api.Success>('/api/emoji/like', {
    method: 'GET',
    params: {
      ...params,
    },
    ...(options || {}),
  });
}

/** 获取BQB 获取BQB GET /api/emoji/list */
export async function bqbList(
  // 叠加生成的Param类型 (非body参数swagger默认没有生成对象)
  params: Api.bqbListParams,
  options?: { [key: string]: any },
) {
  return request<any>('/api/emoji/list', {
    method: 'GET',
    params: {
      // page has a default value: 1
      page: '1',
      // size has a default value: 20
      size: '20',
      ...params,
    },
    ...(options || {}),
  });
}
