"""
Push 订阅 API 路由
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/push", tags=["push"])


class SubscriptionRequest(BaseModel):
    """订阅请求。"""
    endpoint: str
    keys: dict  # {"p256dh": "...", "auth": "..."}
    user_id: str = "default"


@router.post("/subscribe")
async def subscribe(request: SubscriptionRequest):
    """订阅推送通知。"""
    from src.scheduler.push_service import add_subscription, PushSubscription
    
    sub = PushSubscription(
        endpoint=request.endpoint,
        keys=request.keys,
        user_id=request.user_id
    )
    add_subscription(sub)
    
    return {"status": "subscribed"}


@router.post("/unsubscribe")
async def unsubscribe(request: SubscriptionRequest):
    """取消订阅。"""
    from src.scheduler.push_service import remove_subscription
    
    remove_subscription(request.endpoint)
    return {"status": "unsubscribed"}


@router.get("/vapid-key")
async def get_vapid_key():
    """获取 VAPID 公钥。"""
    from src.scheduler.push_service import get_vapid_public_key
    
    return {"publicKey": get_vapid_public_key()}


@router.post("/test")
async def test_push():
    """测试推送通知。"""
    from src.scheduler.push_service import send_push_notification
    
    count = send_push_notification("测试", "这是一条测试推送")
    return {"sent": count}
