// @ts-ignore
/* eslint-disable */
import { request } from '@/utils/request';

export async function getDefaultCfg(
    params?: Api.GetDefaultCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_cfg/default', {
      method: 'GET',
      params,
      ...(options || {}),
    });
  }

export async function listProviders(
    params?: Api.ListProvidersParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_cfg/providers', {
      method: 'GET',
      params,
      ...(options || {}),
    });
  }

export async function createModelCfg(
    data: Api.CreateModelCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_cfg/create', {
      method: 'POST',
      data,
      ...(options || {}),
    });
  }

  export async function deleteModelCfg(
    params: Api.DeleteModelCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_cfg/delete', {
      method: 'POST',
      params,
      ...(options || {}),
    });
  }

  export async function listModelCfg(
    params?: Api.ListModelCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_cfg/list', {
      method: 'GET',
      params,
      ...(options || {}),
    });
  }

  export async function getAvailableModelCfg(
    params: Api.GetAvailableModelCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_cfg/available', {
      method: 'GET',
      params,
      ...(options || {}),
    });
  }

  export async function setDefaultModelCfg(
    data: Api.SetDefaultModelCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_cfg/setting', {
      method: 'POST',
      data,
      ...(options || {}),
    });
  }