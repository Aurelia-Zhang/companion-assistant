"""
文件名: token_usage.py
功能: Token 使用量数据模型
在系统中的角色:
    - 记录每次 LLM 调用的 token 消耗
    - 用于成本核算和用量统计

核心逻辑:
    - TokenUsage: 单次调用的 token 消耗
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# 模型价格 (每 1K tokens 的美元价格)
MODEL_PRICES = {
    "gpt-4o-mini": {
        "input": 0.00015,   # $0.15 / 1M
        "output": 0.0006,   # $0.60 / 1M
    },
    "gpt-4o": {
        "input": 0.005,     # $5.00 / 1M
        "output": 0.015,    # $15.00 / 1M
    },
}


class TokenUsage(BaseModel):
    """Token 使用量记录。
    
    Attributes:
        id: 数据库自增 ID
        timestamp: 记录时间
        model: 使用的模型名称
        agent_id: Agent ID (可选)
        prompt_tokens: 输入 token 数
        completion_tokens: 输出 token 数
        total_tokens: 总 token 数
        cost_usd: 费用 (美元)
    """
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    model: str = "gpt-4o-mini"
    agent_id: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """计算 API 调用成本。"""
    prices = MODEL_PRICES.get(model, MODEL_PRICES["gpt-4o-mini"])
    input_cost = (prompt_tokens / 1000) * prices["input"]
    output_cost = (completion_tokens / 1000) * prices["output"]
    return round(input_cost + output_cost, 6)
