"""
测试 Supabase 连接的脚本
运行: uv run python scripts/test_supabase.py
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def test_connection():
    """测试数据库连接。"""
    from src.database import get_db_client, is_using_supabase
    
    print("=" * 50)
    print("Supabase 连接测试")
    print("=" * 50)
    
    # 检查配置
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ 未配置 SUPABASE_URL 或 SUPABASE_KEY")
        print("   请在 .env 文件中添加配置")
        return False
    
    print(f"✅ SUPABASE_URL: {supabase_url[:40]}...")
    print(f"✅ SUPABASE_KEY: {supabase_key[:20]}...")
    print()
    
    # 测试连接
    try:
        db = get_db_client()
        print(f"✅ 数据库客户端类型: {type(db).__name__}")
        print(f"✅ 使用 Supabase: {is_using_supabase()}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False
    
    print()
    
    # 测试写入
    print("测试写入 user_status...")
    try:
        from src.memory.status_store import save_status, get_recent_statuses
        from src.models.status import UserStatus, StatusType
        
        test_status = UserStatus(
            status_type=StatusType.NOTE,
            detail="Supabase 连接测试",
            recorded_at=datetime.now(),
            source="test"
        )
        result_id = save_status(test_status)
        print(f"✅ 写入成功，ID: {result_id}")
    except Exception as e:
        print(f"❌ 写入失败: {e}")
        return False
    
    # 测试读取
    print("测试读取 user_status...")
    try:
        statuses = get_recent_statuses(limit=5)
        print(f"✅ 读取成功，返回 {len(statuses)} 条记录")
        for s in statuses[:3]:
            print(f"   - {s.status_type}: {s.detail}")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return False
    
    print()
    print("=" * 50)
    print("🎉 所有测试通过！Supabase 连接正常")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
