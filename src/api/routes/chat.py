"""
文件名: api/routes/chat.py
功能: 对话相关的 API 路由 (v1.2 统一版本)
在系统中的角色:
    - 提供 HTTP API 供前端调用
    - 统一使用 chat_manager 处理所有聊天请求
    - 支持私聊和群聊

核心逻辑:
    1. 接收前端的消息请求
    2. 使用 chat_manager 处理（支持 per-agent 配置）
    3. 触发信息提取
    4. 返回 AI 回复
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from src.agents.chat_manager import get_chat_manager
from src.agents.info_extractor import process_conversation
from src.models.agent_persona import get_all_agents, get_default_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ==================== Request/Response Models ====================

class ChatRequest(BaseModel):
    """聊天请求模型。"""
    message: str
    session_id: Optional[str] = None  # 如果不传，使用当前活跃会话或创建新会话
    agent_ids: Optional[List[str]] = None  # 如果传入，指定要对话的 Agent


class ChatResponse(BaseModel):
    """聊天响应模型。"""
    responses: List[dict]  # [{agent_id, agent_name, content, timestamp}, ...]
    session_id: str
    extracted_count: int = 0


class SessionInfo(BaseModel):
    """会话信息。"""
    id: str
    type: str  # "private" or "group"
    agents: List[str]
    title: str
    updated_at: str


class AgentInfo(BaseModel):
    """Agent 信息。"""
    id: str
    name: str
    emoji: str
    model: str


# ==================== API Routes ====================

@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """发送消息并获取 AI 回复。
    
    统一的聊天入口，支持：
    - 私聊：agent_ids 只有一个
    - 群聊：agent_ids 有多个
    - 续聊：传入 session_id
    """
    manager = get_chat_manager()
    
    try:
        # 1. 确定会话
        if request.session_id:
            # 续聊：加入已有会话
            session = manager.join_session(request.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        elif request.agent_ids:
            # 新建会话 - 需要将名字转换为 ID
            resolved_ids = []
            all_agents = get_all_agents()
            for agent_ref in request.agent_ids:
                # 尝试匹配 ID 或名字
                matched = False
                for agent in all_agents:
                    if agent_ref.lower() in [agent.id.lower(), agent.name.lower()]:
                        if agent.id not in resolved_ids:
                            resolved_ids.append(agent.id)
                        matched = True
                        break
                if not matched:
                    # 如果没匹配到，直接使用（可能就是 ID）
                    if agent_ref not in resolved_ids:
                        resolved_ids.append(agent_ref)
            
            session = manager.start_new_chat(resolved_ids)
        elif manager.current_session:
            # 使用当前活跃会话
            session = manager.current_session
        else:
            # 默认：与默认 Agent 私聊
            default_agent = get_default_agent()
            session = manager.start_new_chat([default_agent.id])
        
        # 2. 发送消息并获取回复
        responses = manager.send_message(request.message)
        
        # 3. 提取生活信息（后台处理，不阻塞）
        extracted_count = 0
        if responses:
            try:
                extracted_count = process_conversation(
                    request.message,
                    responses[0]["content"]
                )
            except Exception:
                pass
        
        return ChatResponse(
            responses=responses,
            session_id=session.id,
            extracted_count=extracted_count
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(limit: int = 20):
    """获取会话列表。"""
    manager = get_chat_manager()
    sessions = manager.list_all_sessions(limit=limit)
    return [
        SessionInfo(
            id=s["id"],
            type=s["type"],
            agents=s["agents"],
            title=s["title"],
            updated_at=s["updated_at"]
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 50):
    """获取会话历史消息。"""
    manager = get_chat_manager()
    session = manager.join_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = manager.get_history(limit=limit)
    return {
        "session": {
            "id": session.id,
            "type": session.session_type,
            "title": session.get_display_name()
        },
        "messages": [
            {
                "role": msg.role,
                "agent_id": msg.agent_id,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }


@router.get("/agents", response_model=List[AgentInfo])
async def list_agents():
    """获取所有可用的 Agent。"""
    agents = get_all_agents()
    return [
        AgentInfo(
            id=a.id,
            name=a.name,
            emoji=a.emoji,
            model=a.model
        )
        for a in agents
    ]


class RenameRequest(BaseModel):
    """重命名请求。"""
    title: str


@router.patch("/sessions/{session_id}/rename")
async def rename_session(session_id: str, request: RenameRequest):
    """重命名会话。"""
    from src.database import get_db_client
    
    db = get_db_client()
    db.update(
        table="chat_session",
        data={"title": request.title},
        filters={"id": session_id}
    )
    
    return {"status": "ok", "title": request.title}


# ==================== 向后兼容的旧 API ====================
# 这些 API 标记为废弃，但保留用于兼容

from src.agents import run_companion, get_conversation_history


class LegacyChatRequest(BaseModel):
    """旧版聊天请求模型（废弃）。"""
    message: str
    thread_id: str = "main_chat"


class LegacyChatResponse(BaseModel):
    """旧版聊天响应模型（废弃）。"""
    response: str
    extracted_count: int = 0


@router.post("/send/legacy", response_model=LegacyChatResponse)
async def send_message_legacy(request: LegacyChatRequest):
    """发送消息（旧版 API，已废弃）。
    
    保留用于向后兼容，建议使用 /send 代替。
    """
    try:
        response = run_companion(request.message, thread_id=request.thread_id)
        
        extracted_count = 0
        try:
            extracted_count = process_conversation(request.message, response)
        except Exception:
            pass
        
        return LegacyChatResponse(response=response, extracted_count=extracted_count)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{thread_id}")
async def get_history_legacy(thread_id: str):
    """获取对话历史（旧版 API，已废弃）。"""
    try:
        history = get_conversation_history(thread_id)
        return {"messages": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
