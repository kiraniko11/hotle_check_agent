"""功能说明：提供项目通用的统一响应封装工具。"""

from rest_framework import status
from rest_framework.response import Response

DEFAULT_SUCCESS_CODE = 200


def unified_response(code: int = DEFAULT_SUCCESS_CODE, msg: str = "", data=None,
                     status_code: int | None = None) -> Response:
    """功能说明：按统一结构返回接口响应。

    响应体固定为 {"code": 业务状态码, "msg": 提示信息, "data": 业务数据}，
    默认 HTTP 状态码为 200，业务失败信息通过 code 字段表达，前端可统一处理。
    """
    http_status = status_code if status_code is not None else status.HTTP_200_OK
    return Response({"code": code, "msg": msg, "data": data}, status=http_status)


def feedback_response(code: int = DEFAULT_SUCCESS_CODE, msg: str = "", data=None,
                      status_code: int | None = None) -> Response:
    """功能说明：留言反馈模块的统一响应（与全局结构保持一致）。"""
    return unified_response(code=code, msg=msg, data=data, status_code=status_code)


def admin_response(code: int = DEFAULT_SUCCESS_CODE, msg: str = "", data=None,
                   status_code: int | None = None) -> Response:
    """功能说明：管理后台模块的统一响应（与全局结构保持一致）。"""
    return unified_response(code=code, msg=msg, data=data, status_code=status_code)
