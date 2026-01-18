"""
文件名: diary.py
功能: 日记数据模型
在系统中的角色:
    - 存储每日生成的 AI 日记
    - 被 diary_store 调用

核心逻辑:
    - DiaryEntry: 日记条目，包含日期、内容、生成时间
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class DiaryEntry(BaseModel):
    """日记条目模型。
    
    Attributes:
        id: 数据库自增 ID
        diary_date: 日记日期 (YYYY-MM-DD)
        content: 日记内容 (AI 生成的总结)
        generated_at: 生成时间
    """
    id: Optional[int] = None
    diary_date: date
    content: str
    generated_at: datetime = Field(default_factory=datetime.now)
