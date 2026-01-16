# 部署指南

## Railway 一键部署

### 1. 准备工作
- GitHub 账号
- Railway 账号 (railroad.app)
- 项目推送到 GitHub

### 2. 部署步骤

```bash
# 1. 推送代码到 GitHub
git add .
git commit -m "v1.0.0 ready for deploy"
git push origin main
```

然后在 Railway:
1. 登录 railway.app
2. New Project → Deploy from GitHub repo
3. 选择你的仓库
4. 添加环境变量:
   - `OPENAI_API_KEY` = `sk-xxx`
   - `AGENT_XUEBA_API_KEY` = `sk-xxx` (可选，学霸君专用)
   - `AGENT_TIYU_API_KEY` = `sk-xxx` (可选，运动达人专用)
5. Deploy!

### 3. 获取访问地址
部署成功后，Railway 会分配一个 URL，如:
`https://your-app.up.railway.app`

用 iPhone Safari 访问这个 URL，然后添加到主屏幕即可！

---

## 环境变量说明

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `OPENAI_API_KEY` | ✅ | 默认 API Key |
| `AGENT_XUEBA_API_KEY` | ❌ | 学霸君专用 Key |
| `AGENT_TIYU_API_KEY` | ❌ | 运动达人专用 Key |

如果某个 Agent 没有专用 Key，会使用默认的 `OPENAI_API_KEY`。

---

## 其他平台

### Fly.io
```bash
fly launch
fly secrets set OPENAI_API_KEY=sk-xxx
fly deploy
```

### Render
创建 `render.yaml` 或直接在 Dashboard 配置。
