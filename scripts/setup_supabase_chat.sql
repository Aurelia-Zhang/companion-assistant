-- ============================================
-- 聊天会话表（在 Supabase SQL Editor 执行）
-- ============================================

-- 1. 创建会话表
CREATE TABLE IF NOT EXISTS chat_session (
    id TEXT PRIMARY KEY,
    session_type TEXT NOT NULL DEFAULT 'private',
    agent_ids TEXT NOT NULL,  -- JSON 数组存储
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 创建消息表
CREATE TABLE IF NOT EXISTS chat_message (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES chat_session(id),
    role TEXT NOT NULL,
    agent_id TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 创建索引
CREATE INDEX IF NOT EXISTS idx_session_updated ON chat_session(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_message_session ON chat_message(session_id, created_at);

-- 4. 验证
SELECT table_name FROM information_schema.tables WHERE table_name IN ('chat_session', 'chat_message');
