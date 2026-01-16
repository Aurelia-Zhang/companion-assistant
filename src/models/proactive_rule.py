"""
文件名: proactive_rule.py
功能: 定义主动消息触发规则的数据模型
在系统中的角色:
    - 定义 AI 主动发消息的触发条件
    - 支持多种规则类型：时间触发、条件触发、随机触发
    - 被 scheduler 调用来判断是否应该发送主动消息

核心逻辑:
    - RuleType: 规则类型枚举
    - ProactiveRule: 单条规则的定义
    - 规则检查器：评估当前是否满足触发条件
"""

from datetime import datetime, time
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import random


class RuleType(str, Enum):
    """主动消息规则类型。"""
    # 基于时间的规则
    TIME_IDLE = "time_idle"           # 用户空闲超过 N 分钟
    TIME_NO_WAKE = "time_no_wake"     # 到某时间用户还没起床
    TIME_PERIODIC = "time_periodic"    # 定时检查（如每小时）
    
    # 基于状态的规则
    STATUS_STUDY_LONG = "status_study_long"  # 学习时间过长，提醒休息
    STATUS_MOOD_BAD = "status_mood_bad"      # 检测到负面情绪，关心
    
    # 特殊日期
    SPECIAL_DATE = "special_date"     # 生日、节日等


class ProactiveRule(BaseModel):
    """主动消息规则定义。
    
    Attributes:
        id: 规则 ID
        name: 规则名称（用于日志和调试）
        rule_type: 规则类型
        enabled: 是否启用
        probability: 触发概率 (0.0-1.0)，让消息更随机自然
        cooldown_minutes: 冷却时间，避免频繁触发
        params: 规则参数（根据类型不同而不同）
        prompt_hint: 给 LLM 的提示，引导生成什么样的消息
    """
    id: str
    name: str
    rule_type: RuleType
    enabled: bool = True
    probability: float = 0.7  # 70% 概率触发
    cooldown_minutes: int = 60  # 默认 1 小时冷却
    params: dict = Field(default_factory=dict)
    prompt_hint: str = ""


# ==================== 默认规则集 ====================

DEFAULT_RULES = [
    ProactiveRule(
        id="idle_30min",
        name="用户空闲30分钟问候",
        rule_type=RuleType.TIME_IDLE,
        probability=0.5,
        cooldown_minutes=120,
        params={"idle_minutes": 30},
        prompt_hint="用户有一段时间没说话了，发一条轻松的问候，问问他在做什么。"
    ),
    ProactiveRule(
        id="no_wake_9am",
        name="9点还没起床提醒",
        rule_type=RuleType.TIME_NO_WAKE,
        probability=0.8,
        cooldown_minutes=60,
        params={"wake_deadline_hour": 9},
        prompt_hint="已经上午了用户还没记录起床，温柔地问候一下，看看他是否还在睡。"
    ),
    ProactiveRule(
        id="study_2h",
        name="学习2小时提醒休息",
        rule_type=RuleType.STATUS_STUDY_LONG,
        probability=0.9,
        cooldown_minutes=30,
        params={"study_minutes": 120},
        prompt_hint="用户已经学习很长时间了，提醒他休息一下，保护眼睛。"
    ),
    ProactiveRule(
        id="mood_care",
        name="负面情绪关心",
        rule_type=RuleType.STATUS_MOOD_BAD,
        probability=0.95,
        cooldown_minutes=180,
        params={"bad_keywords": ["紧张", "焦虑", "难过", "累", "烦"]},
        prompt_hint="用户最近记录了负面情绪，主动关心一下他的状态。"
    ),
]


def should_trigger(rule: ProactiveRule) -> bool:
    """根据概率判断规则是否应该触发。
    
    即使条件满足，也只有一定概率真正发消息，
    让 AI 的行为更像人，不那么机械。
    """
    if not rule.enabled:
        return False
    return random.random() < rule.probability


def get_default_rules() -> list[ProactiveRule]:
    """获取默认规则列表。"""
    return DEFAULT_RULES.copy()
