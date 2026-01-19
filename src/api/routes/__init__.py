"""
文件名: api/routes/__init__.py
功能: API 路由包初始化
"""

from src.api.routes.chat import router as chat_router
from src.api.routes.status import router as status_router
from src.api.routes.command import router as command_router

__all__ = ["chat_router", "status_router", "command_router"]
