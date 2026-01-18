"""
文件名: token_store.py
功能: Token 使用量的数据库存储
在系统中的角色:
    - 保存和查询 token 使用记录
    - 提供按日/月汇总统计
    
    v1.2.1: 重构使用统一的 db_client，支持 Supabase 和 SQLite

核心逻辑:
    1. save_usage: 保存单条使用记录
    2. get_daily_summary: 按日汇总
    3. get_monthly_summary: 按月汇总
"""

from datetime import date, datetime, timedelta
from typing import Optional

from src.models.token_usage import TokenUsage
from src.database import get_db_client


class TokenStore:
    """Token 使用量存储类。"""
    
    def __init__(self):
        self.db = get_db_client()
        self._ensure_table()
    
    def _ensure_table(self) -> None:
        """确保数据库表存在（仅 SQLite 需要）。"""
        from src.database.db_client import SQLiteClient
        if isinstance(self.db, SQLiteClient):
            self.db.execute_raw("""
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
            self.db.execute_raw("""
                CREATE INDEX IF NOT EXISTS idx_token_timestamp 
                ON token_usage(timestamp DESC)
            """)
    
    def save_usage(self, usage: TokenUsage) -> int:
        """保存 token 使用记录。"""
        data = {
            "timestamp": usage.timestamp.isoformat(),
            "model": usage.model,
            "agent_id": usage.agent_id,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": usage.cost_usd
        }
        result = self.db.insert("token_usage", data)
        return result.get("id", 0)
    
    def get_today_summary(self) -> dict:
        """获取今日汇总。"""
        today = date.today()
        return self._get_date_summary(today)
    
    def _get_date_summary(self, target_date: date) -> dict:
        """获取指定日期的汇总。"""
        date_str = target_date.isoformat()
        
        from src.database.db_client import SQLiteClient
        if isinstance(self.db, SQLiteClient):
            # SQLite: 使用原始 SQL
            rows = self.db.execute_raw("""
                SELECT 
                    COUNT(*) as call_count,
                    COALESCE(SUM(prompt_tokens), 0) as prompt_tokens,
                    COALESCE(SUM(completion_tokens), 0) as completion_tokens,
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(SUM(cost_usd), 0) as cost_usd
                FROM token_usage
                WHERE date(timestamp) = ?
            """, (date_str,))
            row = dict(rows[0]) if rows else {}
        else:
            # Supabase: 获取所有然后过滤
            all_rows = self.db.select(table="token_usage")
            day_rows = [r for r in all_rows if r.get("timestamp", "").startswith(date_str)]
            
            row = {
                "call_count": len(day_rows),
                "prompt_tokens": sum(r.get("prompt_tokens", 0) for r in day_rows),
                "completion_tokens": sum(r.get("completion_tokens", 0) for r in day_rows),
                "total_tokens": sum(r.get("total_tokens", 0) for r in day_rows),
                "cost_usd": sum(r.get("cost_usd", 0) for r in day_rows)
            }
        
        return {
            "date": date_str,
            "call_count": row.get("call_count", 0),
            "prompt_tokens": row.get("prompt_tokens", 0),
            "completion_tokens": row.get("completion_tokens", 0),
            "total_tokens": row.get("total_tokens", 0),
            "cost_usd": round(row.get("cost_usd", 0), 4)
        }
    
    def get_monthly_summary(self, year: int = None, month: int = None) -> dict:
        """获取月度汇总。"""
        today = date.today()
        year = year or today.year
        month = month or today.month
        
        month_prefix = f"{year}-{month:02d}"
        
        from src.database.db_client import SQLiteClient
        if isinstance(self.db, SQLiteClient):
            # SQLite: 使用原始 SQL
            rows = self.db.execute_raw("""
                SELECT 
                    COUNT(*) as call_count,
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(SUM(cost_usd), 0) as cost_usd
                FROM token_usage
                WHERE strftime('%Y-%m', timestamp) = ?
            """, (month_prefix,))
            row = dict(rows[0]) if rows else {}
        else:
            # Supabase: 获取所有然后过滤
            all_rows = self.db.select(table="token_usage")
            month_rows = [r for r in all_rows if r.get("timestamp", "").startswith(month_prefix)]
            
            row = {
                "call_count": len(month_rows),
                "total_tokens": sum(r.get("total_tokens", 0) for r in month_rows),
                "cost_usd": sum(r.get("cost_usd", 0) for r in month_rows)
            }
        
        return {
            "year": year,
            "month": month,
            "call_count": row.get("call_count", 0),
            "total_tokens": row.get("total_tokens", 0),
            "cost_usd": round(row.get("cost_usd", 0), 4)
        }


# 便捷函数
_store: Optional[TokenStore] = None


def get_token_store() -> TokenStore:
    global _store
    if _store is None:
        _store = TokenStore()
    return _store


def save_usage(usage: TokenUsage) -> int:
    return get_token_store().save_usage(usage)


def get_today_summary() -> dict:
    return get_token_store().get_today_summary()


def get_monthly_summary(year: int = None, month: int = None) -> dict:
    return get_token_store().get_monthly_summary(year, month)
