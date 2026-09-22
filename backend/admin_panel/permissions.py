"""功能说明：管理后台的专属权限校验。"""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from accounts.models import User


class IsSystemAdmin(BasePermission):
    """功能说明：限制接口仅允许系统管理员角色访问。"""

    message = "仅系统管理员可以访问该接口。"

    def has_permission(self, request: Request, view: APIView) -> bool:
        """功能说明：判断当前请求用户是否为系统管理员。"""
        # 先确认用户已经通过 JWT 或其他认证方式登录。
        if not request.user or not request.user.is_authenticated:
            return False

        # 仅允许业务角色为 admin 的账号访问管理接口。
        return request.user.role == User.Role.ADMIN
