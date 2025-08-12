// @ts-ignore
/* eslint-disable */
import { request } from '@/utils/request';

export async function getDefaultCfg(
    params?: Api.GetDefaultCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_setting_cfg/default', {
      method: 'GET',
      params,
      ...(options || {}),
    });
  }

export async function listProviders(
    params?: Api.ListProvidersParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_setting_cfg/providers', {
      method: 'GET',
      params,
      ...(options || {}),
    });
  }

export async function createModelCfg(
    data: Api.CreateModelCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_setting_cfg/create', {
      method: 'POST',
      data,
      ...(options || {}),
    });
  }

  export async function deleteModelCfg(
    params: Api.DeleteModelCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_setting_cfg/delete', {
      method: 'POST',
      params,
      ...(options || {}),
    });
  }

  export async function listModelCfg(
    params?: Api.ListModelCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_setting_cfg/list', {
      method: 'GET',
      params,
      ...(options || {}),
    });
  }

  export async function getAvailableModelCfg(
    params: Api.GetAvailableModelCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_setting_cfg/available_list', {
      method: 'GET',
      params,
      ...(options || {}),
    });
  }

  export async function setDefaultModelCfg(
    data: Api.SetDefaultModelCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_setting_cfg/setting', {
      method: 'POST',
      data,
      ...(options || {}),
    });
  }

  export async function addAvailableModelCfg(
    data: Api.addAvailableModelCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_available_cfg/add', {
      method: 'POST',
      data,
      ...(options || {}),
    });
  }

  export async function getAvailableModelCfgList(
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_available_cfg/list', {
      method: 'GET',
      ...(options || {}),
    });
  }

  export async function deleteAvailableModelCfg(
    params: Api.DeleteModelCfgParams,
    options?: { [key: string]: any },
  ) {
    return request<Api.Success>('/sys/model_available_cfg/delete', {
      method: 'POST',
      params,
      ...(options || {}),
    });
  }