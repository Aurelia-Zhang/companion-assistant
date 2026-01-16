"""
文件名: test_companion_agent.py
功能: 测试陪伴 Agent 的核心功能
在系统中的角色: 验证 Phase 1 实现的正确性

测试内容:
    1. Agent 能正常创建
    2. 对话能正常进行
    3. 对话历史能正确保存和读取
"""

import os
import tempfile
import pytest

# 跳过测试如果没有 API 密钥
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="需要 OPENAI_API_KEY 环境变量"
)


def test_companion_agent_creation():
    """测试: Agent 能正常创建。"""
    from src.agents.companion_agent import create_companion_agent
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        agent, saver = create_companion_agent(db_path)
        
        # 验证返回值类型
        assert agent is not None
        assert saver is not None


def test_companion_agent_response():
    """测试: Agent 能正常回复。"""
    from src.agents.companion_agent import run_companion
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        
        response = run_companion(
            "你好，能听到我说话吗？",
            thread_id="test_thread",
            db_path=db_path
        )
        
        # 验证返回了非空字符串
        assert isinstance(response, str)
        assert len(response) > 0
        print(f"AI 回复: {response}")


def test_conversation_history():
    """测试: 对话历史能正确保存和读取。"""
    from src.agents.companion_agent import run_companion, get_conversation_history
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        thread_id = "history_test"
        
        # 发送一条消息
        run_companion("测试消息", thread_id=thread_id, db_path=db_path)
        
        # 获取历史
        history = get_conversation_history(thread_id=thread_id, db_path=db_path)
        
        # 验证历史包含用户消息和 AI 回复
        assert len(history) >= 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        print(f"历史记录: {history}")


def test_persona_injection():
    """测试: 人设 Prompt 能正确生成。"""
    from src.config import get_system_prompt, DEFAULT_COMPANION_PERSONA
    
    prompt = get_system_prompt()
    
    # 验证包含人设内容
    assert "小伴" in prompt
    assert "温暖" in prompt


if __name__ == "__main__":
    # 允许直接运行测试文件
    pytest.main([__file__, "-v"])
