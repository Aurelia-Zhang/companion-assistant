"""
测试记忆系统的脚本
运行: uv run python scripts/test_memory.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def test_memory_system():
    """测试记忆系统。"""
    print("=" * 50)
    print("记忆系统测试")
    print("=" * 50)
    
    # 1. 检查 Supabase 配置
    from src.database import is_using_supabase
    if not is_using_supabase():
        print("❌ 未配置 Supabase，记忆系统不可用")
        return False
    print("✅ Supabase 已配置")
    
    # 2. 测试记忆模块初始化
    try:
        from src.memory.supabase_memory import get_memory
        mem = get_memory()
        if mem is None:
            print("❌ 记忆模块初始化失败")
            return False
        print("✅ 记忆模块初始化成功")
    except Exception as e:
        print(f"❌ 记忆模块初始化失败: {e}")
        return False
    
    # 3. 测试添加记忆
    print("\n测试添加记忆...")
    try:
        from src.memory.supabase_memory import add_memory
        mem_id = add_memory(
            content="测试记忆：用户喜欢编程和AI技术",
            memory_type="semantic",
            importance=0.7,
            emotion_tags=["好奇"],
            entity_refs=["编程", "AI"]
        )
        print(f"✅ 记忆添加成功，ID: {mem_id}")
    except Exception as e:
        print(f"❌ 添加记忆失败: {e}")
        return False
    
    # 4. 测试搜索记忆
    print("\n测试搜索记忆...")
    try:
        from src.memory.supabase_memory import search_memories
        results = search_memories("编程技术", limit=3)
        print(f"✅ 搜索成功，找到 {len(results)} 条记忆")
        for r in results:
            print(f"   - [{r.get('memory_type')}] {r.get('content', '')[:50]}...")
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return False
    
    # 5. 测试记忆提取器
    print("\n测试记忆提取器...")
    try:
        from src.memory.memory_extractor import extract_memories
        memories = extract_memories(
            user_message="我下周三有个重要的算法考试，有点紧张",
            ai_response="别担心，我相信你一定能考好！考试前记得好好休息。"
        )
        print(f"✅ 提取成功，提取了 {len(memories)} 条记忆")
        for m in memories:
            print(f"   - [{m.get('type')}] {m.get('content', '')[:50]}...")
    except Exception as e:
        print(f"❌ 记忆提取失败: {e}")
        # 这个可能因为模型调用失败，不算致命错误
    
    print("\n" + "=" * 50)
    print("🎉 记忆系统测试完成！")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = test_memory_system()
    sys.exit(0 if success else 1)
