"""用户模型"""
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    """用户管理器"""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """创建超级管理员"""
        extra_fields.setdefault("role", User.Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """自定义用户模型"""

    REQUIRED_FIELDS = ["mobile"]
    objects = UserManager()

    class Role(models.TextChoices):
        """用户角色"""
        USER = "user", "普通用户"
        ADMIN = "admin", "管理员"

    username = models.CharField("用户名", max_length=150, unique=True)
    mobile = models.CharField("手机号", max_length=11, unique=True)
    avatar = models.FileField("头像", upload_to="avatars/%Y/%m/", blank=True, default="")
    role = models.CharField("角色", max_length=20, choices=Role.choices, default=Role.USER)

    def save(self, *args, **kwargs):
        """保存用户时同步管理员权限"""
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)

    class Meta:
        db_table = "system_user"
        verbose_name = "系统用户"
        verbose_name_plural = "系统用户"
