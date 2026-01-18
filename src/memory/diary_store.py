"""
文件名: diary_store.py
功能: 日记的数据库存储和检索
在系统中的角色:
    - 日记 CRUD 操作
    - 被日记生成器和命令解析器调用
    
    v1.2.1: 重构使用统一的 db_client，支持 Supabase 和 SQLite

核心逻辑:
    1. save_diary: 保存/更新日记
    2. get_diary: 根据日期获取日记
    3. get_recent_diaries: 获取最近的日记
"""

from datetime import date, datetime
from typing import Optional, List

from src.models.diary import DiaryEntry
from src.database import get_db_client


class DiaryStore:
    """日记存储类。"""
    
    def __init__(self):
        self.db = get_db_client()
        self._ensure_table()
    
    def _ensure_table(self) -> None:
        """确保数据库表存在（仅 SQLite 需要）。"""
        from src.database.db_client import SQLiteClient
        if isinstance(self.db, SQLiteClient):
            self.db.execute_raw("""
                CREATE TABLE IF NOT EXISTS diary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    diary_date DATE NOT NULL UNIQUE,
                    content TEXT NOT NULL,
                    generated_at TIMESTAMP NOT NULL
                )
            """)
            self.db.execute_raw("""
                CREATE INDEX IF NOT EXISTS idx_diary_date 
                ON diary(diary_date DESC)
            """)
    
    def save_diary(self, entry: DiaryEntry) -> int:
        """保存或更新日记。同一天的日记会被覆盖。"""
        data = {
            "diary_date": entry.diary_date.isoformat(),
            "content": entry.content,
            "generated_at": entry.generated_at.isoformat()
        }
        result = self.db.upsert("diary", data)
        return result.get("id", 0)
    
    def get_diary(self, diary_date: date) -> Optional[DiaryEntry]:
        """根据日期获取日记。"""
        rows = self.db.select(
            table="diary",
            filters={"diary_date": diary_date.isoformat()}
        )
        if not rows:
            return None
        return self._row_to_entry(rows[0])
    
    def get_recent_diaries(self, limit: int = 7) -> List[DiaryEntry]:
        """获取最近的日记列表。"""
        rows = self.db.select(
            table="diary",
            order_by="diary_date",
            order_desc=True,
            limit=limit
        )
        return [self._row_to_entry(row) for row in rows]
    
    def _row_to_entry(self, row: dict) -> DiaryEntry:
        """将数据库行转换为 DiaryEntry 对象。"""
        diary_date = row.get("diary_date")
        if isinstance(diary_date, str):
            diary_date = date.fromisoformat(diary_date)
        
        generated_at = row.get("generated_at")
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        
        return DiaryEntry(
            id=row.get("id"),
            diary_date=diary_date,
            content=row.get("content", ""),
            generated_at=generated_at
        )


# 便捷函数
_store: Optional[DiaryStore] = None


def get_diary_store() -> DiaryStore:
    global _store
    if _store is None:
        _store = DiaryStore()
    return _store


def save_diary(entry: DiaryEntry) -> int:
    return get_diary_store().save_diary(entry)


def get_diary(diary_date: date) -> Optional[DiaryEntry]:
    return get_diary_store().get_diary(diary_date)


def get_recent_diaries(limit: int = 7) -> List[DiaryEntry]:
    return get_diary_store().get_recent_diaries(limit)
