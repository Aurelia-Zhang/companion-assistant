# AI Context 上下文

> **每次新 Session 开始时，AI 必须先阅读此文件。**

## 当前版本
`v1.2.5` (2026-01-19)

## 当前阶段
- [x] MVP v1.0: 核心功能完成
- [x] v1.1: 日记 + Token 统计
- [x] v1.2: 聊天系统重构 + 前端 + RAG + 推送
- [x] v1.2.1: Per-Agent API 配置 + 代码统一
- [x] v1.2.2: Supabase 云数据库迁移
- [x] v1.2.3: 邮件工具集成 (AI 可发邮件)
- [x] v1.2.4: RAG 长期记忆系统 (Supabase pgvector)
- [x] v1.2.5: 手机推送通知 (Web Push) + Render 部署

---

## 项目架构

```
companion-assistant/
├── main_v2.py       # CLI 入口 (v1.2)
├── server.py        # API 服务器
├── src/
│   ├── agents/
│   │   ├── multi_agent.py      # 多Agent聊天 (主要)
│   │   ├── chat_manager.py     # 会话管理器
│   │   └── companion_agent.py  # 单Agent (LangGraph)
│   ├── database/
│   │   └── db_client.py        # 数据库抽象层 (Supabase/SQLite)
│   ├── memory/
│   │   ├── supabase_memory.py  # 向量记忆 (pgvector)
│   │   ├── memory_extractor.py # 自动记忆提取
│   │   ├── chat_store.py       # 聊天存储
│   │   ├── status_store.py     # 状态存储
│   │   └── rag_memory.py       # 本地向量 (ChromaDB, 备用)
│   ├── utils/
│   │   └── llm_factory.py      # LLM工厂 (多provider)
│   ├── scheduler/
│   │   ├── proactive_service.py # 主动消息
│   │   └── push_service.py      # Web Push
│   └── tools/
│       └── email_tool.py        # 邮件发送
├── frontend/         # PWA前端
└── scripts/          # 辅助脚本
```

---

## 核心功能

### 1. 多 Agent 聊天
- 私聊: `@小伴`
- 群聊: `@小伴 @学霸君`
- Agent 可使用不同模型和 API

### 2. Per-Agent API 配置
```python
# agent_persona.py
AgentPersona(
    model="claude-3-haiku",
    api_base_url="https://api.anthropic.com/v1",
    api_key_env="ANTHROPIC_API_KEY"
)
```

### 3. 云数据库 (Supabase)
- 所有数据存储在 Supabase
- SQLite 作为本地开发回退
- 配置: `SUPABASE_URL`, `SUPABASE_KEY`

### 4. 自动记忆系统
- **自动提取**: 对话后 LLM 提取值得记忆的信息
- **四类记忆**: 语义/情景/情感/预测
- **向量检索**: Supabase pgvector
- **上下文注入**: 对话时自动检索相关记忆

### 5. 邮件工具
- AI 可主动发送邮件
- QQ邮箱 SMTP
- 配置: `EMAIL_SENDER`, `EMAIL_PASSWORD`, `EMAIL_RECEIVER`

### 6. 推送通知
- Web Push (iOS 16.4+ PWA)
- 配置: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`
- 前端命令: `/push` 订阅, `/testpush` 测试

---

## 部署

**推荐: Render** (免费, 自动HTTPS)

```bash
# 本地开发
uv run python server.py

# 部署到 Render
git push  # 自动部署
```

**环境变量**:
| 变量 | 必需 | 说明 |
|------|------|------|
| OPENAI_API_KEY | ✅ | OpenAI API |
| SUPABASE_URL | ✅ | Supabase 项目 URL |
| SUPABASE_KEY | ✅ | Supabase anon key |
| EMAIL_SENDER | ❌ | QQ邮箱 |
| EMAIL_PASSWORD | ❌ | 授权码 |
| VAPID_PUBLIC_KEY | ❌ | Web Push 公钥 |
| VAPID_PRIVATE_KEY | ❌ | Web Push 私钥 |

---

## 重要决策

| 日期 | 决策 | 原因 |
|------|------|------|
| 2026-01-16 | LangGraph | 强状态管理 |
| 2026-01-18 | Supabase | 云数据库 + pgvector |
| 2026-01-19 | Render | 免费部署 + HTTPS |
| 2026-01-19 | 自动记忆 | LLM 提取 + 向量存储 |
