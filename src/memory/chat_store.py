"""
文件名: chat_store.py
功能: 聊天会话和消息的数据库存储
在系统中的角色:
    - 会话和消息的 CRUD 操作
    - 支持按会话查询消息历史
    
    v1.2.1: 重构使用统一的 db_client，支持 Supabase 和 SQLite

核心逻辑:
    1. create_session: 创建新会话
    2. add_message: 添加消息
    3. get_session_messages: 获取会话消息
    4. list_sessions: 列出所有会话
"""

import json
from datetime import datetime
from typing import Optional, List

from src.models.chat_session import ChatSession, ChatMessage
from src.database import get_db_client


class ChatStore:
    """聊天存储类。"""
    
    def __init__(self):
        self.db = get_db_client()
        self._ensure_tables()
    
    def _ensure_tables(self) -> None:
        """确保数据库表存在（仅 SQLite 需要）。"""
        from src.database.db_client import SQLiteClient
        if isinstance(self.db, SQLiteClient):
            self.db.execute_raw("""
                CREATE TABLE IF NOT EXISTS chat_session (
                    id TEXT PRIMARY KEY,
                    session_type TEXT NOT NULL,
                    agent_ids TEXT NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)
            self.db.execute_raw("""
                CREATE TABLE IF NOT EXISTS chat_message (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    agent_id TEXT,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES chat_session(id)
                )
            """)
            self.db.execute_raw("""
                CREATE INDEX IF NOT EXISTS idx_message_session 
                ON chat_message(session_id, created_at)
            """)
    
    def create_session(self, session: ChatSession) -> str:
        """创建新会话。"""
        data = {
            "id": session.id,
            "session_type": session.session_type,
            "agent_ids": json.dumps(session.agent_ids),
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }
        self.db.insert("chat_session", data)
        return session.id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取会话。"""
        rows = self.db.select(
            table="chat_session",
            filters={"id": session_id}
        )
        if not rows:
            return None
        return self._row_to_session(rows[0])
    
    def list_sessions(self, limit: int = 20) -> List[ChatSession]:
        """列出最近的会话。"""
        rows = self.db.select(
            table="chat_session",
            order_by="updated_at",
            order_desc=True,
            limit=limit
        )
        return [self._row_to_session(row) for row in rows]
    
    def add_message(self, message: ChatMessage) -> str:
        """添加消息。"""
        data = {
            "id": message.id,
            "session_id": message.session_id,
            "role": message.role,
            "agent_id": message.agent_id,
            "content": message.content,
            "created_at": message.created_at.isoformat()
        }
        self.db.insert("chat_message", data)
        
        # 更新会话的 updated_at
        self.db.update(
            table="chat_session",
            data={"updated_at": datetime.now().isoformat()},
            filters={"id": message.session_id}
        )
        return message.id
    
    def get_session_messages(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        """获取会话消息。"""
        rows = self.db.select(
            table="chat_message",
            filters={"session_id": session_id},
            order_by="created_at",
            order_desc=False,
            limit=limit
        )
        return [self._row_to_message(row) for row in rows]
    
    def export_session(self, session_id: str) -> dict:
        """导出会话为 JSON。"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        messages = self.get_session_messages(session_id, limit=1000)
        
        return {
            "session": session.model_dump(mode="json"),
            "messages": [m.model_dump(mode="json") for m in messages]
        }
    
    def _row_to_session(self, row: dict) -> ChatSession:
        """将数据库行转换为 ChatSession 对象。"""
        agent_ids = row.get("agent_ids", "[]")
        if isinstance(agent_ids, str):
            agent_ids = json.loads(agent_ids)
        
        created_at = self._parse_datetime(row.get("created_at"))
        updated_at = self._parse_datetime(row.get("updated_at"))
        
        return ChatSession(
            id=row.get("id", ""),
            session_type=row.get("session_type", "private"),
            agent_ids=agent_ids,
            title=row.get("title"),
            created_at=created_at,
            updated_at=updated_at
        )
    
    def _parse_datetime(self, value) -> datetime:
        """安全解析日期时间值。"""
        if value is None:
            return datetime.now()
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # 处理各种 ISO 格式
            try:
                # 标准 ISO 格式 (可能带 Z 或 +00:00)
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                # 尝试更宽松的解析
                try:
                    from dateutil.parser import parse
                    return parse(value)
                except:
                    pass
                # 最后回退
                return datetime.now()
        return datetime.now()
    
    def _row_to_message(self, row: dict) -> ChatMessage:
        """将数据库行转换为 ChatMessage 对象。"""
        created_at = self._parse_datetime(row.get("created_at"))
        
        return ChatMessage(
            id=row.get("id", ""),
            session_id=row.get("session_id", ""),
            role=row.get("role", "user"),
            agent_id=row.get("agent_id"),
            content=row.get("content", ""),
            created_at=created_at
        )


# 便捷函数
_store: Optional[ChatStore] = None


def get_chat_store() -> ChatStore:
    global _store
    if _store is None:
        _store = ChatStore()
    return _store


def create_session(session: ChatSession) -> str:
    return get_chat_store().create_session(session)


def get_session(session_id: str) -> Optional[ChatSession]:
    return get_chat_store().get_session(session_id)


def list_sessions(limit: int = 20) -> List[ChatSession]:
    return get_chat_store().list_sessions(limit)


def add_message(message: ChatMessage) -> str:
    return get_chat_store().add_message(message)


def get_session_messages(session_id: str, limit: int = 50) -> List[ChatMessage]:
    return get_chat_store().get_session_messages(session_id, limit)


def export_session(session_id: str) -> dict:
    return get_chat_store().export_session(session_id)
