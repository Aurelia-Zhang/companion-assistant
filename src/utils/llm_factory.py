"""
文件名: llm_factory.py
功能: 统一的 LLM 实例创建工厂
在系统中的角色:
    - 集中管理所有 LLM 实例的创建
    - 支持 per-agent 的 API 配置 (model, api_base_url, api_key)
    - 支持多种 LLM 提供商 (OpenAI, Anthropic/Claude, 等)
    - 提供统一的默认值回退机制

核心逻辑:
    1. 根据 Agent 配置的 provider 选择对应的 LLM 类
    2. 读取 model、api_base_url、api_key_env 配置
    3. 如果 Agent 没有配置某项，回退到环境变量默认值
    4. 返回配置好的 LLM 实例
"""

import os
from typing import Optional, Literal

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from src.models.agent_persona import AgentPersona, get_default_agent


# 支持的 LLM 提供商
LLMProvider = Literal["openai", "anthropic"]


def create_llm(
    agent: Optional[AgentPersona] = None,
    temperature: float = 0.7,
    model_override: Optional[str] = None,
):
    """根据 Agent 配置创建 LLM 实例。
    
    这是创建 LLM 实例的统一入口。所有模块都应该使用这个函数，
    而不是直接 new ChatOpenAI() 或 ChatAnthropic()。
    
    Args:
        agent: Agent 人设配置。如果不传，使用默认 Agent。
        temperature: 生成温度，控制输出随机性。
        model_override: 强制使用的模型名称（覆盖 Agent 配置）。
    
    Returns:
        配置好的 LLM 实例 (ChatOpenAI 或 ChatAnthropic)。
    
    示例:
        # 使用默认 Agent 配置
        llm = create_llm()
        
        # 使用指定 Agent 配置
        from src.models.agent_persona import get_agent_by_id
        agent = get_agent_by_id("claude_assistant")
        llm = create_llm(agent=agent, temperature=0.5)
    """
    # 如果没有指定 Agent，使用默认 Agent
    if agent is None:
        agent = get_default_agent()
    
    # 确定模型名称
    model = model_override or agent.model or "gpt-4o-mini"
    
    # 根据模型名称自动检测 provider
    provider = _detect_provider(model, agent)
    
    # 确定 API Key
    api_key = _get_api_key(agent, provider)
    
    # 确定 API Base URL
    api_base = agent.api_base_url or os.getenv("OPENAI_API_BASE")
    
    # 根据 provider 创建对应的 LLM 实例
    if provider == "anthropic":
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=api_key,
        )
    else:
        # 默认使用 OpenAI
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key,
            base_url=api_base,
        )


def _detect_provider(model: str, agent: AgentPersona) -> LLMProvider:
    """根据模型名称自动检测 provider。
    
    优先使用 Agent 配置的 provider，否则根据模型名称推断。
    """
    # 如果 Agent 配置了 provider，直接使用
    if hasattr(agent, 'provider') and agent.provider:
        return agent.provider
    
    # 根据模型名称推断
    model_lower = model.lower()
    
    if any(name in model_lower for name in ["claude", "anthropic"]):
        return "anthropic"
    
    # 默认使用 OpenAI
    return "openai"


def _get_api_key(agent: AgentPersona, provider: LLMProvider) -> Optional[str]:
    """获取 API Key。
    
    优先级: Agent 专用 Key > Provider 默认 Key
    """
    # 1. 尝试 Agent 专用 Key
    if agent.api_key_env:
        key = os.getenv(agent.api_key_env)
        if key:
            return key
    
    # 2. 回退到 Provider 默认 Key
    if provider == "anthropic":
        return os.getenv("ANTHROPIC_API_KEY")
    else:
        return os.getenv("OPENAI_API_KEY")


def create_llm_simple(
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
):
    """创建简单的 LLM 实例（不使用 Agent 配置）。
    
    用于不需要 per-agent 配置的场景，如信息提取、日记生成等。
    会根据模型名称自动选择 provider。
    
    Args:
        model: 模型名称。
        temperature: 生成温度。
    
    Returns:
        LLM 实例。
    """
    model_lower = model.lower()
    
    if any(name in model_lower for name in ["claude", "anthropic"]):
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
    else:
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
        )
