"""
文件名: companion_agent.py
功能: 增强版陪伴 Agent，带人设注入和对话记忆
在系统中的角色:
    - 这是核心的陪伴 Agent 实现
    - 使用 LangGraph 的 SqliteSaver 实现对话持久化
    - 注入人设 Prompt，让 AI 保持一致的人格
    - 通过 thread_id 区分不同的对话会话

核心逻辑:
    1. 加载人设 Prompt 作为 System Message
    2. 用户消息进入图 -> chat 节点调用 LLM -> 返回回复
    3. 使用 SqliteSaver 保存每一步的状态
    4. 下次对话时，通过 thread_id 恢复之前的对话历史

学习要点:
    - SqliteSaver: LangGraph 的 SQLite 持久化方案
    - thread_id: 用于区分不同对话的唯一标识
    - System Message: 如何注入人设
    - 重要：SqliteSaver.from_conn_string() 返回上下文管理器，需要用 with 语句
"""

from typing import Annotated, TypedDict
import os
import sqlite3

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver

from src.config import get_system_prompt, get_full_system_prompt


# ==================== 全局变量 ====================
# 数据库路径，确保整个应用使用同一个数据库
DEFAULT_DB_PATH = "data/conversations.db"


# ==================== 1. 定义状态 ====================
class CompanionState(TypedDict):
    """陪伴 Agent 的状态定义。
    
    相比 Phase 0 的简单状态，这里增加了更多字段，
    为后续功能扩展做准备。
    """
    messages: Annotated[list, add_messages]  # 对话消息列表


# ==================== 2. 定义节点 ====================
def chat_node(state: CompanionState) -> dict:
    """调用 LLM 生成回复。
    
    这个节点会：
    1. 检查是否有 System Message，没有则注入人设
    2. 调用 LLM 生成回复
    3. 返回新消息
    
    Args:
        state: 当前状态，包含对话历史
        
    Returns:
        包含 AI 回复的状态更新
    """
    from langchain_community.callbacks import get_openai_callback
    from src.models.token_usage import TokenUsage
    from src.memory.token_store import save_usage
    
    messages = state["messages"]
    
    # 如果对话刚开始，注入人设 Prompt（包含今日状态）
    # System Message 应该是第一条消息
    if not messages or not isinstance(messages[0], SystemMessage):
        # 使用 get_full_system_prompt 包含今日用户状态
        system_prompt = get_full_system_prompt()
        messages = [SystemMessage(content=system_prompt)] + list(messages)
    
    # 创建 LLM 实例
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,  # 稍微高一点，让回复更自然
    )
    
    # 使用 get_openai_callback 追踪 token
    with get_openai_callback() as cb:
        response = llm.invoke(messages)
    
    # DEBUG: 打印 token 信息
    print(f"[DEBUG Token] prompt={cb.prompt_tokens}, completion={cb.completion_tokens}, total={cb.total_tokens}")
    
    # 保存 token 使用记录
    if cb.total_tokens > 0:
        usage = TokenUsage(
            model="gpt-4o-mini",
            agent_id="xiaoban",
            prompt_tokens=cb.prompt_tokens,
            completion_tokens=cb.completion_tokens,
            total_tokens=cb.total_tokens,
            cost_usd=cb.total_cost
        )
        save_usage(usage)
    
    return {"messages": [response]}


# ==================== 3. 构建图 ====================
def _build_graph() -> StateGraph:
    """构建 LangGraph 图（内部函数）。
    
    Returns:
        未编译的 StateGraph
    """
    graph = StateGraph(CompanionState)
    graph.add_node("chat", chat_node)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    return graph


def _ensure_db_dir(db_path: str) -> None:
    """确保数据库目录存在。"""
    db_dir = os.path.dirname(db_path)
    if db_dir:  # 如果有目录部分
        os.makedirs(db_dir, exist_ok=True)


# ==================== 4. 运行 Agent ====================
def run_companion(
    user_message: str,
    thread_id: str = "default",
    db_path: str = DEFAULT_DB_PATH
) -> str:
    """运行陪伴 Agent，获取回复。
    
    这个函数会：
    1. 创建/恢复指定 thread_id 的对话
    2. 发送用户消息
    3. 返回 AI 回复
    
    通过 thread_id，你可以管理多个独立的对话。
    比如不同场景或不同"房间"可以有不同的 thread_id。
    
    重要：SqliteSaver.from_conn_string() 返回一个上下文管理器，
    必须在 with 语句中使用，这样才能正确管理数据库连接。
    
    Args:
        user_message: 用户输入的消息
        thread_id: 对话线程 ID，用于区分不同对话
        db_path: SQLite 数据库路径
        
    Returns:
        AI 的回复文本
    """
    _ensure_db_dir(db_path)
    
    # 构建图
    graph = _build_graph()
    
    # 使用 with 语句正确管理 SqliteSaver
    # from_conn_string 返回的是上下文管理器，必须这样用
    with SqliteSaver.from_conn_string(db_path) as saver:
        # 用 checkpointer 编译图
        agent = graph.compile(checkpointer=saver)
        
        # 配置：指定 thread_id
        config = {"configurable": {"thread_id": thread_id}}
        
        # 准备输入
        input_state = {"messages": [HumanMessage(content=user_message)]}
        
        # 运行图
        result = agent.invoke(input_state, config)
        
        # 提取 AI 回复
        ai_message = result["messages"][-1]
        return ai_message.content


def get_conversation_history(
    thread_id: str = "default",
    db_path: str = DEFAULT_DB_PATH
) -> list[dict]:
    """获取指定对话的历史记录。
    
    用于调试或展示对话历史。
    
    Args:
        thread_id: 对话线程 ID
        db_path: SQLite 数据库路径
        
    Returns:
        消息列表，每条消息是 {"role": "user/assistant", "content": "..."} 格式
    """
    _ensure_db_dir(db_path)
    
    graph = _build_graph()
    
    with SqliteSaver.from_conn_string(db_path) as saver:
        agent = graph.compile(checkpointer=saver)
        config = {"configurable": {"thread_id": thread_id}}
        
        # 获取当前状态
        state = agent.get_state(config)
        
        if not state.values:
            return []
        
        messages = state.values.get("messages", [])
        history = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                continue  # 跳过系统消息
            elif isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        
        return history


# ==================== 5. 兼容旧接口 ====================
def create_companion_agent(db_path: str = DEFAULT_DB_PATH):
    """创建 Agent（兼容旧接口，不推荐使用）。
    
    注意：这个函数保留是为了兼容性。
    推荐直接使用 run_companion() 函数。
    """
    _ensure_db_dir(db_path)
    graph = _build_graph()
    # 返回未编译的图，让调用者自己管理 saver
    return graph, None
