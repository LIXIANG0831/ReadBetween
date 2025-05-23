import axios from 'axios';
import { ElMessage } from 'element-plus';

import { get } from 'lodash-es';

/** 创建请求实例 */
function createService() {
  // 创建一个 axios 实例命名为 service
  const service = axios.create({
    // baseURL: 'https://emoji.just4dream.club',
    baseURL: import.meta.env.VITE_BACKEND_URL,
    timeout: 50000,
    headers: { 'Content-Type': 'application/json' },
  });
  // 请求拦截
  service.interceptors.request.use(
    (config) => config,
    // 发送失败
    (error) => Promise.reject(error),
  );
  // 响应拦截（可根据具体业务作出相应的调整）
  service.interceptors.response.use(
    (response) => {
      // apiData 是 api 返回的数据
      const apiData = response.data;
      // 二进制数据则直接返回
      const responseType = response.request?.responseType;
      if (responseType === 'blob' || responseType === 'arraybuffer') return apiData;
      // 这个 code 是和后端约定的业务 code
      const code = apiData.status_code;
      // 如果没有 code, 代表这不是项目后端开发的 api
      if (code === undefined) {
        // 流式接口的特殊处理
        if (response.status === 200){
          return response;
        }
        else{
          ElMessage.error('非本系统的接口');
          return Promise.reject(new Error('非本系统的接口'));
        }
      }
      switch (code) {
        case 200:
          // 业务正常
          return response;
        default:
          // 不是正确的 code
          ElMessage.error(apiData.status_message || 'Error');
          return Promise.reject(new Error('Error'));
      }
    },
    (error) => {
      // status 是 HTTP 状态码
      const status = get(error, 'response.status');
      switch (status) {
        case 400:
          error.message = '请求错误';
          break;
        case 403:
          error.message = '拒绝访问';
          break;
        case 404:
          error.message = '请求地址出错';
          break;
        case 408:
          error.message = '请求超时';
          break;
        case 500:
          error.message = '服务器内部错误';
          break;
        case 501:
          error.message = '服务未实现';
          break;
        case 502:
          error.message = '网关错误';
          break;
        case 503:
          error.message = '服务不可用';
          break;
        case 504:
          error.message = '网关超时';
          break;
        case 505:
          error.message = 'HTTP 版本不受支持';
          break;
        default:
          break;
      }
      ElMessage.error(error.message);
      return Promise.reject(error);
    },
  );
  return service;
}

export const request = createService();
