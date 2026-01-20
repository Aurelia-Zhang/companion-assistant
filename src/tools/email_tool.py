"""
文件名: email_tool.py
功能: 邮件发送工具 (MCP 风格)
在系统中的角色:
    - 提供 AI 可调用的邮件发送功能
    - 使用 SMTP 发送邮件（支持 SSL 和 TLS）

核心逻辑:
    1. send_email: 发送邮件
    2. 作为 LangChain Tool 供 Agent 调用
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from langchain_core.tools import tool


def _get_smtp_config() -> dict:
    """获取 SMTP 配置。"""
    return {
        "host": os.getenv("EMAIL_SMTP_HOST", "smtp.qq.com"),
        "port": int(os.getenv("EMAIL_SMTP_PORT", "465")),
        "use_ssl": os.getenv("EMAIL_USE_SSL", "true").lower() == "true",
        "sender": os.getenv("EMAIL_SENDER", ""),
        "password": os.getenv("EMAIL_PASSWORD", ""),
        "receiver": os.getenv("EMAIL_RECEIVER", ""),
    }


def send_email(
    subject: str,
    body: str,
    to: Optional[str] = None,
    html: bool = False
) -> dict:
    """发送邮件。
    
    Args:
        subject: 主题
        body: 正文内容
        to: 收件人邮箱（可选，默认使用 EMAIL_RECEIVER）
        html: 是否为 HTML 格式
        
    Returns:
        {"success": bool, "message": str}
    """
    config = _get_smtp_config()
    
    if not config["sender"] or not config["password"]:
        return {
            "success": False,
            "message": "SMTP 未配置。请设置 EMAIL_SENDER 和 EMAIL_PASSWORD 环境变量"
        }
    
    receiver = to or config["receiver"]
    if not receiver:
        return {
            "success": False,
            "message": "未指定收件人。请设置 EMAIL_RECEIVER 环境变量或传入 to 参数"
        }
    
    try:
        msg = MIMEMultipart()
        msg["From"] = config["sender"]
        msg["To"] = receiver
        msg["Subject"] = f"[AI助手] {subject}"
        
        content_type = "html" if html else "plain"
        msg.attach(MIMEText(body, content_type, "utf-8"))
        
        # 设置超时时间 (秒)
        timeout = 10
        
        # 根据配置选择 SSL 或 TLS
        if config["use_ssl"]:
            # QQ邮箱等使用 SSL (端口 465)
            server = smtplib.SMTP_SSL(config["host"], config["port"], timeout=timeout)
            try:
                server.login(config["sender"], config["password"])
                server.send_message(msg)
            finally:
                try:
                    server.quit()
                except:
                    pass  # 忽略关闭连接时的错误
        else:
            # Gmail 等使用 TLS (端口 587)
            with smtplib.SMTP(config["host"], config["port"], timeout=timeout) as server:
                server.starttls()
                server.login(config["sender"], config["password"])
                server.send_message(msg)
        
        return {"success": True, "message": f"邮件已发送至 {receiver}"}
        
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "邮箱认证失败，请检查邮箱地址和授权码"}
    except TimeoutError:
        return {"success": False, "message": "连接邮件服务器超时，请检查网络"}
    except OSError as e:
        return {"success": False, "message": f"网络错误: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"发送失败: {str(e)}"}


@tool
def send_email_tool(subject: str, body: str) -> str:
    """发送邮件给用户。
    
    用于发送重要提醒、日报汇总等信息。
    请确保内容简洁有用，不要发送无意义的邮件。
    
    Args:
        subject: 邮件主题，简短描述邮件内容
        body: 邮件正文，详细内容
        
    Returns:
        发送结果
    """
    result = send_email(subject, body)
    if result["success"]:
        return f"✅ {result['message']}"
    return f"❌ {result['message']}"


# 所有可用工具列表
EMAIL_TOOLS = [send_email_tool]


def get_email_tools():
    """获取邮件工具列表。"""
    return EMAIL_TOOLS


# 便捷函数
def send_notification(subject: str, body: str) -> bool:
    """发送通知邮件（便捷函数）。"""
    result = send_email(subject, body)
    return result["success"]
