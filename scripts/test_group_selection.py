"""
测试群聊智能选择逻辑（不实际调用 LLM）
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("群聊智能选择测试")
print("=" * 60)

from src.agents.chat_manager import ChatManager
from src.models.chat_session import ChatSession

# 创建测试 manager 和 session
manager = ChatManager()
manager.current_session = ChatSession(
    session_type="group",
    agent_ids=["xiaoban", "xueba"]
)

print(f"测试会话: {manager.current_session.agent_ids}")
print()

# 测试用例
test_cases = [
    ("你好", "随机选择"),
    ("@all 大家好", "@全体"),
    ("@全体 你们好啊", "@全体"),
    ("@xueba 这道题怎么做", "@xueba"),
    ("@学霸君 帮我复习", "@学霸君"),
    ("@xiaoban @xueba 你们好", "@ 多个"),
    ("我要复习考试", "关键词: 考试/复习"),
    ("今天天气不错", "随机选择"),
]

for content, expected in test_cases:
    print(f"消息: '{content}'")
    print(f"预期: {expected}")
    
    # 只测试选择逻辑，不调用 LLM
    responders = manager._select_group_responders(content)
    print(f"实际: {[a.name for a in responders]}")
    print()

print("=" * 60)
print("测试完成")
