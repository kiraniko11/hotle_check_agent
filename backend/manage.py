#!/usr/bin/env python
"""Django项目管理入口"""
import os
import sys


def main():
    """执行Django管理命令"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("无法导入Django，请确认已安装依赖") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
