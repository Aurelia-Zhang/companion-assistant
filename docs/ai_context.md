# AI Context 上下文

> **每次新 Session 开始时，AI 必须先阅读此文件。**

## 当前版本
`v1.0.0` (MVP 完成)

## 当前阶段
- [x] Phase 0: 环境搭建
- [x] Phase 1: 核心对话 + 记忆
- [x] Phase 2: 快捷状态 + AI 提取
- [x] Phase 3: 主动消息
- [x] Phase 4: PWA 前端
- [x] Phase 5: 多智能体
- [/] v1.1 迭代开发中

## v1.0 完成的功能
- 多 Agent (小伴/学霸君/运动达人)
- 对话持久化 (SQLite)
- 快捷状态命令
- AI 自动提取
- 主动消息系统
- PWA 前端
- 部署配置

## v1.1 开发中
- 日记功能
- Token 统计
- Token 节省策略
- 大文件/长期记忆

## 数据存储
- **位置**: `data/conversations.db` (SQLite)
- **表**: 
  - LangGraph checkpoints (对话历史)
  - `user_status` (状态记录)
  - `trigger_history.json` (主动消息触发历史)

## 重要决策记录
| 日期 | 决策 | 原因 |
|------|------|------|
| 2026-01-16 | 选择 LangGraph | 强状态管理，适合复杂 Agent |
| 2026-01-16 | 选择 SQLite | 轻量，无需额外服务 |
| 2026-01-16 | 选择 PWA | iPhone 兼容，开发成本低 |
