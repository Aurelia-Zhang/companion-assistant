# AI Context 上下文

> **每次新 Session 开始时，AI 必须先阅读此文件。**

## 当前版本
`v1.2.2` (2026-01-18)

## 当前阶段
- [x] MVP v1.0: 核心功能完成
- [x] v1.1: 日记 + Token 统计
- [x] v1.2: 聊天系统重构 + 前端 + RAG + 推送
- [x] v1.2.1: Per-Agent API 配置 + 代码统一
- [x] v1.2.2: Supabase 云数据库迁移
- [ ] 待办: MCP 邮件功能

---

## 项目架构

```
companion-assistant/
├── main.py          # 旧版 CLI (v1.0)
├── main_v2.py       # 新版 CLI (v1.2) ← 使用这个
├── server.py        # API 服务器 + 前端
├── src/
│   ├── agents/
│   │   ├── companion_agent.py  # 单Agent对话 (LangGraph)
│   │   ├── multi_agent.py      # 多Agent群聊
│   │   ├── chat_manager.py     # v1.2 会话管理器
│   │   └── diary_generator.py  # 日记生成
│   ├── models/
│   │   ├── agent_persona.py    # Agent人设 (含api_base_url)
│   │   ├── chat_session.py     # 聊天会话模型
│   │   └── token_usage.py      # Token使用量
│   ├── memory/
│   │   ├── status_store.py     # 用户状态存储
│   │   ├── chat_store.py       # 聊天记录存储
│   │   ├── diary_store.py      # 日记存储
│   │   ├── token_store.py      # Token统计存储
│   │   └── rag_memory.py       # RAG向量记忆 (ChromaDB)
│   ├── scheduler/
│   │   ├── proactive_service.py # 主动消息
│   │   └── push_service.py      # Web Push推送
│   ├── tools/
│   │   └── email_tool.py        # 邮件MCP
│   └── commands/
│       └── command_parser.py    # /命令解析
├── frontend/         # PWA前端
└── data/             # SQLite数据库
```

---

## v1.2 新功能

### 1. 聊天系统重构
- `main_v2.py`: 新CLI入口
- 私聊: `@小伴`
- 群聊: `@小伴 @学霸君`
- 命令: `/list`, `/join <序号>`, `/export`

### 2. Agent配置增强
- `agent_persona.py` 添加:
  - `model`: 模型名称
  - `api_base_url`: 自定义API地址

### 3. RAG长期记忆
- ChromaDB向量存储
- `/import <文件>` 导入
- `/memory search <关键词>` 搜索
- 对话时自动检索相关记忆

### 4. 推送通知
- iOS Web Push (需PWA添加到主屏幕)
- 配置: `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`

### 5. Token统计
- `/tokens` 今日统计
- `/tokens month` 月度统计
- 自动记录每次API调用

### 6. 日记功能
- `/diary` 生成/查看今日日记
- `/diary 2026-01-18` 查看指定日期

---

## 数据存储

**SQLite**: `data/conversations.db`

| 表 | 用途 |
|----|------|
| chat_session | 聊天会话 |
| chat_message | 聊天消息 |
| user_status | 用户状态 |
| token_usage | Token统计 |
| diary | 日记 |

**ChromaDB**: `data/chroma_db/` (RAG向量)

---

## 待完成

1. **Supabase迁移**: 替换SQLite为云数据库
2. **前端会话列表**: `/list` API尚未实现
3. **AI自动记忆**: AI主动写入记忆库

---

## 重要决策

| 日期 | 决策 | 原因 |
|------|------|------|
| 2026-01-16 | LangGraph | 强状态管理 |
| 2026-01-16 | SQLite | 轻量无服务 |
| 2026-01-18 | ChromaDB | 本地向量存储 |
| 2026-01-18 | Web Push | iOS原生支持 |
