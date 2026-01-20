# v1.2.5 功能总结

> 完成日期: 2026-01-19

## 本次 Session 完成的功能

### 1. Per-Agent API 配置
- `llm_factory.py`: 统一 LLM 创建，支持 OpenAI/Claude/OpenRouter
- Agent 可配置独立的 model、api_base_url、api_key_env

### 2. Supabase 云数据库
- `db_client.py`: 数据库抽象层，自动选择 Supabase/SQLite
- 迁移 4 个 store: status, chat, token, diary
- 配置: `SUPABASE_URL`, `SUPABASE_KEY`

### 3. 邮件工具
- `email_tool.py`: QQ邮箱 SMTP 发送
- AI 可调用 `send_email_tool` 发送邮件
- Tool 执行后继续生成文本回复

### 4. RAG 自动记忆
- `supabase_memory.py`: pgvector 向量存储
- `memory_extractor.py`: LLM 自动提取记忆
- 四类记忆: 语义/情景/情感/预测
- 对话后异步存储，下次对话检索

### 5. Web Push 推送
- `push_service.py`: pywebpush 发送
- `sw.js`: Service Worker push 事件
- 前端 `/push` 订阅，`/testpush` 测试

### 6. Render 部署
- `render.yaml`: 部署配置
- `requirements.txt`: 依赖列表
- `server.py`: 支持 PORT 环境变量

## 关键文件

| 文件 | 功能 |
|------|------|
| `src/utils/llm_factory.py` | LLM 工厂 |
| `src/database/db_client.py` | 数据库抽象 |
| `src/memory/supabase_memory.py` | 向量记忆 |
| `src/memory/memory_extractor.py` | 记忆提取 |
| `src/tools/email_tool.py` | 邮件工具 |
| `frontend/sw.js` | Service Worker |
