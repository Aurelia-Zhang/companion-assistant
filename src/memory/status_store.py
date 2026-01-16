"""
文件名: status_store.py
功能: 用户状态的数据库存储和检索
在系统中的角色:
    - 负责将用户状态持久化到 SQLite 数据库
    - 提供状态的增删查功能
    - 被命令解析器调用来保存状态
    - 被 Agent 调用来获取用户最近的状态作为上下文

核心逻辑:
    1. 初始化时自动创建 user_status 表
    2. save_status: 保存一条状态记录
    3. get_recent_statuses: 获取最近 N 条状态
    4. get_statuses_by_type: 按类型查询状态
    5. get_today_statuses: 获取今日所有状态
"""

import sqlite3
import os
from datetime import datetime, date
from typing import Optional
from contextlib import contextmanager

from src.models.status import UserStatus, StatusType


# 默认数据库路径，与对话记录使用同一个数据库
DEFAULT_DB_PATH = "data/conversations.db"


class StatusStore:
    """用户状态存储类。
    
    封装了所有与状态存储相关的数据库操作。
    使用 SQLite 作为后端，轻量且无需额外服务。
    """
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """初始化状态存储。
        
        Args:
            db_path: SQLite 数据库路径
        """
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_table()
    
    def _ensure_db_dir(self) -> None:
        """确保数据库目录存在。"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接的上下文管理器。
        
        使用 with 语句确保连接正确关闭。
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 让结果可以用列名访问
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_table(self) -> None:
        """初始化数据库表。"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status_type TEXT NOT NULL,
                    detail TEXT,
                    recorded_at TIMESTAMP NOT NULL,
                    source TEXT NOT NULL DEFAULT 'command'
                )
            """)
            # 创建索引加速查询
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status_recorded_at 
                ON user_status(recorded_at DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status_type 
                ON user_status(status_type)
            """)
            conn.commit()
    
    def save_status(self, status: UserStatus) -> int:
        """保存一条状态记录。
        
        Args:
            status: 要保存的状态对象
            
        Returns:
            新记录的 ID
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO user_status (status_type, detail, recorded_at, source)
                VALUES (?, ?, ?, ?)
                """,
                (status.status_type, status.detail, status.recorded_at, status.source)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_recent_statuses(self, limit: int = 10) -> list[UserStatus]:
        """获取最近的状态记录。
        
        Args:
            limit: 最多返回多少条
            
        Returns:
            状态列表，按时间倒序
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, status_type, detail, recorded_at, source
                FROM user_status
                ORDER BY recorded_at DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
            
            return [self._row_to_status(row) for row in rows]
    
    def get_today_statuses(self) -> list[UserStatus]:
        """获取今日所有状态记录。
        
        Returns:
            今日状态列表，按时间正序
        """
        today = date.today().isoformat()
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, status_type, detail, recorded_at, source
                FROM user_status
                WHERE date(recorded_at) = ?
                ORDER BY recorded_at ASC
                """,
                (today,)
            ).fetchall()
            
            return [self._row_to_status(row) for row in rows]
    
    def get_statuses_by_type(
        self, 
        status_type: StatusType, 
        limit: int = 10
    ) -> list[UserStatus]:
        """按类型获取状态记录。
        
        Args:
            status_type: 状态类型
            limit: 最多返回多少条
            
        Returns:
            状态列表，按时间倒序
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, status_type, detail, recorded_at, source
                FROM user_status
                WHERE status_type = ?
                ORDER BY recorded_at DESC
                LIMIT ?
                """,
                (status_type.value if isinstance(status_type, StatusType) else status_type, limit)
            ).fetchall()
            
            return [self._row_to_status(row) for row in rows]
    
    def _row_to_status(self, row: sqlite3.Row) -> UserStatus:
        """将数据库行转换为 UserStatus 对象。"""
        return UserStatus(
            id=row["id"],
            status_type=row["status_type"],
            detail=row["detail"],
            recorded_at=datetime.fromisoformat(row["recorded_at"]) 
                if isinstance(row["recorded_at"], str) 
                else row["recorded_at"],
            source=row["source"]
        )


# ==================== 便捷函数 ====================
# 提供模块级别的快捷访问

_default_store: Optional[StatusStore] = None


def get_store(db_path: str = DEFAULT_DB_PATH) -> StatusStore:
    """获取默认的状态存储实例（单例模式）。"""
    global _default_store
    if _default_store is None or _default_store.db_path != db_path:
        _default_store = StatusStore(db_path)
    return _default_store


def save_status(status: UserStatus, db_path: str = DEFAULT_DB_PATH) -> int:
    """保存状态（便捷函数）。"""
    return get_store(db_path).save_status(status)


def get_recent_statuses(limit: int = 10, db_path: str = DEFAULT_DB_PATH) -> list[UserStatus]:
    """获取最近状态（便捷函数）。"""
    return get_store(db_path).get_recent_statuses(limit)


def get_today_statuses(db_path: str = DEFAULT_DB_PATH) -> list[UserStatus]:
    """获取今日状态（便捷函数）。"""
    return get_store(db_path).get_today_statuses()
