"""
文件名: diary_generator.py
功能: 自动生成每日日记
在系统中的角色:
    - 汇总当日对话和状态
    - 调用 LLM 生成日记摘要
    - 保存到数据库

核心逻辑:
    1. 获取当日用户状态
    2. 获取当日对话历史（从 checkpoint）
    3. 用 LLM 生成温馨的日记总结
"""

from datetime import date, datetime
from typing import Optional
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from src.models.diary import DiaryEntry
from src.memory.diary_store import save_diary, get_diary
from src.memory.status_store import get_today_statuses


def generate_diary_content(statuses_text: str) -> str:
    """用 LLM 生成日记内容。"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    prompt = f"""
你是用户的 AI 陪伴助手"小伴"。请根据以下信息，用温暖的语气写一篇简短的日记总结。

## 今日记录
{statuses_text if statuses_text else "今天暂无记录"}

## 要求
- 用第一人称（"你"）写给用户
- 温暖、亲切的语气
- 简短，3-5 句话
- 如果有特别的事情，可以给予鼓励或关心
- 如果没什么记录，就简单问候

请直接输出日记内容：
"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


def generate_today_diary() -> DiaryEntry:
    """生成今日日记。
    
    Returns:
        生成的 DiaryEntry
    """
    today = date.today()
    
    # 获取今日状态
    statuses = get_today_statuses()
    
    # 格式化状态信息
    if statuses:
        status_lines = []
        for s in statuses:
            time_str = s.recorded_at.strftime("%H:%M")
            detail = f" - {s.detail}" if s.detail else ""
            source = " [AI记录]" if s.source == "ai" else ""
            status_lines.append(f"{time_str} {s.status_type}{detail}{source}")
        statuses_text = "\n".join(status_lines)
    else:
        statuses_text = ""
    
    # 生成日记内容
    content = generate_diary_content(statuses_text)
    
    # 创建日记条目
    entry = DiaryEntry(
        diary_date=today,
        content=content,
        generated_at=datetime.now()
    )
    
    # 保存到数据库
    save_diary(entry)
    
    return entry


def get_or_generate_diary(diary_date: date) -> Optional[DiaryEntry]:
    """获取指定日期的日记，如果是今天且不存在则生成。"""
    entry = get_diary(diary_date)
    
    # 如果是今天且没有日记，自动生成
    if entry is None and diary_date == date.today():
        entry = generate_today_diary()
    
    return entry
