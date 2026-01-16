"""
文件名: commands/__init__.py
功能: commands 子包初始化
在系统中的角色: 导出命令解析相关的类和函数
"""

from src.commands.command_parser import (
    CommandResult,
    parse_and_execute,
)

__all__ = [
    "CommandResult",
    "parse_and_execute",
]
