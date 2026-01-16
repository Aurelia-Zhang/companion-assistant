"""
文件名: agents/__init__.py
功能: agents 子包初始化
在系统中的角色: 导出所有 Agent 相关的类和函数
"""

from src.agents.simple_agent import create_simple_agent, run_agent

__all__ = ["create_simple_agent", "run_agent"]
