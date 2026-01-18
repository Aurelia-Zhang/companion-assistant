"""
文件名: db_client.py
功能: 统一的数据库客户端抽象层
在系统中的角色:
    - 提供 Supabase 和 SQLite 的统一接口
    - 根据环境变量自动选择后端
    - 有 SUPABASE_URL → 使用 Supabase
    - 无配置 → 回退到 SQLite（本地开发）

核心逻辑:
    1. get_db_client() 返回当前激活的数据库客户端
    2. 所有 store 模块通过此模块访问数据库
    3. 保持向后兼容，本地开发无需任何配置
"""

import os
from typing import Optional, Any, List, Dict
from abc import ABC, abstractmethod


class DBClient(ABC):
    """数据库客户端抽象基类。
    
    定义了所有数据库操作的统一接口。
    """
    
    @abstractmethod
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """插入一条记录。"""
        pass
    
    @abstractmethod
    def select(
        self, 
        table: str, 
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """查询记录。"""
        pass
    
    @abstractmethod
    def update(
        self, 
        table: str, 
        data: Dict[str, Any], 
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新记录。"""
        pass
    
    @abstractmethod
    def upsert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """插入或更新记录。"""
        pass
    
    @abstractmethod
    def execute_raw(self, sql: str, params: Optional[tuple] = None) -> Any:
        """执行原始 SQL（仅用于复杂查询）。"""
        pass


class SupabaseClient(DBClient):
    """Supabase 数据库客户端。"""
    
    def __init__(self):
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL 和 SUPABASE_KEY 环境变量必须设置")
        
        self.client = create_client(url, key)
    
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        result = self.client.table(table).insert(data).execute()
        return result.data[0] if result.data else {}
    
    def select(
        self, 
        table: str, 
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        query = self.client.table(table).select(columns)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        if order_by:
            query = query.order(order_by, desc=order_desc)
        
        if limit:
            query = query.limit(limit)
        
        result = query.execute()
        return result.data or []
    
    def update(
        self, 
        table: str, 
        data: Dict[str, Any], 
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        query = self.client.table(table).update(data)
        for key, value in filters.items():
            query = query.eq(key, value)
        result = query.execute()
        return result.data[0] if result.data else {}
    
    def upsert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        result = self.client.table(table).upsert(data).execute()
        return result.data[0] if result.data else {}
    
    def execute_raw(self, sql: str, params: Optional[tuple] = None) -> Any:
        # Supabase 通过 RPC 执行原始 SQL
        # 对于复杂查询，建议创建 Supabase Function
        raise NotImplementedError("Supabase 不直接支持原始 SQL，请使用 select/insert 等方法")


class SQLiteClient(DBClient):
    """SQLite 数据库客户端（本地开发用）。"""
    
    def __init__(self, db_path: str = "data/conversations.db"):
        import sqlite3
        self.db_path = db_path
        self._ensure_db_dir()
    
    def _ensure_db_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    
    def _get_connection(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            cursor = conn.execute(sql, tuple(data.values()))
            conn.commit()
            # 返回插入的数据（加上自动生成的 id）
            result = dict(data)
            result["id"] = cursor.lastrowid
            return result
        finally:
            conn.close()
    
    def select(
        self, 
        table: str, 
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            sql = f"SELECT {columns} FROM {table}"
            params = []
            
            if filters:
                conditions = [f"{k} = ?" for k in filters.keys()]
                sql += " WHERE " + " AND ".join(conditions)
                params.extend(filters.values())
            
            if order_by:
                direction = "DESC" if order_desc else "ASC"
                sql += f" ORDER BY {order_by} {direction}"
            
            if limit:
                sql += f" LIMIT {limit}"
            
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def update(
        self, 
        table: str, 
        data: Dict[str, Any], 
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            where_clause = " AND ".join([f"{k} = ?" for k in filters.keys()])
            sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            params = list(data.values()) + list(filters.values())
            conn.execute(sql, params)
            conn.commit()
            return {**data, **filters}
        finally:
            conn.close()
    
    def upsert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            sql = f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})"
            cursor = conn.execute(sql, tuple(data.values()))
            conn.commit()
            result = dict(data)
            result["id"] = cursor.lastrowid
            return result
        finally:
            conn.close()
    
    def execute_raw(self, sql: str, params: Optional[tuple] = None) -> Any:
        conn = self._get_connection()
        try:
            if params:
                result = conn.execute(sql, params)
            else:
                result = conn.execute(sql)
            conn.commit()
            return result.fetchall()
        finally:
            conn.close()


# ==================== 全局客户端 ====================

_client: Optional[DBClient] = None


def get_db_client() -> DBClient:
    """获取数据库客户端（单例模式）。
    
    自动检测配置：
    - 有 SUPABASE_URL 和 SUPABASE_KEY → 使用 Supabase
    - 否则 → 使用 SQLite
    
    Returns:
        DBClient 实例
    """
    global _client
    
    if _client is not None:
        return _client
    
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
        print("[DB] 使用 Supabase 云数据库")
        _client = SupabaseClient()
    else:
        print("[DB] 使用本地 SQLite 数据库")
        _client = SQLiteClient()
    
    return _client


def is_using_supabase() -> bool:
    """检查是否正在使用 Supabase。"""
    return isinstance(get_db_client(), SupabaseClient)
