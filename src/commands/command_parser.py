"""
文件名: command_parser.py
功能: 解析用户输入的快捷命令
在系统中的角色:
    - 检测用户输入是否是快捷命令 (以 / 开头)
    - 解析命令类型和参数
    - 创建对应的 UserStatus 对象并保存
    - 返回友好的确认消息

核心逻辑:
    1. 检查输入是否以 / 开头
    2. 解析命令名和参数
    3. 根据命令映射找到对应的 StatusType
    4. 创建 UserStatus 并保存到数据库
    5. 返回确认消息

支持的命令:
    /wake [备注]        - 起床
    /sleep [备注]       - 睡觉
    /shower [备注]      - 洗澡
    /meal breakfast/lunch/dinner [备注] - 用餐
    /drink [备注]       - 喝饮料
    /study start/end [备注] - 学习开始/结束
    /out [备注]         - 外出
    /back [备注]        - 回来
    /mood [心情描述]    - 记录心情
    /note [内容]        - 自由记录
    /status             - 查看今日状态
"""

from datetime import datetime
from typing import Optional, Tuple

from src.models.status import (
    UserStatus, 
    StatusType, 
    COMMAND_MAPPING,
    MEAL_SUBCOMMANDS,
    STUDY_SUBCOMMANDS,
)
from src.memory.status_store import save_status, get_today_statuses


class CommandResult:
    """命令执行结果。
    
    Attributes:
        success: 是否成功
        message: 返回给用户的消息
        is_command: 输入是否是命令
    """
    def __init__(self, success: bool, message: str, is_command: bool = True):
        self.success = success
        self.message = message
        self.is_command = is_command


def parse_and_execute(user_input: str) -> CommandResult:
    """解析并执行用户命令。
    
    这是命令解析的主入口。
    
    Args:
        user_input: 用户的原始输入
        
    Returns:
        CommandResult 对象，包含执行结果和消息
    """
    # 去除首尾空格
    user_input = user_input.strip()
    
    # 检查是否是命令 (以 / 开头)
    if not user_input.startswith("/"):
        return CommandResult(False, "", is_command=False)
    
    # 去掉开头的 /
    command_str = user_input[1:]
    
    # 分割命令和参数
    parts = command_str.split(maxsplit=1)
    if not parts:
        return CommandResult(False, "❌ 命令格式错误，请输入 /help 查看帮助")
    
    command_name = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    # 特殊命令: 查看状态
    if command_name == "status":
        return _handle_status_command()
    
    # 特殊命令: 帮助
    if command_name == "help":
        return _handle_help_command()
    
    # 查找命令映射
    if command_name not in COMMAND_MAPPING:
        return CommandResult(False, f"❌ 未知命令: /{command_name}，输入 /help 查看帮助")
    
    status_type, needs_subcommand = COMMAND_MAPPING[command_name]
    
    # 处理需要子命令的情况
    if needs_subcommand:
        return _handle_subcommand(command_name, args)
    
    # 创建状态并保存
    status = UserStatus(
        status_type=status_type,
        detail=args if args else None,
        recorded_at=datetime.now(),
        source="command"
    )
    
    save_status(status)
    
    # 生成确认消息
    message = _generate_confirmation(status_type, args)
    return CommandResult(True, message)


