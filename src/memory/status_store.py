"""
文件名: status_store.py
功能: 用户状态的数据库存储和检索
在系统中的角色:
    - 负责将用户状态持久化到数据库
    - 提供状态的增删查功能
    - 被命令解析器调用来保存状态
    - 被 Agent 调用来获取用户最近的状态作为上下文
    
    v1.2.1: 重构使用统一的 db_client，支持 Supabase 和 SQLite

核心逻辑:
    1. save_status: 保存一条状态记录
    2. get_recent_statuses: 获取最近 N 条状态
    3. get_today_statuses: 获取今日所有状态
"""

from datetime import datetime, date
from typing import Optional, List

from src.models.status import UserStatus, StatusType
from src.database import get_db_client


class StatusStore:
    """用户状态存储类。
    
    封装了所有与状态存储相关的数据库操作。
    自动选择 Supabase 或 SQLite 后端。
    """
    
    def __init__(self):
        self.db = get_db_client()
        self._ensure_table()
    
    def _ensure_table(self) -> None:
        """确保数据库表存在（仅 SQLite 需要）。"""
        from src.database.db_client import SQLiteClient
        if isinstance(self.db, SQLiteClient):
            self.db.execute_raw("""
                CREATE TABLE IF NOT EXISTS user_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status_type TEXT NOT NULL,
                    detail TEXT,
                    recorded_at TIMESTAMP NOT NULL,
                    source TEXT NOT NULL DEFAULT 'command'
                )
            """)
            self.db.execute_raw("""
                CREATE INDEX IF NOT EXISTS idx_status_recorded_at 
                ON user_status(recorded_at DESC)
            """)
    
    def save_status(self, status: UserStatus) -> int:
        """保存一条状态记录。
        
        Args:
            status: 要保存的状态对象
            
        Returns:
            新记录的 ID
        """
        data = {
            "status_type": status.status_type,
            "detail": status.detail,
            "recorded_at": status.recorded_at.isoformat(),
            "source": status.source
        }
        result = self.db.insert("user_status", data)
        return result.get("id", 0)
    
    def get_recent_statuses(self, limit: int = 10) -> List[UserStatus]:
        """获取最近的状态记录。
        
        Args:
            limit: 最多返回多少条
            
        Returns:
            状态列表，按时间倒序
        """
        rows = self.db.select(
            table="user_status",
            order_by="recorded_at",
            order_desc=True,
            limit=limit
        )
        return [self._row_to_status(row) for row in rows]
    
    def get_today_statuses(self) -> List[UserStatus]:
        """获取今日所有状态记录。
        
        Returns:
            今日状态列表，按时间正序
        """
        today = date.today().isoformat()
        
        # Supabase 和 SQLite 的日期过滤方式不同
        from src.database.db_client import SQLiteClient
        if isinstance(self.db, SQLiteClient):
            # SQLite: 使用原始 SQL
            rows = self.db.execute_raw(
                "SELECT * FROM user_status WHERE date(recorded_at) = ? ORDER BY recorded_at ASC",
                (today,)
            )
            return [self._row_to_status(dict(row)) for row in rows]
        else:
            # Supabase: 使用 gte/lt 过滤
            from datetime import timedelta
            start = datetime.combine(date.today(), datetime.min.time())
            end = start + timedelta(days=1)
            
            # 使用 Supabase 的 RPC 或过滤
            rows = self.db.select(
                table="user_status",
                order_by="recorded_at",
                order_desc=False
            )
            # 手动过滤今日的记录
            today_rows = [
                row for row in rows 
                if row.get("recorded_at", "").startswith(today)
            ]
            return [self._row_to_status(row) for row in today_rows]
    
    def get_statuses_by_type(
        self, 
        status_type: StatusType, 
        limit: int = 10
    ) -> List[UserStatus]:
        """按类型获取状态记录。"""
        type_value = status_type.value if isinstance(status_type, StatusType) else status_type
        rows = self.db.select(
            table="user_status",
            filters={"status_type": type_value},
            order_by="recorded_at",
            order_desc=True,
            limit=limit
        )
        return [self._row_to_status(row) for row in rows]
    
    def _row_to_status(self, row: dict) -> UserStatus:
        """将数据库行转换为 UserStatus 对象。"""
        from datetime import timezone, timedelta
        CHINA_TZ = timezone(timedelta(hours=8))
        
        recorded_at = row.get("recorded_at")
        if isinstance(recorded_at, str):
            # 处理不同格式的时间字符串
            try:
                dt = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
                # 转换到东八区
                if dt.tzinfo is not None:
                    recorded_at = dt.astimezone(CHINA_TZ)
                else:
                    # 如果没有时区信息，假定是 UTC
                    recorded_at = dt.replace(tzinfo=timezone.utc).astimezone(CHINA_TZ)
            except ValueError:
                recorded_at = datetime.now(CHINA_TZ)
        elif isinstance(recorded_at, datetime):
            # 如果已经是 datetime 对象
            if recorded_at.tzinfo is not None:
                recorded_at = recorded_at.astimezone(CHINA_TZ)
            else:
                recorded_at = recorded_at.replace(tzinfo=timezone.utc).astimezone(CHINA_TZ)
        else:
            recorded_at = datetime.now(CHINA_TZ)
        
        return UserStatus(
            id=row.get("id"),
            status_type=row.get("status_type", ""),
            detail=row.get("detail"),
            recorded_at=recorded_at,
            source=row.get("source", "command")
        )


# ==================== 便捷函数 ====================

_default_store: Optional[StatusStore] = None


def get_store() -> StatusStore:
    """获取默认的状态存储实例（单例模式）。"""
    global _default_store
    if _default_store is None:
        _default_store = StatusStore()
    return _default_store


def save_status(status: UserStatus) -> int:
    """保存状态（便捷函数）。"""
    return get_store().save_status(status)


def get_recent_statuses(limit: int = 10) -> List[UserStatus]:
    """获取最近状态（便捷函数）。"""
    return get_store().get_recent_statuses(limit)


def get_today_statuses() -> List[UserStatus]:
    """获取今日状态（便捷函数）。"""
    return get_store().get_today_statuses()
