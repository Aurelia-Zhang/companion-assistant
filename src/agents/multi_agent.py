"""
文件名: multi_agent.py
功能: 多 Agent 管理和调度
在系统中的角色:
    - 根据用户消息选择合适的 Agent 回复
    - 支持 @提及 指定 Agent
    - 支持关键词触发和概率触发
    - 调用对应 Agent 生成回复

核心逻辑:
    1. 解析用户消息，检查是否有 @提及
    2. 如果没有 @，检查关键词匹配
    3. 如果没有关键词匹配，使用默认 Agent
    4. 概率触发：即使选了默认，其他 Agent 也可能"插嘴"
"""

import random
import re
from typing import Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.models.agent_persona import (
    AgentPersona,
    get_default_agent,
    get_agent_by_id,
    get_all_agents,
)
from src.config import get_dynamic_user_context


def parse_mention(message: str) -> tuple[Optional[str], str]:
    """解析消息中的 @提及。
    
    Args:
        message: 用户消息
        
    Returns:
        (agent_id, 去除@后的消息)
    """
    # 匹配 @名称 或 @id
    match = re.match(r'^@(\w+)\s*(.*)', message, re.DOTALL)
    if not match:
        return None, message
    
    mention = match.group(1)
    rest = match.group(2).strip()
    
    # 尝试匹配 Agent
    for agent in get_all_agents():
        if mention.lower() in [agent.id.lower(), agent.name.lower()]:
            return agent.id, rest
    
    return None, message


def select_agent(message: str) -> tuple[AgentPersona, str]:
    """根据消息选择 Agent。
    
    Args:
        message: 用户消息
        
    Returns:
        (选中的 Agent, 处理后的消息)
    """
    # 1. 检查 @提及
    mentioned_id, clean_message = parse_mention(message)
    if mentioned_id:
        agent = get_agent_by_id(mentioned_id)
        if agent:
            return agent, clean_message
    
    # 2. 检查关键词匹配
    message_lower = message.lower()
    for agent in get_all_agents():
        if agent.is_default:
            continue
        for keyword in agent.trigger_keywords:
            if keyword in message_lower:
                return agent, message
    
    # 3. 使用默认 Agent
    return get_default_agent(), message


def check_random_join(primary_agent: AgentPersona, message: str) -> Optional[AgentPersona]:
    """检查是否有其他 Agent 想要"插嘴"。
    
    根据概率，可能返回另一个想要加入对话的 Agent。
    
    Args:
        primary_agent: 主要回复的 Agent
        message: 用户消息
        
    Returns:
        想要插嘴的 Agent，或 None
    """
    for agent in get_all_agents():
        if agent.id == primary_agent.id:
            continue
        if agent.trigger_probability > 0:
            if random.random() < agent.trigger_probability:
                return agent
    return None


def generate_response(agent: AgentPersona, message: str, context: str = "") -> str:
    """生成 Agent 回复。
    
    Args:
        agent: 回复的 Agent
        message: 用户消息
        context: 可选的上下文
        
    Returns:
        Agent 的回复
    """
    import os
    
    # 获取 Agent 专用的 API Key，如果没有则使用默认的
    api_key = None
    if agent.api_key_env:
        api_key = os.getenv(agent.api_key_env)
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=api_key)
    
    # 构建 System Prompt
    user_context = get_dynamic_user_context()
    system_prompt = f"""
{agent.personality}

{user_context}

## 回复要求
- 保持你的人设特点
- 回复自然、简洁
- 可以使用 emoji
""".strip()
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=message)
    ]
    
    response = llm.invoke(messages)
    return response.content


def multi_agent_chat(message: str) -> list[dict]:
    """多 Agent 聊天入口。
    
    Args:
        message: 用户消息
        
    Returns:
        回复列表，每项包含 {agent_id, agent_name, emoji, response}
    """
    results = []
    
    # 选择主要 Agent
    primary_agent, clean_message = select_agent(message)
    
    # 生成主要回复
    primary_response = generate_response(primary_agent, clean_message)
    results.append({
        "agent_id": primary_agent.id,
        "agent_name": primary_agent.name,
        "emoji": primary_agent.emoji,
        "response": primary_response
    })
    
    # 检查是否有其他 Agent 想插嘴
    joiner = check_random_join(primary_agent, message)
    if joiner:
        # 让插嘴的 Agent 看到主要 Agent 的回复
        join_prompt = f"""
用户说: {message}
{primary_agent.name}回复: {primary_response}

你觉得有什么想补充的吗？简短回复即可，如果没什么要说的就回复"（无）"。
""".strip()
        join_response = generate_response(joiner, join_prompt)
        
        if "（无）" not in join_response and len(join_response) > 5:
            results.append({
                "agent_id": joiner.id,
                "agent_name": joiner.name,
                "emoji": joiner.emoji,
                "response": join_response
            })
    
    return results
