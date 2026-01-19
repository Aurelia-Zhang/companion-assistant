# AI 陪伴助手 🐱

> 一个提供"极致陪伴"的 AI 助手，支持多智能体、自动记忆、主动关心等功能。

## 🎯 项目状态
- **当前版本**: v1.2.5
- **最后更新**: 2026-01-19

## ✨ 核心功能

| 功能 | 描述 |
|------|------|
| 🐱 **多 Agent** | 私聊 `@小伴` / 群聊 `@小伴 @学霸君` |
| 🧠 **自动记忆** | AI 自动提取和检索长期记忆 |
| 📧 **邮件通知** | AI 可主动发邮件给你 |
| 📲 **推送通知** | iOS/Android PWA 推送 |
| ⏰ **主动关心** | 定时问候、起床提醒 |
| 📊 **Token 统计** | 追踪 API 使用量和费用 |
| 📔 **日记功能** | 每日自动生成日记 |

## 🚀 快速开始

### 本地开发

```bash
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY

# 启动 CLI
uv run python main_v2.py

# 启动 Web 服务
uv run python server.py
# 访问 http://localhost:8000
```

### 云部署 (Render)

1. Fork/Push 到 GitHub
2. 在 [Render](https://render.com) 创建 Web Service
3. 配置环境变量 (见 `.env.example`)
4. 自动部署完成

## 📁 项目结构

```
├── main_v2.py       # CLI 入口
├── server.py        # Web 服务器
├── src/
│   ├── agents/      # Agent 和聊天管理
│   ├── database/    # 数据库抽象 (Supabase/SQLite)
│   ├── memory/      # 记忆系统 (pgvector)
│   ├── scheduler/   # 主动消息 + 推送
│   ├── tools/       # AI 工具 (邮件等)
│   └── utils/       # LLM 工厂等
├── frontend/        # PWA 前端
└── scripts/         # 辅助脚本
```

## 🛠️ 技术栈

- **LLM**: OpenAI / Anthropic / OpenRouter
- **框架**: LangChain + LangGraph
- **数据库**: Supabase (PostgreSQL + pgvector)
- **后端**: FastAPI + uvicorn
- **前端**: PWA (原生 JS)
- **部署**: Render

## 📚 文档

- [AI 上下文](docs/ai_context.md) ← **新 AI 会话必读**
- [部署指南](docs/deployment_guide.md)
- [需求文档](docs/requirements_mvp.md)

## 🔧 环境变量

| 变量 | 必需 | 说明 |
|------|:----:|------|
| `OPENAI_API_KEY` | ✅ | OpenAI API 密钥 |
| `SUPABASE_URL` | ✅ | Supabase 项目 URL |
| `SUPABASE_KEY` | ✅ | Supabase anon key |
| `EMAIL_SENDER` | ❌ | 发件邮箱 (QQ邮箱) |
| `EMAIL_PASSWORD` | ❌ | 邮箱授权码 |
| `VAPID_PUBLIC_KEY` | ❌ | Web Push 公钥 |
| `VAPID_PRIVATE_KEY` | ❌ | Web Push 私钥 |

## 📜 更新日志

### v1.2.5 (2026-01-19)
- ✅ Supabase 云数据库迁移
- ✅ 自动记忆提取 (pgvector)
- ✅ 邮件工具集成
- ✅ Web Push 推送
- ✅ Render 部署支持

### v1.2.0 (2026-01-18)
- 聊天系统重构 (私聊/群聊)
- Per-Agent API 配置
- RAG 长期记忆
- Token 统计

### v1.0.0 (2026-01-16)
- MVP 发布
- 基础对话 + 主动消息
