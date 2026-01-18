"""
文件名: chat_session.py
功能: 聊天会话和消息模型
在系统中的角色:
    - 统一管理私聊和群聊会话
    - 存储带时间戳的消息记录

核心逻辑:
    - ChatSession: 会话（私聊/群聊）
    - ChatMessage: 单条消息
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
import uuid


class ChatMessage(BaseModel):
    """聊天消息。
    
    Attributes:
        id: 消息唯一标识
        session_id: 所属会话ID
        role: 角色 ('user' | 'assistant')
        agent_id: Agent ID (用户消息时为 None)
        content: 消息内容
        created_at: 创建时间
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: Literal["user", "assistant"]
    agent_id: Optional[str] = None  # user 消息时为 None
    content: str
    created_at: datetime = Field(default_factory=datetime.now)


class ChatSession(BaseModel):
    """聊天会话。
    
    Attributes:
        id: 会话唯一标识
        session_type: 类型 ('private' | 'group')
        agent_ids: 参与的 Agent ID 列表
        title: 会话标题（可选，用于显示）
        created_at: 创建时间
        updated_at: 最后更新时间
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_type: Literal["private", "group"]
    agent_ids: list[str]
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def get_display_name(self) -> str:
        """获取显示名称。"""
        if self.title:
            return self.title
        if self.session_type == "private":
            return f"与 {self.agent_ids[0]} 的对话"
        return f"群聊 ({len(self.agent_ids)} 人)"
