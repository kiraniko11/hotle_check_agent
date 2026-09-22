"""Django项目配置"""
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
import os
import pymysql

# 启用PyMySQL作为MySQLdb兼容驱动
pymysql.install_as_MySQLdb()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent
# 先加载 .env（真实配置），再加载 .env.example（仅用于补齐缺失项）。
# 顺序不可颠倒：python-dotenv 默认不覆盖已存在的变量，
# 若先加载 .env.example，其中的值会抢占 .env，导致“改了 .env 却不生效”。
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.example")


def get_bool_env(name: str, default: bool = False) -> bool:
    """读取布尔类型环境变量"""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_list_env(name: str, default: str = "") -> list[str]:
    """读取逗号分隔的列表环境变量"""
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# 基础配置
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-this-in-production")
DEBUG = get_bool_env("DEBUG", True)
ALLOWED_HOSTS = get_list_env("ALLOWED_HOSTS", "127.0.0.1,localhost")

# 应用配置
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方应用
    "corsheaders",
    "rest_framework",
    # 自定义应用
    "accounts.apps.AccountsConfig",
    "rooms.apps.RoomsConfig",
    "feedback.apps.FeedbackConfig",
    "AiChat.apps.AiChatConfig",
    "admin_panel.apps.AdminPanelConfig",
]

# 中间件配置
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# 模板配置
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# 数据库配置
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "hotel_booking"),
        "USER": os.getenv("DB_USER", "root"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# 密码校验
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# 国际化
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# 静态文件
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# 媒体文件
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 自定义用户模型
AUTH_USER_MODEL = "accounts.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework配置
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# JWT配置
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS配置
CORS_ALLOWED_ORIGINS = get_list_env(
    "CORS_ALLOWED_ORIGINS",
    "http://127.0.0.1:5173,http://localhost:5173",
)
CORS_ALLOW_CREDENTIALS = True

# AI智能体配置（OpenAI兼容协议，可换DeepSeek、通义等任意兼容服务）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_CHAT_MODEL = os.getenv("AI_CHAT_MODEL", "deepseek-chat")
AI_CHAT_BASE_URL = os.getenv("AI_CHAT_BASE_URL", "https://api.deepseek.com")
AI_CHAT_API_KEY = os.getenv("AI_CHAT_API_KEY", "")
