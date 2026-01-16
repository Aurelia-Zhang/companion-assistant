"""
文件名: simple_agent.py
功能: 最简单的 LangGraph Agent 实现 (Hello World 级别)
在系统中的角色:
    - 这是我们学习 LangGraph 的第一个示例
    - 演示了 StateGraph 的基本用法：定义状态、添加节点、设置边
    - 被 main.py 调用，用于测试基础对话功能

核心逻辑:
    1. 定义一个 AgentState，包含消息列表
    2. 创建一个 "chat" 节点，调用 LLM 生成回复
    3. 构建一个最简单的图: START -> chat -> END
    4. 用户输入消息 -> 图运行 -> 返回 AI 回复

学习要点:
    - StateGraph: LangGraph 的核心，定义状态流转
    - add_node: 添加处理节点
    - add_edge: 添加节点之间的边 (流转方向)
    - compile: 编译图为可执行的 Runnable
"""

from typing import Annotated, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


# ==================== 1. 定义状态 ====================
# AgentState 是整个图的"记忆"，在节点之间传递
# messages 字段使用 add_messages 注解，表示新消息会追加到列表中，而不是覆盖
class AgentState(TypedDict):
    """Agent 的状态定义。

    这个状态会在图的各个节点之间传递。
    每个节点可以读取状态，也可以返回更新后的状态。
    """
    messages: Annotated[list, add_messages]  # 对话消息列表，自动追加


# ==================== 2. 定义节点 ====================
# 节点是图中的"处理单元"，接收状态，返回状态更新
def chat_node(state: AgentState) -> dict:
    """调用 LLM 生成回复。

    这是最简单的节点：拿到当前消息列表，调用 LLM，返回新消息。

    Args:
        state: 当前的 Agent 状态，包含所有历史消息

    Returns:
        包含新消息的字典，会被合并到状态中
    """
    # 创建 LLM 实例 (这里用 OpenAI，之后可以换成 Gemini)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    # 调用 LLM，传入所有历史消息
    response = llm.invoke(state["messages"])

    # 返回新消息，会自动追加到 messages 列表
    return {"messages": [response]}


# ==================== 3. 构建图 ====================
def create_simple_agent() -> StateGraph:
    """创建一个最简单的对话 Agent。

    这个 Agent 只有一个节点：chat
    流程: 用户输入 -> chat 节点处理 -> 返回 AI 回复

    Returns:
        编译后的可执行图
    """
    # 创建 StateGraph，指定状态类型
    graph = StateGraph(AgentState)

    # 添加节点: "chat" 节点会调用 chat_node 函数
    graph.add_node("chat", chat_node)

    # 添加边: START -> chat -> END
    # START 是特殊节点，表示图的入口
    # END 是特殊节点，表示图的出口
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    # 编译图，返回可执行的 Runnable
    return graph.compile()


# ==================== 4. 运行 Agent ====================
def run_agent(user_message: str) -> str:
    """运行 Agent，获取 AI 回复。

    Args:
        user_message: 用户输入的消息

    Returns:
        AI 的回复文本
    """
    # 创建 Agent
    agent = create_simple_agent()

    # 准备初始状态: 包含用户消息
    initial_state = {
        "messages": [("user", user_message)]
    }

    # 运行图，获取最终状态
    final_state = agent.invoke(initial_state)

    # 从最终状态中提取 AI 的回复
    # 最后一条消息就是 AI 的回复
    ai_message = final_state["messages"][-1]

    return ai_message.content
