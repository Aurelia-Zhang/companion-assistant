"""
文件名: rag_memory.py
功能: RAG 长期记忆存储
在系统中的角色:
    - 导入大文件并向量化
    - 对话时检索相关片段

核心逻辑:
    1. import_file: 读取文件 → 分块 → 向量化 → 存储
    2. search: 根据查询检索相关片段
    3. get_context: 获取与对话相关的记忆上下文
"""

import os
from typing import Optional
from pathlib import Path

# ChromaDB 和 LangChain
try:
    import chromadb
    from chromadb.config import Settings
    from langchain_openai import OpenAIEmbeddings
    from langchain_chroma import Chroma
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


# 存储路径
CHROMA_PATH = "data/chroma_db"


class RAGMemory:
    """RAG 记忆存储。"""
    
    def __init__(self):
        if not RAG_AVAILABLE:
            raise ImportError("ChromaDB not installed. Run: uv add chromadb langchain-chroma")
        
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        # 确保目录存在
        os.makedirs(CHROMA_PATH, exist_ok=True)
        
        # 初始化 ChromaDB
        self.vectorstore = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=self.embeddings,
            collection_name="long_term_memory"
        )
    
    def import_file(self, file_path: str, doc_type: str = "user_data") -> int:
        """导入文件到记忆库。
        
        Args:
            file_path: 文件路径
            doc_type: 文档类型 (user_data / persona / reference)
            
        Returns:
            导入的片段数量
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # 读取文件内容
        content = path.read_text(encoding="utf-8")
        
        # 分块
        chunks = self.text_splitter.split_text(content)
        
        # 添加元数据
        metadatas = [
            {
                "source": path.name,
                "doc_type": doc_type,
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]
        
        # 存储
        self.vectorstore.add_texts(texts=chunks, metadatas=metadatas)
        
        return len(chunks)
    
    def search(self, query: str, k: int = 3, doc_type: str = None) -> list[dict]:
        """搜索相关记忆片段。
        
        Args:
            query: 搜索查询
            k: 返回数量
            doc_type: 可选的文档类型过滤
            
        Returns:
            相关片段列表
        """
        filter_dict = {"doc_type": doc_type} if doc_type else None
        
        results = self.vectorstore.similarity_search_with_score(
            query, k=k, filter=filter_dict
        )
        
        return [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", ""),
                "doc_type": doc.metadata.get("doc_type", ""),
                "score": score
            }
            for doc, score in results
        ]
    
    def get_context_for_chat(self, message: str, max_tokens: int = 500) -> str:
        """获取与消息相关的记忆上下文。
        
        Args:
            message: 用户消息
            max_tokens: 最大 token 数（约）
            
        Returns:
            格式化的上下文字符串
        """
        results = self.search(message, k=3)
        
        if not results:
            return ""
        
        context_parts = []
        total_len = 0
        
        for r in results:
            content = r["content"]
            if total_len + len(content) > max_tokens * 4:  # 粗略估算
                break
            context_parts.append(f"[{r['source']}] {content}")
            total_len += len(content)
        
        if not context_parts:
            return ""
        
        return "## 相关记忆\n" + "\n".join(context_parts)
    
    def list_documents(self) -> list[str]:
        """列出所有已导入的文档。"""
        # ChromaDB 没有直接列出所有文档的方法
        # 我们通过获取一个大集合来实现
        try:
            all_docs = self.vectorstore.get()
            sources = set()
            if all_docs and all_docs.get("metadatas"):
                for meta in all_docs["metadatas"]:
                    if meta and "source" in meta:
                        sources.add(meta["source"])
            return list(sources)
        except Exception:
            return []


# 单例
_rag_memory: Optional[RAGMemory] = None


def get_rag_memory() -> RAGMemory:
    """获取 RAG 记忆单例。"""
    global _rag_memory
    if _rag_memory is None:
        _rag_memory = RAGMemory()
    return _rag_memory


def import_file(file_path: str, doc_type: str = "user_data") -> int:
    """导入文件到记忆库。"""
    return get_rag_memory().import_file(file_path, doc_type)


def search_memory(query: str, k: int = 3) -> list[dict]:
    """搜索记忆。"""
    return get_rag_memory().search(query, k)


def get_memory_context(message: str) -> str:
    """获取与消息相关的记忆上下文。"""
    try:
        return get_rag_memory().get_context_for_chat(message)
    except Exception:
        return ""


def list_imported_documents() -> list[str]:
    """列出已导入文档。"""
    try:
        return get_rag_memory().list_documents()
    except Exception:
        return []