def _handle_subcommand(command_name: str, args: str) -> CommandResult:
    """处理需要子命令的情况 (如 /meal, /study)。"""
    parts = args.split(maxsplit=1)
    
    if not parts:
        if command_name == "meal":
            return CommandResult(False, "❌ 请指定餐食: /meal breakfast, /meal lunch, 或 /meal dinner")
        elif command_name == "study":
            return CommandResult(False, "❌ 请指定: /study start 或 /study end")
        return CommandResult(False, f"❌ 命令 /{command_name} 需要子命令")
    
    subcommand = parts[0].lower()
    detail = parts[1] if len(parts) > 1 else None
    
    # 查找子命令映射
    if command_name == "meal":
        if subcommand not in MEAL_SUBCOMMANDS:
            return CommandResult(False, f"❌ 未知餐食: {subcommand}，可选: breakfast, lunch, dinner")
        status_type = MEAL_SUBCOMMANDS[subcommand]
    elif command_name == "study":
        if subcommand not in STUDY_SUBCOMMANDS:
            return CommandResult(False, f"❌ 未知参数: {subcommand}，可选: start, end")
        status_type = STUDY_SUBCOMMANDS[subcommand]
    else:
        return CommandResult(False, f"❌ 未知命令: /{command_name}")
    
    # 创建状态并保存
    status = UserStatus(
        status_type=status_type,
        detail=detail,
        recorded_at=datetime.now(),
        source="command"
    )
    
    save_status(status)
    
    message = _generate_confirmation(status_type, detail)
    return CommandResult(True, message)


def _handle_status_command() -> CommandResult:
    """处理 /status 命令：显示今日状态。"""
    statuses = get_today_statuses()
    
    if not statuses:
        return CommandResult(True, "📭 今日暂无记录")
    
    # 格式化输出
    lines = ["📊 **今日状态**", "-" * 30]
    
    for s in statuses:
        time_str = s.recorded_at.strftime("%H:%M")
        type_emoji = _get_status_emoji(s.status_type)
        type_name = _get_status_name(s.status_type)
        detail_str = f" - {s.detail}" if s.detail else ""
        lines.append(f"  {time_str} {type_emoji} {type_name}{detail_str}")
    
    lines.append("-" * 30)
    return CommandResult(True, "\n".join(lines))


def _handle_help_command() -> CommandResult:
    """处理 /help 命令：显示帮助信息。"""
    help_text = """
📖 **快捷命令帮助**
━━━━━━━━━━━━━━━━━━
**作息**
  /wake [备注]     - 起床
  /sleep [备注]    - 睡觉
  /shower [备注]   - 洗澡

**饮食**
  /meal breakfast [备注] - 早饭
  /meal lunch [备注]     - 午饭
  /meal dinner [备注]    - 晚饭
  /drink [备注]          - 喝饮料

**学习**
  /study start [备注] - 开始学习
  /study end [备注]   - 结束学习

**其他**
  /out [备注]      - 外出
  /back [备注]     - 回来
  /mood [心情]     - 记录心情
  /note [内容]     - 自由记录

**查看**
  /status          - 查看今日状态
━━━━━━━━━━━━━━━━━━
""".strip()
    return CommandResult(True, help_text)


def _generate_confirmation(status_type: StatusType, detail: Optional[str]) -> str:
    """生成状态记录的确认消息。"""
    emoji = _get_status_emoji(status_type)
    name = _get_status_name(status_type)
    time_str = datetime.now().strftime("%H:%M")
    
    base = f"{emoji} 已记录: {name} ({time_str})"
    if detail:
        base += f"\n   📝 {detail}"
    return base


def _get_status_emoji(status_type: str) -> str:
    """获取状态对应的 emoji。"""
    emoji_map = {
        "wake": "🌅",
        "sleep": "🌙",
        "shower": "🚿",
        "meal_breakfast": "🍳",
        "meal_lunch": "🍱",
        "meal_dinner": "🍽️",
        "drink": "☕",
        "study_start": "📚",
        "study_end": "✅",
        "out": "🚶",
        "back": "🏠",
        "mood": "💭",
        "note": "📝",
    }
    return emoji_map.get(status_type, "📌")


def _get_status_name(status_type: str) -> str:
    """获取状态的中文名称。"""
    name_map = {
        "wake": "起床",
        "sleep": "睡觉",
        "shower": "洗澡",
        "meal_breakfast": "早饭",
        "meal_lunch": "午饭",
        "meal_dinner": "晚饭",
        "drink": "喝饮料",
        "study_start": "开始学习",
        "study_end": "结束学习",
        "out": "外出",
        "back": "回来",
        "mood": "心情",
        "note": "记录",
    }
    return name_map.get(status_type, status_type)
