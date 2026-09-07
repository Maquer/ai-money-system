#!/usr/bin/env python3
"""
Vercel 部署入口 - 适配 Serverless
原 gateway.py 的所有功能，但用 Vercel 的 handler 接口
"""
import sys
import os
from pathlib import Path

# Vercel 环境
sys.path.insert(0, os.path.dirname(__file__))

# 复用 gateway.py 的 app
from gateway import app

# Vercel 要求的 handler
def handler(request, context=None):
    return app(request.scope, request.receive, request.send)
