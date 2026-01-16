"""
文件名: scheduler_runner.py
功能: APScheduler 调度器运行器
在系统中的角色:
    - 启动后台定时任务
    - 定期调用 proactive_service 检查规则
    - 触发主动消息时通知主程序

核心逻辑:
    1. 创建 APScheduler 实例
    2. 添加定时任务（如每 5 分钟检查一次）
    3. 在后台线程运行
    4. 触发时将消息放入队列，供主程序处理
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import queue
from typing import Optional

from src.scheduler.proactive_service import check_and_send


# 消息队列，用于将主动消息传递给主程序
message_queue: queue.Queue = queue.Queue()

# 调度器实例
_scheduler: Optional[BackgroundScheduler] = None


def _check_job():
    """定时检查任务。"""
    message = check_and_send()
    if message:
        message_queue.put(message)


def start_scheduler(check_interval_minutes: int = 5) -> BackgroundScheduler:
    """启动后台调度器。
    
    Args:
        check_interval_minutes: 检查间隔（分钟）
        
    Returns:
        启动的调度器实例
    """
    global _scheduler
    
    if _scheduler is not None:
        return _scheduler
    
    _scheduler = BackgroundScheduler()
    
    # 添加定时检查任务
    _scheduler.add_job(
        _check_job,
        trigger=IntervalTrigger(minutes=check_interval_minutes),
        id="proactive_check",
        name="主动消息检查",
        replace_existing=True
    )
    
    _scheduler.start()
    print(f"[调度器] 已启动，每 {check_interval_minutes} 分钟检查一次")
    
    return _scheduler


def stop_scheduler():
    """停止调度器。"""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None


def get_pending_message() -> Optional[str]:
    """获取待发送的主动消息（非阻塞）。
    
    Returns:
        消息内容，或 None 如果队列为空
    """
    try:
        return message_queue.get_nowait()
    except queue.Empty:
        return None


def trigger_check_now() -> Optional[str]:
    """立即触发一次检查（用于测试）。
    
    Returns:
        生成的消息，或 None
    """
    return check_and_send()
