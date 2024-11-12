from awsome.models.dao.access_log import AccessLogDao
from fastapi import Request


async def log_access(request: Request, call_next):
    """
    Logs access to the given IP address and path.
    """
    ip_address = request.client.host
    method = request.method
    path = request.url.path

    # 过滤无需记录路径
    filter_path_list = ['/docs', '/favicon.ico', '/openapi.json', '/health']
    for filter_path in filter_path_list:
        if path.startswith(f"{filter_path}"):
            return await call_next(request)

    AccessLogDao.insert(ip_address, method, path)  # 记录信息到数据库

    response = await call_next(request)
    return response
