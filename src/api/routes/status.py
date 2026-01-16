"""
文件名: api/routes/status.py
功能: 用户状态相关的 API 路由
在系统中的角色:
    - 提供状态记录和查询的 HTTP API
    - /status: 记录状态
    - /status/today: 获取今日状态
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from src.models.status import UserStatus, StatusType
from src.memory.status_store import save_status, get_today_statuses, get_recent_statuses
from src.commands import parse_and_execute

router = APIRouter(prefix="/api/status", tags=["status"])


class StatusRequest(BaseModel):
    """状态记录请求。"""
    command: str  # 如 "/wake 9:00"


class StatusResponse(BaseModel):
    """状态记录响应。"""
    success: bool
    message: str


class TodayStatusResponse(BaseModel):
    """今日状态响应。"""
    statuses: list[dict]


@router.post("/record", response_model=StatusResponse)
async def record_status(request: StatusRequest):
    """记录用户状态（通过命令）。"""
    result = parse_and_execute(request.command)
    return StatusResponse(success=result.success, message=result.message)


@router.get("/today", response_model=TodayStatusResponse)
async def get_today():
    """获取今日所有状态。"""
    statuses = get_today_statuses()
    return TodayStatusResponse(
        statuses=[
            {
                "id": s.id,
                "type": s.status_type,
                "detail": s.detail,
                "time": s.recorded_at.strftime("%H:%M"),
                "source": s.source
            }
            for s in statuses
        ]
    )
