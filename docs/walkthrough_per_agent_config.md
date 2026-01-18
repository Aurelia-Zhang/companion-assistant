# Per-Agent API 配置 + 代码统一

> 记录日期: 2026-01-18 | ✅ 验收通过

## 完成内容

### 1. 创建统一的 LLM 工厂

新文件 `src/utils/llm_factory.py`：
- `create_llm(agent, temperature)` - 支持 per-agent 配置
- `create_llm_simple(model, temperature)` - 简单场景

### 2. 重构 LLM 调用点

| 文件 | 改动 |
|------|------|
| `companion_agent.py` | 使用 `create_llm()` + 正确记录 agent_id |
| `multi_agent.py` | 删除重复代码，统一使用工厂函数 |
| `proactive_service.py` | 使用 `create_llm_simple()` |
| `info_extractor.py` | 使用 `create_llm_simple()` |

### 3. API 统一 (v1.2)

重写 `src/api/routes/chat.py`：
- `/send` - 统一使用 `chat_manager`
- `/sessions` - 新增会话列表 API
- `/sessions/{id}/history` - 新增历史消息 API
- `/agents` - 返回 Agent 的 model 信息
- 旧 API 移至 `/send/legacy`

### 4. 配置更新

`.env.example` 新增 per-agent 配置示例：
```
AGENT_XUEBA_API_KEY=sk-xxx
AGENT_XUEBA_API_BASE=https://api.different-provider.com/v1
```

### 5. 废弃标记

`main.py` 添加废弃警告，引导使用 `main_v2.py`

---

## 关键文件

| 文件 | 用途 |
|------|------|
| `src/utils/llm_factory.py` | [NEW] 统一 LLM 创建 |
| `src/api/routes/chat.py` | [MODIFIED] 使用 chat_manager |
| `main.py` | [DEPRECATED] 已废弃 |
| `main_v2.py` | [推荐] 新版 CLI 入口 |

---

## 验收测试

### 自动测试
```powershell
cd e:\Dev\project\companion-assistant
uv run pytest tests/ -v
```

### 手动测试

1. **测试 main_v2.py**:
```powershell
uv run python main_v2.py
# @小伴 你好
# @学霸君 什么是算法
```

2. **测试 API 服务**:
```powershell
uv run python server.py
# 访问 http://localhost:8000
```

---

## 架构变化

```
Before:
  main.py → companion_agent (硬编码)
  main_v2.py → chat_manager → multi_agent (per-agent)
  API /send → companion_agent (硬编码)
  API /multi → multi_agent (per-agent)

After:
  main.py → [DEPRECATED]
  main_v2.py → chat_manager → multi_agent (per-agent)
  API /send → chat_manager (per-agent) ✅
  API /send/legacy → companion_agent (per-agent) ✅
```

所有 LLM 调用现在都支持 per-agent 配置！
