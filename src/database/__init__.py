"""
database 模块 - 数据库连接层

提供统一的数据库访问接口：
- get_db_client(): 获取数据库客户端
- is_using_supabase(): 检查是否使用 Supabase
"""

from src.database.db_client import get_db_client, is_using_supabase, DBClient

__all__ = ["get_db_client", "is_using_supabase", "DBClient"]
