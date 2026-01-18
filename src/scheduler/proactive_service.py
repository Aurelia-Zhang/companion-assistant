"""
文件名: proactive_service.py
功能: 主动消息服务 - 检查规则并生成主动消息
在系统中的角色:
    - 被 scheduler 定期调用
    - 检查各种规则条件是否满足
    - 调用 LLM 生成主动消息
    - 记录发送历史，避免频繁触发

核心逻辑:
    1. 遍历启用的规则
    2. 检查每条规则的条件是否满足
    3. 如果满足且通过概率检查，生成消息
    4. 记录触发时间，用于冷却判断
"""

from datetime import datetime, timedelta
from typing import Optional
import json
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.models.proactive_rule import ProactiveRule, RuleType, should_trigger, get_default_rules
from src.memory.status_store import get_today_statuses, get_recent_statuses
from src.models.status import StatusType


# 触发历史记录文件
TRIGGER_HISTORY_FILE = "data/trigger_history.json"


class ProactiveService:
    """主动消息服务。"""
    
    def __init__(self):
        self.rules = get_default_rules()
        self.trigger_history: dict[str, datetime] = {}
        self._load_trigger_history()
    
    def _load_trigger_history(self) -> None:
        """加载触发历史。"""
        if os.path.exists(TRIGGER_HISTORY_FILE):
            try:
                with open(TRIGGER_HISTORY_FILE, "r") as f:
                    data = json.load(f)
                    self.trigger_history = {
                        k: datetime.fromisoformat(v) 
                        for k, v in data.items()
                    }
            except Exception:
                self.trigger_history = {}
    
    def _save_trigger_history(self) -> None:
        """保存触发历史。"""
        os.makedirs(os.path.dirname(TRIGGER_HISTORY_FILE), exist_ok=True)
        with open(TRIGGER_HISTORY_FILE, "w") as f:
            json.dump(
                {k: v.isoformat() for k, v in self.trigger_history.items()},
                f
            )
    
    def _is_in_cooldown(self, rule: ProactiveRule) -> bool:
        """检查规则是否在冷却中。"""
        last_trigger = self.trigger_history.get(rule.id)
        if not last_trigger:
            return False
        cooldown_end = last_trigger + timedelta(minutes=rule.cooldown_minutes)
        return datetime.now() < cooldown_end
    
    def check_all_rules(self) -> Optional[tuple[ProactiveRule, str]]:
        """检查所有规则，返回第一个触发的规则和生成的消息。
        
        Returns:
            (触发的规则, 生成的消息) 或 None
        """
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            if self._is_in_cooldown(rule):
                continue
            
            if self._check_rule_condition(rule):
                if should_trigger(rule):
                    message = self._generate_message(rule)
                    if message:
                        # 记录触发
                        self.trigger_history[rule.id] = datetime.now()
                        self._save_trigger_history()
                        return (rule, message)
        
        return None
    
    def _check_rule_condition(self, rule: ProactiveRule) -> bool:
        """检查单条规则的条件是否满足。"""
        now = datetime.now()
        
        if rule.rule_type == RuleType.TIME_NO_WAKE:
            # 检查是否过了起床时间但没有起床记录
            deadline_hour = rule.params.get("wake_deadline_hour", 9)
            if now.hour >= deadline_hour:
                today_statuses = get_today_statuses()
                wake_recorded = any(
                    s.status_type == StatusType.WAKE.value 
                    for s in today_statuses
                )
                return not wake_recorded
        
        elif rule.rule_type == RuleType.STATUS_STUDY_LONG:
            # 检查是否学习时间过长
            study_limit = rule.params.get("study_minutes", 120)
            today_statuses = get_today_statuses()
            
            # 找到最后一次 study_start
            last_study_start = None
            study_ended = False
            for s in reversed(today_statuses):
                if s.status_type == StatusType.STUDY_END.value:
                    study_ended = True
                    break
                if s.status_type == StatusType.STUDY_START.value:
                    last_study_start = s.recorded_at
                    break
            
            if last_study_start and not study_ended:
                study_duration = (now - last_study_start).total_seconds() / 60
                return study_duration >= study_limit
        
        elif rule.rule_type == RuleType.STATUS_MOOD_BAD:
            # 检查最近是否有负面情绪记录
            bad_keywords = rule.params.get("bad_keywords", [])
            recent = get_recent_statuses(limit=5)
            
            for s in recent:
                if s.status_type == StatusType.MOOD.value and s.detail:
                    for keyword in bad_keywords:
                        if keyword in s.detail:
                            return True
        
        return False
    
    def _generate_message(self, rule: ProactiveRule) -> Optional[str]:
        """根据规则生成主动消息。"""
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.8)
        
        # 获取今日状态作为上下文
        today_statuses = get_today_statuses()
        status_context = "\n".join([
            f"- {s.recorded_at.strftime('%H:%M')} {s.status_type}: {s.detail or ''}"
            for s in today_statuses[-5:]  # 最近 5 条
        ]) if today_statuses else "今日暂无记录"
        
        prompt = f"""
你是"小伴"，用户的 AI 陪伴助手。现在需要主动发一条消息给用户。

## 触发原因
{rule.name}

## 消息风格指导
{rule.prompt_hint}

## 用户今日状态
{status_context}

## 要求
- 消息要简短自然，像朋友发微信一样
- 可以用 emoji
- 不要太正式或客套
- 1-2 句话即可

请直接输出消息内容，不要加任何前缀或解释：
"""
        
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            print(f"[调试] 生成主动消息失败: {e}")
            return None


# 单例实例
_service: Optional[ProactiveService] = None


def get_proactive_service() -> ProactiveService:
    """获取主动消息服务单例。"""
    global _service
    if _service is None:
        _service = ProactiveService()
    return _service


def check_and_send() -> Optional[str]:
    """检查并发送主动消息（便捷函数）。
    
    Returns:
        生成的消息，或 None 如果没有触发
    """
    from src.scheduler.push_service import notify_user
    
    service = get_proactive_service()
    result = service.check_all_rules()
    if result:
        rule, message = result
        print(f"[主动消息] 触发规则: {rule.name}")
        
        # 发送 Web Push 通知
        try:
            notify_user(message)
        except Exception as e:
            print(f"[推送] 发送失败: {e}")
        
        return message
    return None
