"""
文件名: email_tool.py
功能: 邮件发送工具 (MCP 风格)
在系统中的角色:
    - 提供 AI 可调用的邮件发送功能
    - 使用 SMTP 发送邮件

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


# SMTP 配置从环境变量读取
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")


def send_email(
    to: str,
    subject: str,
    body: str,
    html: bool = False
) -> dict:
    """发送邮件。
    
    Args:
        to: 收件人邮箱
        subject: 主题
        body: 正文内容
        html: 是否为 HTML 格式
        
    Returns:
        {"success": bool, "message": str}
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        return {
            "success": False,
            "message": "SMTP 未配置。请设置 SMTP_USER 和 SMTP_PASSWORD 环境变量"
        }
    
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_FROM or SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        
        content_type = "html" if html else "plain"
        msg.attach(MIMEText(body, content_type, "utf-8"))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(msg["From"], [to], msg.as_string())
        
        return {"success": True, "message": f"邮件已发送至 {to}"}
        
    except Exception as e:
        return {"success": False, "message": f"发送失败: {str(e)}"}


@tool
def send_email_tool(to: str, subject: str, body: str) -> str:
    """发送邮件给指定收件人。
    
    Args:
        to: 收件人邮箱地址
        subject: 邮件主题
        body: 邮件正文内容
        
    Returns:
        发送结果
    """
    result = send_email(to, subject, body)
    return result["message"]


# 所有可用工具列表
EMAIL_TOOLS = [send_email_tool]


def get_email_tools():
    """获取邮件工具列表。"""
    return EMAIL_TOOLS
