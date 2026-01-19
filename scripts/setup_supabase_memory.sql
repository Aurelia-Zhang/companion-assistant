-- ============================================
-- Supabase 记忆系统设置
-- 在 Supabase SQL Editor 中执行
-- ============================================

-- 1. 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 创建记忆表
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,                    -- 记忆内容
    memory_type TEXT NOT NULL DEFAULT 'episodic',  -- episodic/semantic/emotional/predictive
    importance FLOAT DEFAULT 0.5,             -- 重要性 0-1
    embedding vector(1536),                   -- OpenAI text-embedding-3-small 维度
    emotion_tags TEXT[] DEFAULT '{}',         -- 情感标签
    entity_refs TEXT[] DEFAULT '{}',          -- 关联实体
    source_session TEXT,                      -- 来源会话 ID
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ DEFAULT NOW(),
    access_count INTEGER DEFAULT 0
);

-- 3. 创建向量搜索索引 (使用 ivfflat 加速)
CREATE INDEX ON memories USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 4. 创建时间索引
CREATE INDEX idx_memories_created ON memories(created_at DESC);
CREATE INDEX idx_memories_type ON memories(memory_type);

-- 5. 创建相似度搜索函数
CREATE OR REPLACE FUNCTION match_memories(
    query_embedding vector(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5,
    memory_type_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id INT,
    content TEXT,
    memory_type TEXT,
    importance FLOAT,
    similarity FLOAT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.content,
        m.memory_type,
        m.importance,
        1 - (m.embedding <=> query_embedding) AS similarity,
        m.created_at
    FROM memories m
    WHERE 
        (memory_type_filter IS NULL OR m.memory_type = memory_type_filter)
        AND 1 - (m.embedding <=> query_embedding) > match_threshold
    ORDER BY m.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 6. 测试: 检查扩展是否启用
SELECT * FROM pg_extension WHERE extname = 'vector';
