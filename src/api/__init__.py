"""
文件名: api/__init__.py
功能: API 包初始化，创建 FastAPI 应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from src.api.routes import chat_router, status_router, command_router
from src.api.routes.push import router as push_router
from src.api.routes.upload import router as upload_router


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例。"""
    app = FastAPI(
        title="AI 陪伴助手 API",
        description="提供对话、状态记录等功能的 API",
        version="1.2.6"
    )
    
    # 配置 CORS（允许前端跨域访问）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 开发环境允许所有来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(chat_router)
    app.include_router(status_router)
    app.include_router(push_router)
    app.include_router(command_router)
    app.include_router(upload_router)
    
    # 静态文件（前端）- 直接使用 frontend 目录
    frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend")
    if os.path.exists(frontend_path):
        app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
    
    return app


app = create_app()
