// @ts-ignore
/* eslint-disable */
import { request } from '../utils/request';

/** 获取验证码 用于获取验证码 GET /api/captcha */
export async function captcha(options?: { [key: string]: any }) {
  return request<Api.SuccessStr_>('/api/captcha', {
    method: 'GET',
    ...(options || {}),
  });
}

/** 获取邮箱验证码 用于获取邮箱验证码 GET /api/email_code/${param0} */
export async function emailCode(
  // 叠加生成的Param类型 (非body参数swagger默认没有生成对象)
  params: Api.emailCodeParams,
  options?: { [key: string]: any },
) {
  const { email: param0, ...queryParams } = params;
  return request<Api.SuccessBool_>(`/api/email_code/${param0}`, {
    method: 'GET',
    params: { ...queryParams },
    ...(options || {}),
  });
}

/** 登陆 登陆后可以上传表情包 GET /api/login */
export async function login(body: Api.LoginSchema, options?: { [key: string]: any }) {
  return request<Api.SuccessJWTOutSchema_>('/api/login', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  });
}

/** 登陆 登陆后可以上传表情包 POST /api/login_email */
export async function loginEmail(body: Api.LoginEmailSchema, options?: { [key: string]: any }) {
  return request<Api.SuccessJWTOutSchema_>('/api/login_email', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  });
}

/** 验证验证码 用于验证验证码 GET /api/validate_captcha/${param0} */
export async function validateCaptcha(
  // 叠加生成的Param类型 (非body参数swagger默认没有生成对象)
  params: Api.validateCaptchaParams,
  options?: { [key: string]: any },
) {
  const { code: param0, ...queryParams } = params;
  return request<Api.SuccessUnionBool_str_>(`/api/validate_captcha/${param0}`, {
    method: 'GET',
    params: { ...queryParams },
    ...(options || {}),
  });
}

/** 验证验证码 用于验证验证码 POST /api/validate_code */
export async function validateCode(body: Api.EmailCodeSchema, options?: { [key: string]: any }) {
  return request<Api.SuccessUnionBool_str_>('/api/validate_code', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  });
}
