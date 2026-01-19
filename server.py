"""
文件名: server.py
功能: FastAPI 服务器启动入口
在系统中的角色:
    - 启动 HTTP 服务器
    - 同时启动后台调度器
    - 运行 `uv run python server.py` 启动

核心逻辑:
    1. 启动主动消息调度器
    2. 启动 FastAPI 服务器
"""

import os
from dotenv import load_dotenv

load_dotenv()


def main():
    """启动服务器。"""
    import uvicorn
    from src.scheduler import start_scheduler
    
    # 启动后台调度器
    start_scheduler(check_interval_minutes=5)
    
    # 获取端口 (Render 通过 PORT 环境变量设置)
    port = int(os.getenv("PORT", 8000))
    
    # 生产环境禁用 reload
    is_dev = os.getenv("DEV_MODE", "false").lower() == "true"
    
    # 启动 FastAPI
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=port,
        reload=is_dev
    )


if __name__ == "__main__":
    main()
