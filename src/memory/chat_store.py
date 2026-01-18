"""
文件名: chat_store.py
功能: 聊天会话和消息的数据库存储
在系统中的角色:
    - 会话和消息的 CRUD 操作
    - 支持按会话查询消息历史

核心逻辑:
    1. create_session: 创建新会话
    2. add_message: 添加消息
    3. get_session_messages: 获取会话消息
    4. list_sessions: 列出所有会话
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from src.models.chat_session import ChatSession, ChatMessage


DEFAULT_DB_PATH = "data/conversations.db"


class ChatStore:
    """聊天存储类。"""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_tables()
    
    def _ensure_db_dir(self) -> None:
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_tables(self) -> None:
        with self._get_connection() as conn:
            # 会话表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_session (
                    id TEXT PRIMARY KEY,
                    session_type TEXT NOT NULL,
                    agent_ids TEXT NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)
            
            # 消息表
            conn.execute("""
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
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_message_session 
                ON chat_message(session_id, created_at)
            """)
            conn.commit()
    
    def create_session(self, session: ChatSession) -> str:
        """创建新会话。"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO chat_session (id, session_type, agent_ids, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session.id,
                    session.session_type,
                    json.dumps(session.agent_ids),
                    session.title,
                    session.created_at,
                    session.updated_at
                )
            )
            conn.commit()
            return session.id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取会话。"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM chat_session WHERE id = ?",
                (session_id,)
            ).fetchone()
            
            if not row:
                return None
            
            return ChatSession(
                id=row["id"],
                session_type=row["session_type"],
                agent_ids=json.loads(row["agent_ids"]),
                title=row["title"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            )
    
    def list_sessions(self, limit: int = 20) -> list[ChatSession]:
        """列出最近的会话。"""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_session ORDER BY updated_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            
            return [
                ChatSession(
                    id=row["id"],
                    session_type=row["session_type"],
                    agent_ids=json.loads(row["agent_ids"]),
                    title=row["title"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"])
                )
                for row in rows
            ]
    
    def add_message(self, message: ChatMessage) -> str:
        """添加消息。"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO chat_message (id, session_id, role, agent_id, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.session_id,
                    message.role,
                    message.agent_id,
                    message.content,
                    message.created_at
                )
            )
            # 更新会话的 updated_at
            conn.execute(
                "UPDATE chat_session SET updated_at = ? WHERE id = ?",
                (datetime.now(), message.session_id)
            )
            conn.commit()
            return message.id
    
    def get_session_messages(self, session_id: str, limit: int = 50) -> list[ChatMessage]:
        """获取会话消息。"""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM chat_message 
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (session_id, limit)
            ).fetchall()
            
            return [
                ChatMessage(
                    id=row["id"],
                    session_id=row["session_id"],
                    role=row["role"],
                    agent_id=row["agent_id"],
                    content=row["content"],
                    created_at=datetime.fromisoformat(row["created_at"])
                )
                for row in rows
            ]
    
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


# 便捷函数
_store: Optional[ChatStore] = None


def get_chat_store(db_path: str = DEFAULT_DB_PATH) -> ChatStore:
    global _store
    if _store is None or _store.db_path != db_path:
        _store = ChatStore(db_path)
    return _store


def create_session(session: ChatSession) -> str:
    return get_chat_store().create_session(session)


def get_session(session_id: str) -> Optional[ChatSession]:
    return get_chat_store().get_session(session_id)


def list_sessions(limit: int = 20) -> list[ChatSession]:
    return get_chat_store().list_sessions(limit)


def add_message(message: ChatMessage) -> str:
    return get_chat_store().add_message(message)


def get_session_messages(session_id: str, limit: int = 50) -> list[ChatMessage]:
    return get_chat_store().get_session_messages(session_id, limit)


def export_session(session_id: str) -> dict:
    return get_chat_store().export_session(session_id)
