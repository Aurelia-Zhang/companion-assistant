"""
文件名: api/routes/chat.py
功能: 对话相关的 API 路由
在系统中的角色:
    - 提供 HTTP API 供前端调用
    - /chat: 发送消息并获取 AI 回复
    - /history: 获取对话历史

核心逻辑:
    1. 接收前端的消息请求
    2. 调用 Agent 处理
    3. 触发信息提取
    4. 返回 AI 回复
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.agents import run_companion, get_conversation_history
from src.agents.info_extractor import process_conversation

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """聊天请求模型。"""
    message: str
    thread_id: str = "main_chat"


class ChatResponse(BaseModel):
    """聊天响应模型。"""
    response: str
    extracted_count: int = 0


class HistoryResponse(BaseModel):
    """历史记录响应模型。"""
    messages: list[dict]


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """发送消息并获取 AI 回复。"""
    try:
        # 调用 Agent
        response = run_companion(request.message, thread_id=request.thread_id)
        
        # 提取生活信息
        extracted_count = 0
        try:
            extracted_count = process_conversation(request.message, response)
        except Exception:
            pass
        
        return ChatResponse(response=response, extracted_count=extracted_count)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{thread_id}", response_model=HistoryResponse)
async def get_history(thread_id: str):
    """获取对话历史。"""
    try:
        history = get_conversation_history(thread_id)
        return HistoryResponse(messages=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 多 Agent 支持 ====================

from src.agents.multi_agent import multi_agent_chat
from src.models.agent_persona import get_all_agents


class MultiChatResponse(BaseModel):
    """多 Agent 回复模型。"""
    responses: list[dict]  # [{agent_id, agent_name, emoji, response}, ...]
    extracted_count: int = 0


class AgentInfo(BaseModel):
    """Agent 信息。"""
    id: str
    name: str
    emoji: str


@router.post("/multi", response_model=MultiChatResponse)
async def send_multi_agent(request: ChatRequest):
    """发送消息并获取多 Agent 回复。"""
    try:
        # 调用多 Agent 系统
        responses = multi_agent_chat(request.message)
        
        # 提取生活信息（使用第一个 Agent 的回复）
        extracted_count = 0
        if responses:
            try:
                extracted_count = process_conversation(
                    request.message, 
                    responses[0]["response"]
                )
            except Exception:
                pass
        
        return MultiChatResponse(responses=responses, extracted_count=extracted_count)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=list[AgentInfo])
async def list_agents():
    """获取所有可用的 Agent。"""
    agents = get_all_agents()
    return [
        AgentInfo(id=a.id, name=a.name, emoji=a.emoji)
        for a in agents
    ]
