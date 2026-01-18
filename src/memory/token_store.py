"""
文件名: token_store.py
功能: Token 使用量的数据库存储
在系统中的角色:
    - 保存和查询 token 使用记录
    - 提供按日/月汇总统计

核心逻辑:
    1. save_usage: 保存单条使用记录
    2. get_daily_summary: 按日汇总
    3. get_monthly_summary: 按月汇总
"""

import sqlite3
import os
from datetime import date, datetime, timedelta
from typing import Optional
from contextlib import contextmanager

from src.models.token_usage import TokenUsage, calculate_cost


DEFAULT_DB_PATH = "data/conversations.db"


class TokenStore:
    """Token 使用量存储类。"""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_table()
    
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
    
    def _init_table(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    model TEXT NOT NULL,
                    agent_id TEXT,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_token_timestamp 
                ON token_usage(timestamp DESC)
            """)
            conn.commit()
    
    def save_usage(self, usage: TokenUsage) -> int:
        """保存 token 使用记录。"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO token_usage 
                (timestamp, model, agent_id, prompt_tokens, completion_tokens, total_tokens, cost_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    usage.timestamp,
                    usage.model,
                    usage.agent_id,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    usage.total_tokens,
                    usage.cost_usd
                )
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_today_summary(self) -> dict:
        """获取今日汇总。"""
        today = date.today()
        return self._get_date_summary(today)
    
    def _get_date_summary(self, target_date: date) -> dict:
        """获取指定日期的汇总。"""
        start = datetime.combine(target_date, datetime.min.time())
        end = start + timedelta(days=1)
        
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT 
                    COUNT(*) as call_count,
                    COALESCE(SUM(prompt_tokens), 0) as prompt_tokens,
                    COALESCE(SUM(completion_tokens), 0) as completion_tokens,
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(SUM(cost_usd), 0) as cost_usd
                FROM token_usage
                WHERE timestamp >= ? AND timestamp < ?
                """,
                (start, end)
            ).fetchone()
            
            return {
                "date": target_date.isoformat(),
                "call_count": row["call_count"],
                "prompt_tokens": row["prompt_tokens"],
                "completion_tokens": row["completion_tokens"],
                "total_tokens": row["total_tokens"],
                "cost_usd": round(row["cost_usd"], 4)
            }
    
    def get_monthly_summary(self, year: int = None, month: int = None) -> dict:
        """获取月度汇总。"""
        today = date.today()
        year = year or today.year
        month = month or today.month
        
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT 
                    COUNT(*) as call_count,
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(SUM(cost_usd), 0) as cost_usd
                FROM token_usage
                WHERE timestamp >= ? AND timestamp < ?
                """,
                (start, end)
            ).fetchone()
            
            return {
                "year": year,
                "month": month,
                "call_count": row["call_count"],
                "total_tokens": row["total_tokens"],
                "cost_usd": round(row["cost_usd"], 4)
            }


# 便捷函数
_store: Optional[TokenStore] = None


def get_token_store(db_path: str = DEFAULT_DB_PATH) -> TokenStore:
    global _store
    if _store is None or _store.db_path != db_path:
        _store = TokenStore(db_path)
    return _store


def save_usage(usage: TokenUsage) -> int:
    return get_token_store().save_usage(usage)


def get_today_summary() -> dict:
    return get_token_store().get_today_summary()


def get_monthly_summary(year: int = None, month: int = None) -> dict:
    return get_token_store().get_monthly_summary(year, month)
