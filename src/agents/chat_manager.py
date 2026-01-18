"""
文件名: chat_manager.py
功能: 统一的聊天管理器
在系统中的角色:
    - 解析 @Agent 创建聊天
    - 管理当前会话
    - 统一私聊/群聊逻辑

核心逻辑:
    1. parse_chat_command: 解析 @Agent 命令
    2. create_chat: 创建私聊/群聊
    3. send_message: 发送消息并获取回复
"""

import re
from datetime import datetime
from typing import Optional

from src.models.chat_session import ChatSession, ChatMessage
from src.models.agent_persona import get_agent_by_id, get_all_agents, get_default_agent
from src.memory.chat_store import (
    create_session, get_session, list_sessions,
    add_message, get_session_messages, export_session
)
from src.agents.multi_agent import generate_response, check_random_join


class ChatManager:
    """聊天管理器。"""
    
    def __init__(self):
        self.current_session: Optional[ChatSession] = None
    
    def parse_at_mentions(self, text: str) -> list[str]:
        """解析 @提及，返回 Agent ID 列表。"""
        # 匹配 @名称 或 @id
        mentions = re.findall(r'@(\w+)', text)
        
        agent_ids = []
        all_agents = get_all_agents()
        
        for mention in mentions:
            for agent in all_agents:
                if mention.lower() in [agent.id.lower(), agent.name.lower()]:
                    if agent.id not in agent_ids:
                        agent_ids.append(agent.id)
                    break
        
        return agent_ids
    
    def start_new_chat(self, agent_ids: list[str]) -> ChatSession:
        """开始新聊天。"""
        if not agent_ids:
            # 使用默认 Agent
            agent_ids = [get_default_agent().id]
        
        session_type = "private" if len(agent_ids) == 1 else "group"
        
        session = ChatSession(
            session_type=session_type,
            agent_ids=agent_ids
        )
        
        create_session(session)
        self.current_session = session
        
        return session
    
    def join_session(self, session_id: str) -> Optional[ChatSession]:
        """加入已有会话。"""
        session = get_session(session_id)
        if session:
            self.current_session = session
        return session
    
    def leave_session(self) -> None:
        """退出当前会话。"""
        self.current_session = None
    
    def get_history(self, limit: int = 50) -> list[ChatMessage]:
        """获取当前会话历史。"""
        if not self.current_session:
            return []
        return get_session_messages(self.current_session.id, limit)
    
    def send_message(self, content: str) -> list[dict]:
        """发送消息并获取 Agent 回复。
        
        Returns:
            回复列表，每项包含 {agent_id, agent_name, content, timestamp}
        """
        if not self.current_session:
            return []
        
        # 保存用户消息
        user_msg = ChatMessage(
            session_id=self.current_session.id,
            role="user",
            agent_id=None,
            content=content
        )
        add_message(user_msg)
        
        responses = []
        
        if self.current_session.session_type == "private":
            # 私聊：只有一个 Agent 回复
            agent_id = self.current_session.agent_ids[0]
            agent = get_agent_by_id(agent_id)
            if agent:
                reply = generate_response(agent, content)
                
                # 保存 Agent 消息
                agent_msg = ChatMessage(
                    session_id=self.current_session.id,
                    role="assistant",
                    agent_id=agent.id,
                    content=reply
                )
                add_message(agent_msg)
                
                responses.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "content": reply,
                    "timestamp": agent_msg.created_at.strftime("%H:%M:%S")
                })
        else:
            # 群聊：所有 Agent 都可能回复
            for agent_id in self.current_session.agent_ids:
                agent = get_agent_by_id(agent_id)
                if agent:
                    reply = generate_response(agent, content)
                    
                    agent_msg = ChatMessage(
                        session_id=self.current_session.id,
                        role="assistant",
                        agent_id=agent.id,
                        content=reply
                    )
                    add_message(agent_msg)
                    
                    responses.append({
                        "agent_id": agent.id,
                        "agent_name": agent.name,
                        "content": reply,
                        "timestamp": agent_msg.created_at.strftime("%H:%M:%S")
                    })
        
        return responses
    
    def list_all_sessions(self, limit: int = 20) -> list[dict]:
        """列出所有会话。"""
        sessions = list_sessions(limit)
        return [
            {
                "id": s.id,
                "type": s.session_type,
                "agents": s.agent_ids,
                "title": s.get_display_name(),
                "updated_at": s.updated_at.strftime("%Y-%m-%d %H:%M")
            }
            for s in sessions
        ]
    
    def export_current_session(self) -> dict:
        """导出当前会话。"""
        if not self.current_session:
            return {}
        return export_session(self.current_session.id)


# 全局实例
_manager: Optional[ChatManager] = None


def get_chat_manager() -> ChatManager:
    global _manager
    if _manager is None:
        _manager = ChatManager()
    return _manager
