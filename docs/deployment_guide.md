# 部署指南

## 推荐: Render (免费)

### 1. 准备工作
- GitHub 账号
- [Render](https://render.com) 账号
- 代码推送到 GitHub

### 2. 部署步骤

1. **登录 Render** → New → Web Service → 选择仓库
2. **配置**:
   - **Name**: `companion-assistant`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
3. **环境变量** (Environment 标签页):

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 |
| `SUPABASE_URL` | Supabase 项目 URL |
| `SUPABASE_KEY` | Supabase anon key |
| `EMAIL_SENDER` | QQ邮箱 (可选) |
| `EMAIL_PASSWORD` | 授权码 (可选) |
| `VAPID_PUBLIC_KEY` | Web Push 公钥 (可选) |
| `VAPID_PRIVATE_KEY` | Web Push 私钥 (可选) |

4. **Deploy!**

### 3. 访问
部署完成后获得 `https://xxx.onrender.com`

iPhone:
1. Safari 打开 URL
2. 分享 → 添加到主屏幕
3. 从主屏幕打开 → `/push` 订阅推送

---

## Supabase 数据库设置

1. 创建 [Supabase](https://supabase.com) 项目
2. SQL Editor 执行 `scripts/setup_supabase_memory.sql`
3. 复制 Project URL 和 anon key 到环境变量

---

## VAPID 密钥生成

```bash
uv run python scripts/generate_vapid_keys.py
```

将输出的公钥和私钥添加到环境变量。

---

## 本地开发

```bash
uv sync
cp .env.example .env
# 编辑 .env

# 启动
uv run python server.py
```

访问 http://localhost:8000

> 注意: 本地没有 HTTPS，iOS 推送不工作。
