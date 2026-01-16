"""
文件名: info_extractor.py
功能: 从对话中自动提取用户生活信息
在系统中的角色:
    - 在 Agent 回复后，分析对话内容
    - 自动识别用户提到的生活事件（如考试、心情、计划等）
    - 将提取的信息保存到数据库
    - 不干扰正常对话流程

核心逻辑:
    1. 接收最近的对话消息
    2. 调用 LLM 分析是否包含值得记录的生活信息
    3. 如果有，解析出结构化数据
    4. 保存到 user_status 表（source = "ai"）

注意:
    - 这是一个"后台"任务，不影响对话响应速度
    - 使用较小的模型和低 temperature 保证稳定性
    - 允许 AI 自由发挥，用户会定期清理数据库
"""

import json
from datetime import datetime
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.models.status import UserStatus, StatusType
from src.memory.status_store import save_status


# 提取信息的 System Prompt
EXTRACTOR_PROMPT = """
你是一个信息提取助手。你的任务是从用户的对话中识别并提取值得记录的生活信息。

## 需要提取的信息类型
1. 情绪/心情 (mood): 用户表达了某种情绪，如开心、难过、焦虑、疲惫等
2. 计划/安排 (note): 用户提到了未来的计划，如考试、面试、旅行等
3. 状态变化: 用户提到了作息、饮食、学习等状态（但这些通常用命令记录，这里主要捕捉对话中自然提到的）
4. 重要事件: 用户提到的重要生活事件，如生日、纪念日、成就等

## 输出格式
如果发现值得记录的信息，返回 JSON 数组：
```json
[
  {"type": "mood", "detail": "因为项目进展顺利感到开心"},
  {"type": "note", "detail": "明天下午有算法考试"}
]
```

如果没有值得记录的信息，返回空数组：
```json
[]
```

## 注意事项
- 只提取明确、具体的信息，不要过度解读
- 心情要有具体原因才记录
- 日常寒暄不需要记录
- 如果用户说"我要去吃饭了"这类简单状态，不需要记录（用户会用命令）
- 重点关注：考试/面试/重要事件、情绪变化、未来计划
"""


def extract_life_info(user_message: str, ai_response: str) -> list[dict]:
    """从对话中提取生活信息。
    
    Args:
        user_message: 用户发送的消息
        ai_response: AI 的回复
        
    Returns:
        提取到的信息列表，每项包含 type 和 detail
    """
    # 使用较小的模型，降低成本
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,  # 低 temperature 保证稳定输出
    )
    
    # 构建消息
    messages = [
        SystemMessage(content=EXTRACTOR_PROMPT),
        HumanMessage(content=f"""
请分析以下对话，提取值得记录的生活信息：

用户: {user_message}
AI: {ai_response}

请返回 JSON 格式的结果：
""")
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # 尝试解析 JSON
        # 处理 markdown 代码块
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        
        if isinstance(result, list):
            return result
        return []
        
    except Exception as e:
        # 解析失败时静默返回空列表，不影响主流程
        print(f"[调试] 信息提取失败: {e}")
        return []


def save_extracted_info(extracted: list[dict]) -> int:
    """保存提取到的信息到数据库。
    
    Args:
        extracted: 提取到的信息列表
        
    Returns:
        成功保存的条数
    """
    saved_count = 0
    
    for item in extracted:
        info_type = item.get("type", "")
        detail = item.get("detail", "")
        
        if not detail:
            continue
        
        # 映射类型
        if info_type == "mood":
            status_type = StatusType.MOOD
        else:
            status_type = StatusType.NOTE
        
        status = UserStatus(
            status_type=status_type,
            detail=detail,
            recorded_at=datetime.now(),
            source="ai"  # 标记为 AI 自动提取
        )
        
        try:
            save_status(status)
            saved_count += 1
        except Exception as e:
            print(f"[调试] 保存提取信息失败: {e}")
    
    return saved_count


def process_conversation(user_message: str, ai_response: str) -> int:
    """处理对话，提取并保存生活信息。
    
    这是对外的主入口函数。
    
    Args:
        user_message: 用户消息
        ai_response: AI 回复
        
    Returns:
        保存的信息条数
    """
    # 跳过太短的消息
    if len(user_message) < 10:
        return 0
    
    # 提取信息
    extracted = extract_life_info(user_message, ai_response)
    
    if not extracted:
        return 0
    
    # 保存到数据库
    return save_extracted_info(extracted)
