"""
测试会话查询
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

print("=" * 50)
print("调试会话查询")
print("=" * 50)

# 1. 检查是否使用 Supabase
from src.database import get_db_client, is_using_supabase

db = get_db_client()
print(f"使用 Supabase: {is_using_supabase()}")

# 2. 直接查询 chat_session 表
print("\n直接查询 Supabase chat_session 表:")
try:
    rows = db.select("chat_session", limit=5)
    print(f"找到 {len(rows)} 条记录")
    for row in rows:
        print(f"  - {row.get('id', 'N/A')[:20]}... type={row.get('session_type')}")
except Exception as e:
    print(f"查询失败: {e}")

# 3. 通过 chat_store 查询
print("\n通过 chat_store.list_sessions 查询:")
try:
    from src.memory.chat_store import list_sessions
    sessions = list_sessions(limit=5)
    print(f"找到 {len(sessions)} 个会话")
    for s in sessions:
        print(f"  - {s.id[:20]}... type={s.session_type}")
except Exception as e:
    print(f"查询失败: {e}")

# 4. 检查表是否存在（Supabase）
if is_using_supabase():
    print("\n检查 Supabase 表结构:")
    try:
        result = db.client.table("chat_session").select("id").limit(1).execute()
        print(f"chat_session 表存在，返回: {result.data}")
    except Exception as e:
        print(f"表可能不存在: {e}")
