from pydantic import BaseModel
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

T = TypeVar('T')  # 定义泛型


class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""
    status_code: int
    status_message: str
    data: T = None


class PageModel(BaseModel, Generic[T]):
    """统一分页返回模型"""
    total: int
    data: T


def resp_200(data: Union[list, dict, str, Any] = None) -> ResponseModel:
    """返回成功响应"""
    return ResponseModel(status_code=200, status_message='SUCCESS', data=data)


def resp_500(code: int = 500,
             message: str = 'BAD REQUEST') -> ResponseModel:
    """返回失败响应"""
    return ResponseModel(status_code=code, status_message=message)
