"""
文件名: push_service.py
功能: Web Push 推送服务
在系统中的角色:
    - 管理订阅
    - 发送推送通知

核心逻辑:
    1. 生成 VAPID 密钥对
    2. 保存订阅信息
    3. 发送推送消息

注意: iOS Safari PWA 从 16.4 开始支持 Web Push
用户必须将 PWA 添加到主屏幕才能收到推送
"""

import json
import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

# pywebpush 需要安装: uv add pywebpush
try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False


# VAPID 配置
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_CLAIMS = {"sub": "mailto:your-email@example.com"}

# 订阅存储路径
SUBSCRIPTIONS_FILE = "data/push_subscriptions.json"


@dataclass
class PushSubscription:
    """推送订阅信息。"""
    endpoint: str
    keys: dict  # {"p256dh": "...", "auth": "..."}
    user_id: str = "default"


def load_subscriptions() -> list[PushSubscription]:
    """加载所有订阅。"""
    if not os.path.exists(SUBSCRIPTIONS_FILE):
        return []
    
    with open(SUBSCRIPTIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [PushSubscription(**s) for s in data]


def save_subscriptions(subscriptions: list[PushSubscription]) -> None:
    """保存订阅。"""
    os.makedirs(os.path.dirname(SUBSCRIPTIONS_FILE), exist_ok=True)
    
    data = [{"endpoint": s.endpoint, "keys": s.keys, "user_id": s.user_id} for s in subscriptions]
    with open(SUBSCRIPTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_subscription(subscription: PushSubscription) -> None:
    """添加新订阅。"""
    subscriptions = load_subscriptions()
    
    # 检查是否已存在
    for sub in subscriptions:
        if sub.endpoint == subscription.endpoint:
            return  # 已存在
    
    subscriptions.append(subscription)
    save_subscriptions(subscriptions)


def remove_subscription(endpoint: str) -> None:
    """移除订阅。"""
    subscriptions = load_subscriptions()
    subscriptions = [s for s in subscriptions if s.endpoint != endpoint]
    save_subscriptions(subscriptions)


def send_push_notification(title: str, body: str, user_id: str = None) -> int:
    """发送推送通知到所有订阅。
    
    Returns:
        成功发送的数量
    """
    if not WEBPUSH_AVAILABLE:
        print("[Push] pywebpush not installed")
        return 0
    
    if not VAPID_PRIVATE_KEY:
        print("[Push] VAPID_PRIVATE_KEY not configured")
        return 0
    
    subscriptions = load_subscriptions()
    if user_id:
        subscriptions = [s for s in subscriptions if s.user_id == user_id]
    
    payload = json.dumps({
        "title": title,
        "body": body,
        "icon": "/icon-192.png",
        "badge": "/icon-192.png"
    })
    
    success_count = 0
    failed_endpoints = []
    
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": sub.keys
                },
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
            success_count += 1
        except WebPushException as e:
            print(f"[Push] Failed: {e}")
            if e.response and e.response.status_code in [404, 410]:
                failed_endpoints.append(sub.endpoint)
    
    # 移除失效订阅
    for endpoint in failed_endpoints:
        remove_subscription(endpoint)
    
    return success_count


def get_vapid_public_key() -> str:
    """获取 VAPID 公钥供前端使用。"""
    return VAPID_PUBLIC_KEY


# 便捷函数
def notify_user(message: str, user_id: str = None) -> bool:
    """发送推送通知的简化接口。"""
    count = send_push_notification("AI 陪伴助手", message, user_id)
    return count > 0
