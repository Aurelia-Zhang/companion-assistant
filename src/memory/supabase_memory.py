"""
文件名: supabase_memory.py
功能: 基于 Supabase pgvector 的长期记忆存储
在系统中的角色:
    - 存储和检索向量化的记忆
    - 支持相似度搜索 + 时间混合检索
    - 自动记忆提取后的存储后端

核心逻辑:
    1. add_memory: 存储新记忆 (自动向量化)
    2. search_memories: 向量相似度搜索
    3. get_relevant_context: 获取与对话相关的记忆上下文
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from langchain_openai import OpenAIEmbeddings

from src.database import get_db_client, is_using_supabase


class SupabaseMemory:
    """基于 Supabase pgvector 的记忆存储。"""
    
    def __init__(self):
        if not is_using_supabase():
            raise RuntimeError("SupabaseMemory 需要配置 Supabase。请设置 SUPABASE_URL 和 SUPABASE_KEY")
        
        self.db = get_db_client()
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    def add_memory(
        self,
        content: str,
        memory_type: str = "episodic",
        importance: float = 0.5,
        emotion_tags: List[str] = None,
        entity_refs: List[str] = None,
        source_session: str = None
    ) -> int:
        """添加一条记忆。
        
        Args:
            content: 记忆内容
            memory_type: 类型 (episodic/semantic/emotional/predictive)
            importance: 重要性 0-1
            emotion_tags: 情感标签
            entity_refs: 关联实体
            source_session: 来源会话 ID
            
        Returns:
            记忆 ID
        """
        # 生成向量嵌入
        embedding = self.embeddings.embed_query(content)
        
        data = {
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "embedding": embedding,
            "emotion_tags": emotion_tags or [],
            "entity_refs": entity_refs or [],
            "source_session": source_session,
            "created_at": datetime.now().isoformat(),
            "last_accessed_at": datetime.now().isoformat(),
            "access_count": 0
        }
        
        result = self.db.insert("memories", data)
        return result.get("id", 0)
    
    def search_memories(
        self,
        query: str,
        limit: int = 5,
        memory_type: str = None,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """搜索相关记忆。
        
        Args:
            query: 搜索查询
            limit: 返回数量
            memory_type: 可选的类型过滤
            threshold: 相似度阈值
            
        Returns:
            记忆列表
        """
        # 生成查询向量
        query_embedding = self.embeddings.embed_query(query)
        
        # 调用 Supabase RPC 函数
        try:
            result = self.db.client.rpc(
                "match_memories",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": threshold,
                    "match_count": limit,
                    "memory_type_filter": memory_type
                }
            ).execute()
            
            memories = result.data or []
            
            # 更新访问记录
            for mem in memories:
                self._update_access(mem["id"])
            
            return memories
        except Exception as e:
            print(f"[Memory] 搜索失败: {e}")
            return []
    
    def get_recent_memories(
        self,
        days: int = 7,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """获取最近的记忆。"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        # 使用 db_client 的 select 不支持复杂过滤
        # 获取所有然后手动过滤
        rows = self.db.select(
            table="memories",
            order_by="created_at",
            order_desc=True,
            limit=limit * 2  # 多取一些再过滤
        )
        
        # 过滤最近 N 天
        recent = [
            r for r in rows
            if r.get("created_at", "") >= cutoff
        ][:limit]
        
        return recent
    
    def get_context_for_chat(self, message: str, max_memories: int = 5) -> str:
        """获取与消息相关的记忆上下文。
        
        结合向量相似度和最近记忆。
        """
        # 1. 向量搜索
        similar = self.search_memories(message, limit=3, threshold=0.6)
        
        # 2. 最近记忆
        recent = self.get_recent_memories(days=3, limit=2)
        
        # 3. 合并去重
        seen_ids = set()
        all_memories = []
        
        for mem in similar + recent:
            if mem["id"] not in seen_ids:
                seen_ids.add(mem["id"])
                all_memories.append(mem)
        
        if not all_memories:
            return ""
        
        # 4. 格式化
        context_parts = []
        for mem in all_memories[:max_memories]:
            mem_type = mem.get("memory_type", "")
            content = mem.get("content", "")
            context_parts.append(f"[{mem_type}] {content}")
        
        return "## 相关记忆\n" + "\n".join(context_parts)
    
    def _update_access(self, memory_id: int):
        """更新记忆的访问记录。"""
        try:
            self.db.client.table("memories").update({
                "last_accessed_at": datetime.now().isoformat(),
                "access_count": self.db.client.table("memories")
                    .select("access_count")
                    .eq("id", memory_id)
                    .single()
                    .execute()
                    .data.get("access_count", 0) + 1
            }).eq("id", memory_id).execute()
        except Exception:
            pass  # 更新失败不影响主流程


# ==================== 单例和便捷函数 ====================

_memory_instance: Optional[SupabaseMemory] = None


def get_memory() -> Optional[SupabaseMemory]:
    """获取记忆实例。如果未配置 Supabase 则返回 None。"""
    global _memory_instance
    
    if not is_using_supabase():
        return None
    
    if _memory_instance is None:
        try:
            _memory_instance = SupabaseMemory()
        except Exception as e:
            print(f"[Memory] 初始化失败: {e}")
            return None
    
    return _memory_instance


def add_memory(
    content: str,
    memory_type: str = "episodic",
    importance: float = 0.5,
    **kwargs
) -> Optional[int]:
    """添加记忆（便捷函数）。"""
    mem = get_memory()
    if mem:
        return mem.add_memory(content, memory_type, importance, **kwargs)
    return None


def search_memories(query: str, limit: int = 5) -> List[Dict]:
    """搜索记忆（便捷函数）。"""
    mem = get_memory()
    if mem:
        return mem.search_memories(query, limit)
    return []


def get_memory_context(message: str) -> str:
    """获取记忆上下文（便捷函数）。"""
    mem = get_memory()
    if mem:
        return mem.get_context_for_chat(message)
    return ""
