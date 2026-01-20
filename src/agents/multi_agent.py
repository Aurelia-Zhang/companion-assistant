"""
文件名: multi_agent.py
功能: Agent 回复生成
在系统中的角色:
    - 调用 LLM 生成 Agent 回复
    - 处理 RAG 记忆上下文
    - 追踪 Token 使用
    - 处理工具调用（如邮件）

注意: Agent 选择逻辑现在由 chat_manager.py 处理
"""

from datetime import datetime
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from src.models.agent_persona import AgentPersona
from src.config import get_dynamic_user_context
from src.utils.llm_factory import create_llm
from src.tools.email_tool import get_email_tools


def generate_response(agent: AgentPersona, message: str, context: str = "") -> str:
    """生成 Agent 回复。
    
    Args:
        agent: 回复的 Agent
        message: 用户消息
        context: 可选的上下文
        
    Returns:
        Agent 的回复
    """
    from langchain_community.callbacks import get_openai_callback
    from src.models.token_usage import TokenUsage, calculate_cost
    from src.memory.token_store import save_usage
    
    # 使用工厂函数创建 LLM 实例（支持 per-agent 配置）
    llm = create_llm(agent=agent, temperature=0.7)
    
    # 构建 System Prompt (包含 RAG 记忆)
    user_context = get_dynamic_user_context()
    
    # 获取 RAG 相关记忆 (优先使用新的 Supabase 记忆系统)
    try:
        from src.memory.supabase_memory import get_memory_context
        memory_context = get_memory_context(message)
    except Exception:
        # 回退到旧的 ChromaDB
        try:
            from src.memory.rag_memory import get_memory_context as get_old_memory
            memory_context = get_old_memory(message)
        except Exception:
            memory_context = ""
    
    system_prompt = f"""
{agent.personality}

{user_context}

{memory_context}

## 回复要求
- 保持你的人设特点
- 回复自然、简洁
- 可以使用 emoji

## 可用工具
你可以使用 send_email_tool 发送邮件给用户，但请谨慎使用：
- 仅在用户明确要求或有重要事项时发送
- 不要频繁发送无意义的邮件
""".strip()
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=message)
    ]
    
    # 绑定工具
    tools = get_email_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    # 使用 get_openai_callback 追踪 token
    with get_openai_callback() as cb:
        response = llm_with_tools.invoke(messages)
    
    # 处理工具调用
    tool_results = []
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call.get('name', '')
            tool_args = tool_call.get('args', {})
            tool_id = tool_call.get('id', '')
            
            # 执行邮件工具
            if tool_name == 'send_email_tool':
                from src.tools.email_tool import send_email_tool
                tool_result = send_email_tool.invoke(tool_args)
                print(f"[Tool] {tool_name}: {tool_result}")
                tool_results.append((tool_id, tool_name, tool_result))
        
        # 如果有工具调用，需要让 LLM 生成后续回复
        if tool_results:
            # 构建包含工具结果的消息
            messages_with_tools = messages + [response]
            for tool_id, tool_name, result in tool_results:
                messages_with_tools.append(
                    ToolMessage(content=result, tool_call_id=tool_id)
                )
            
            # 再次调用 LLM 生成最终回复
            final_response = llm_with_tools.invoke(messages_with_tools)
            response = final_response
    
    # DEBUG: 打印回调捕获的信息
    print(f"[DEBUG Token] prompt={cb.prompt_tokens}, completion={cb.completion_tokens}, total={cb.total_tokens}, cost={cb.total_cost}")
    
    # 保存 token 使用记录
    if cb.total_tokens > 0:
        usage = TokenUsage(
            model=agent.model,
            agent_id=agent.id,
            prompt_tokens=cb.prompt_tokens,
            completion_tokens=cb.completion_tokens,
            total_tokens=cb.total_tokens,
            cost_usd=cb.total_cost
        )
        save_usage(usage)
    
    # 异步提取记忆 (不阻塞主流程)
    final_content = response.content or ""
    try:
        from src.memory.memory_extractor import process_conversation_for_memory
        import threading
        thread = threading.Thread(
            target=process_conversation_for_memory,
            args=(message, final_content, context)
        )
        thread.daemon = True
        thread.start()
    except Exception:
        pass
    
    return final_content
