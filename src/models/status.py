"""
文件名: status.py
功能: 定义用户状态相关的数据模型
在系统中的角色:
    - 这是 Phase 2 快捷状态记录的核心数据结构
    - 定义了用户可以记录的各种状态类型
    - 被 status_store.py 用于存储，被命令解析器用于创建状态

核心逻辑:
    - StatusType: 枚举所有支持的状态类型
    - UserStatus: 单条状态记录的数据模型
    - 支持带备注的状态记录
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class StatusType(str, Enum):
    """用户状态类型枚举。
    
    定义了所有支持的快捷状态命令。
    使用 str 作为基类，方便序列化和比较。
    """
    # 作息相关
    WAKE = "wake"           # 起床
    SLEEP = "sleep"         # 睡觉
    SHOWER = "shower"       # 洗澡
    
    # 饮食相关
    MEAL_BREAKFAST = "meal_breakfast"   # 早饭
    MEAL_LUNCH = "meal_lunch"           # 午饭
    MEAL_DINNER = "meal_dinner"         # 晚饭
    DRINK = "drink"                     # 喝饮料 (咖啡/奶茶等)
    
    # 学习/工作相关
    STUDY_START = "study_start"     # 开始学习
    STUDY_END = "study_end"         # 结束学习
    
    # 外出/活动
    OUT = "out"             # 外出
    BACK = "back"           # 回来
    
    # 心情/情绪
    MOOD = "mood"           # 记录心情
    
    # 通用
    NOTE = "note"           # 自由记录


class UserStatus(BaseModel):
    """用户状态记录模型。
    
    使用 Pydantic 模型，方便验证和序列化。
    
    Attributes:
        id: 数据库自增 ID (创建时可选)
        status_type: 状态类型
        detail: 可选的详细信息/备注
        recorded_at: 记录时间
        source: 记录来源 ("command" = 用户命令, "ai" = AI自动提取)
    """
    id: Optional[int] = None
    status_type: StatusType
    detail: Optional[str] = None
    recorded_at: datetime = Field(default_factory=datetime.now)
    source: str = "command"  # "command" 或 "ai"
    
    class Config:
        # 允许使用枚举值
        use_enum_values = True


# ==================== 命令映射 ====================
# 将用户输入的命令映射到状态类型
# 格式: 命令 -> (状态类型, 是否需要子命令)

COMMAND_MAPPING = {
    "wake": (StatusType.WAKE, False),
    "sleep": (StatusType.SLEEP, False),
    "shower": (StatusType.SHOWER, False),
    "meal": (None, True),  # 需要子命令: breakfast/lunch/dinner
    "drink": (StatusType.DRINK, False),
    "study": (None, True),  # 需要子命令: start/end
    "out": (StatusType.OUT, False),
    "back": (StatusType.BACK, False),
    "mood": (StatusType.MOOD, False),
    "note": (StatusType.NOTE, False),
}

MEAL_SUBCOMMANDS = {
    "breakfast": StatusType.MEAL_BREAKFAST,
    "lunch": StatusType.MEAL_LUNCH,
    "dinner": StatusType.MEAL_DINNER,
}

STUDY_SUBCOMMANDS = {
    "start": StatusType.STUDY_START,
    "end": StatusType.STUDY_END,
}
