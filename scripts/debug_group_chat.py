"""
调试群聊会话 - 检查数据库数据
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("检查数据库中的会话数据")
print("=" * 60)

from src.database import get_db_client, is_using_supabase

db = get_db_client()
print(f"使用 Supabase: {is_using_supabase()}")

# 获取最近的会话
print("\n最近 5 个会话:")
rows = db.select("chat_session", order_by="updated_at", order_desc=True, limit=5)
for row in rows:
    print(f"  ID: {row.get('id', 'N/A')[:20]}...")
    print(f"    type: {row.get('session_type')}")
    print(f"    agent_ids: {row.get('agent_ids')}")
    print(f"    title: {row.get('title')}")
    print()

# 模拟 API 调用
print("=" * 60)
print("\n模拟 API 调用流程:")

from src.agents.chat_manager import get_chat_manager
from src.models.agent_persona import get_all_agents

manager = get_chat_manager()

# 先看看现在的 current_session
print(f"当前 current_session: {manager.current_session}")

# 假设前端传来的数据
agent_ids_from_frontend = ["xiaoban", "xueba"]
print(f"\n前端传入 agent_ids: {agent_ids_from_frontend}")

# 创建新会话
session = manager.start_new_chat(agent_ids_from_frontend)
print(f"\n创建的会话:")
print(f"  ID: {session.id}")
print(f"  type: {session.session_type}")
print(f"  agent_ids: {session.agent_ids}")

# 现在发送消息
print("\n发送消息 '你们好'...")
print(f"current_session.session_type = {manager.current_session.session_type}")
print(f"current_session.agent_ids = {manager.current_session.agent_ids}")

# 不实际调用 LLM，只检查逻辑
if manager.current_session.session_type == "private":
    print("→ 走 private 逻辑，只调用第一个 agent")
else:
    print("→ 走 group 逻辑，遍历所有 agent")
    for agent_id in manager.current_session.agent_ids:
        print(f"   会调用: {agent_id}")
