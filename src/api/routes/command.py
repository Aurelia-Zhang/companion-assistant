"""
命令 API 路由
提供统一的命令执行接口
"""

from fastapi import APIRouter
from pydantic import BaseModel

from src.commands.command_parser import parse_and_execute

router = APIRouter(prefix="/api/command", tags=["command"])


class CommandRequest(BaseModel):
    """命令请求。"""
    command: str


class CommandResponse(BaseModel):
    """命令响应。"""
    success: bool
    message: str
    is_command: bool = True


@router.post("/execute", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """执行命令。
    
    前端发送 /xxx 命令，后端解析并执行。
    """
    result = parse_and_execute(request.command)
    return CommandResponse(
        success=result.success,
        message=result.message,
        is_command=result.is_command
    )
