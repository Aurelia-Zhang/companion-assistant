"""
文件名: diary_store.py
功能: 日记的数据库存储和检索
在系统中的角色:
    - 日记 CRUD 操作
    - 被日记生成器和命令解析器调用

核心逻辑:
    1. 初始化时创建 diary 表
    2. save_diary: 保存/更新日记
    3. get_diary: 根据日期获取日记
"""

import sqlite3
import os
from datetime import date, datetime
from typing import Optional
from contextlib import contextmanager

from src.models.diary import DiaryEntry


DEFAULT_DB_PATH = "data/conversations.db"


class DiaryStore:
    """日记存储类。"""
    
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
                CREATE TABLE IF NOT EXISTS diary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    diary_date DATE NOT NULL UNIQUE,
                    content TEXT NOT NULL,
                    generated_at TIMESTAMP NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_diary_date 
                ON diary(diary_date DESC)
            """)
            conn.commit()
    
    def save_diary(self, entry: DiaryEntry) -> int:
        """保存或更新日记。同一天的日记会被覆盖。"""
        with self._get_connection() as conn:
            # 使用 REPLACE 语法，同日期则更新
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO diary (diary_date, content, generated_at)
                VALUES (?, ?, ?)
                """,
                (entry.diary_date.isoformat(), entry.content, entry.generated_at)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_diary(self, diary_date: date) -> Optional[DiaryEntry]:
        """根据日期获取日记。"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM diary WHERE diary_date = ?",
                (diary_date.isoformat(),)
            ).fetchone()
            
            if not row:
                return None
            
            return DiaryEntry(
                id=row["id"],
                diary_date=date.fromisoformat(row["diary_date"]),
                content=row["content"],
                generated_at=datetime.fromisoformat(row["generated_at"])
            )
    
    def get_recent_diaries(self, limit: int = 7) -> list[DiaryEntry]:
        """获取最近的日记列表。"""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM diary ORDER BY diary_date DESC LIMIT ?",
                (limit,)
            ).fetchall()
            
            return [
                DiaryEntry(
                    id=row["id"],
                    diary_date=date.fromisoformat(row["diary_date"]),
                    content=row["content"],
                    generated_at=datetime.fromisoformat(row["generated_at"])
                )
                for row in rows
            ]


# 便捷函数
_store: Optional[DiaryStore] = None


def get_diary_store(db_path: str = DEFAULT_DB_PATH) -> DiaryStore:
    global _store
    if _store is None or _store.db_path != db_path:
        _store = DiaryStore(db_path)
    return _store


def save_diary(entry: DiaryEntry) -> int:
    return get_diary_store().save_diary(entry)


def get_diary(diary_date: date) -> Optional[DiaryEntry]:
    return get_diary_store().get_diary(diary_date)


def get_recent_diaries(limit: int = 7) -> list[DiaryEntry]:
    return get_diary_store().get_recent_diaries(limit)
