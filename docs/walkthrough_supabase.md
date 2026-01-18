# Supabase 云数据库迁移

> 完成日期: 2026-01-18 | ✅ 验收通过

## 完成内容

### 数据库抽象层
新建 `src/database/db_client.py`：
- `SupabaseClient` - 云数据库
- `SQLiteClient` - 本地开发
- 根据环境变量自动切换

### 重构的 Store 模块
| 文件 | 表 |
|------|---|
| `status_store.py` | user_status |
| `chat_store.py` | chat_session, chat_message |
| `token_store.py` | token_usage |
| `diary_store.py` | diary |

## 配置步骤

1. 创建 Supabase 项目
2. 执行建表 SQL
3. 配置 `.env`:
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx...
```

## 测试命令
```powershell
uv run python scripts/test_supabase.py
```

## 测试结果
```
✅ 写入成功，ID: 1
✅ 读取成功，返回 1 条记录
🎉 所有测试通过！
```
