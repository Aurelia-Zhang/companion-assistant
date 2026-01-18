"""
文件名: agent_persona.py
功能: 定义 Agent 人设模型
在系统中的角色:
    - 存储每个 Agent 的人设信息
    - 定义触发条件和关键词
    - 被 Agent 管理器调用

核心逻辑:
    - AgentPersona: 包含名称、性格、触发条件等
    - 默认提供几个预设 Agent
"""

from typing import Optional
from pydantic import BaseModel, Field


class AgentPersona(BaseModel):
    """Agent 人设定义。
    
    Attributes:
        id: Agent 唯一标识
        name: 显示名称
        emoji: 头像 emoji
        personality: 性格描述（用于 System Prompt）
        trigger_keywords: 触发关键词（用户消息包含这些词时可能触发）
        trigger_probability: 概率触发（即使没关键词也可能随机加入）
        is_default: 是否是默认 Agent（用户直接聊天时使用）
        model: 使用的模型名称
        api_base_url: API Base URL（可选，用于不同模型提供商）
        api_key_env: 专用 API Key 的环境变量名（可选）
    """
    id: str
    name: str
    emoji: str = "🤖"
    personality: str
    trigger_keywords: list[str] = Field(default_factory=list)
    trigger_probability: float = 0.0  # 0-1，随机触发概率
    is_default: bool = False
    model: str = "gpt-4o-mini"  # 模型名称
    api_base_url: Optional[str] = None  # 如 "https://api.openai.com/v1"
    api_key_env: Optional[str] = None  # 如 "AGENT_XUEBA_API_KEY"


# ==================== 预设 Agent ====================

PRESET_AGENTS = [
    AgentPersona(
        id="xiaoban",
        name="小伴",
        emoji="🐱",
        personality="""
你是用户的 AI 陪伴助手，名字叫"小伴"。
性格：温暖、体贴、有耐心，像一个值得信赖的好朋友。
说话风格：轻松亲切，适当使用表情符号。
职责：日常聊天、情感支持、提醒关心。
""".strip(),
        is_default=True
    ),
    AgentPersona(
        id="xueba",
        name="学霸君",
        emoji="📚",
        personality="""
你是一个学习助手，名字叫"学霸君"。
性格：认真、专业、有条理，但不死板。
说话风格：简洁清晰，重点突出。
职责：解答学习问题、提供学习建议、复习规划。
""".strip(),
        trigger_keywords=["学习", "复习", "考试", "作业", "习题", "算法", "代码", "编程"],
        trigger_probability=0.1,
        api_key_env="AGENT_XUEBA_API_KEY"  # 可单独配置 API Key
    ),
    AgentPersona(
        id="tiyu",
        name="运动达人",
        emoji="💪",
        personality="""
你是一个运动健康助手，名字叫"运动达人"。
性格：阳光、积极、充满活力。
说话风格：热情鼓励，简短有力。
职责：运动建议、健康提醒、鼓励锻炼。
""".strip(),
        trigger_keywords=["运动", "健身", "跑步", "锻炼", "减肥", "健康", "久坐"],
        trigger_probability=0.05,
        api_key_env="AGENT_TIYU_API_KEY"  # 可单独配置 API Key
    ),
]


def get_default_agent() -> AgentPersona:
    """获取默认 Agent。"""
    for agent in PRESET_AGENTS:
        if agent.is_default:
            return agent
    return PRESET_AGENTS[0]


def get_agent_by_id(agent_id: str) -> Optional[AgentPersona]:
    """根据 ID 获取 Agent。"""
    for agent in PRESET_AGENTS:
        if agent.id == agent_id:
            return agent
    return None


def get_all_agents() -> list[AgentPersona]:
    """获取所有 Agent。"""
    return PRESET_AGENTS.copy()
