# 邮件功能集成

> 完成日期: 2026-01-18 | ✅ 验收通过

## 功能

AI Agent 现在可以主动发送邮件给用户（日报、提醒等）。

## 配置

`.env` 添加：
```bash
EMAIL_SMTP_HOST=smtp.qq.com
EMAIL_SMTP_PORT=465
EMAIL_USE_SSL=true
EMAIL_SENDER=你的QQ@qq.com
EMAIL_PASSWORD=QQ邮箱授权码
EMAIL_RECEIVER=收件邮箱
```

## 测试

```powershell
uv run python scripts/test_email.py
```

## 使用

AI 可自动判断何时发送邮件。也可主动要求：
```
@小伴 帮我发一封测试邮件
```

## 关键文件

- `src/tools/email_tool.py` - 邮件工具
- `src/agents/multi_agent.py` - 集成到 Agent
