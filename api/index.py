#!/usr/bin/env python3
"""
Vercel 部署入口
从父目录导入 gateway.py 的 app
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入主应用
from gateway import app

# Vercel handler
def handler(request, context=None):
    """Vercel 要求的 handler 格式"""
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest
    return app(request)
