"""
文件上传 API
提供文档上传和 embedding 功能
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import tempfile

router = APIRouter(prefix="/api/upload", tags=["upload"])


class UploadResponse(BaseModel):
    """上传响应。"""
    success: bool
    message: str
    chunks: int = 0


@router.post("/document", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """上传文档并存入记忆库。
    
    支持的格式: .txt, .md, .py, .json
    
    文件会被切分成小块并生成 embedding 存入 Supabase。
    """
    # 检查文件类型
    allowed_extensions = [".txt", ".md", ".py", ".json", ".csv"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式 {file_ext}。支持: {', '.join(allowed_extensions)}"
        )
    
    # 检查文件大小 (最大 1MB)
    content = await file.read()
    if len(content) > 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件过大，最大 1MB")
    
    try:
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(mode='wb', suffix=file_ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # 导入到记忆库
            from src.memory.supabase_memory import store_memory
            from src.database import is_using_supabase
            
            if not is_using_supabase():
                # 回退到旧的 RAG 系统
                from src.memory.rag_memory import import_file
                count = import_file(tmp_path)
                return UploadResponse(
                    success=True,
                    message=f"已将 {file.filename} 导入记忆库 ({count} 个片段)",
                    chunks=count
                )
            
            # 使用 Supabase 存储
            text_content = content.decode('utf-8', errors='ignore')
            
            # 切分文本
            chunks = _split_text(text_content, chunk_size=500)
            
            # 存入每个片段
            count = 0
            for chunk in chunks:
                if chunk.strip():
                    store_memory(
                        content=chunk,
                        memory_type="semantic",
                        importance=0.5,
                        source=file.filename
                    )
                    count += 1
            
            return UploadResponse(
                success=True,
                message=f"已将 {file.filename} 存入记忆库 ({count} 个片段)",
                chunks=count
            )
            
        finally:
            # 清理临时文件
            os.unlink(tmp_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


def _split_text(text: str, chunk_size: int = 500) -> list[str]:
    """将文本切分成小块。"""
    chunks = []
    lines = text.split('\n')
    current_chunk = []
    current_size = 0
    
    for line in lines:
        line_size = len(line)
        if current_size + line_size > chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_size = 0
        
        current_chunk.append(line)
        current_size += line_size
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks
