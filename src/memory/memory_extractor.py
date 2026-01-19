"""
文件名: memory_extractor.py
功能: 从对话中自动提取值得记忆的内容
在系统中的角色:
    - 自动分析对话，识别值得长期记忆的信息
    - 对提取的内容进行分类和重要性评估
    - 存储到 Supabase 记忆库

核心逻辑:
    1. 接收用户消息和 AI 回复
    2. 使用 LLM 判断是否有值得记忆的内容
    3. 提取并分类 (情景/语义/情感/预测)
    4. 自动存储到记忆库
"""

import json
from typing import Optional, List, Dict
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage

from src.utils.llm_factory import create_llm_simple
from src.memory.supabase_memory import add_memory, get_memory


# 记忆提取的 System Prompt
MEMORY_EXTRACTOR_PROMPT = """
你是一个记忆提取助手。你的任务是从用户和 AI 的对话中识别值得长期记忆的信息。

## 记忆类型
1. **semantic** (语义记忆): 用户的个人信息、偏好、习惯、事实
   - 例: "用户是计算机专业研究生"、"用户喜欢跑步"、"用户不喜欢吃辣"
   
2. **episodic** (情景记忆): 具体事件、经历、对话片段
   - 例: "用户今天考试考了90分很开心"、"用户昨天和朋友去看电影了"
   
3. **emotional** (情感记忆): 情绪变化、情感关联、心理状态
   - 例: "用户提到考试时会紧张"、"用户最近工作压力很大"
   
4. **predictive** (预测记忆): 未来计划、重要日期、周期性事件
   - 例: "用户下周三有算法考试"、"用户每周四有网球课"

## 重要性评分 (0.0-1.0)
- 0.8-1.0: 极重要 (生日、重大事件、核心偏好)
- 0.5-0.7: 重要 (计划、情绪变化、一般偏好)
- 0.3-0.5: 一般 (日常事件、小细节)
- 0.0-0.3: 不重要 (不值得记忆)

## 输出格式
如果有值得记忆的内容，返回 JSON 数组:
```json
[
  {
    "content": "用户是计算机专业的研究生，目前在准备毕业论文",
    "type": "semantic",
    "importance": 0.8,
    "emotion_tags": [],
    "entity_refs": ["毕业论文"]
  },
  {
    "content": "用户下周三下午有算法期末考试",
    "type": "predictive", 
    "importance": 0.9,
    "emotion_tags": ["紧张"],
    "entity_refs": ["算法考试", "下周三"]
  }
]
```

如果没有值得记忆的内容，返回空数组:
```json
[]
```

## 注意事项
- 只提取**明确、具体**的信息，不要过度推断
- 日常寒暄（你好、再见）**不需要记忆**
- 已知信息**不需要重复记忆**
- **合并相关信息**为一条记忆，不要过于碎片化
- 用户的**情感状态**很重要，要注意捕捉
"""


def extract_memories(
    user_message: str,
    ai_response: str,
    session_id: str = None
) -> List[Dict]:
    """从对话中提取记忆。
    
    Args:
        user_message: 用户消息
        ai_response: AI 回复
        session_id: 会话 ID
        
    Returns:
        提取到的记忆列表
    """
    # 检查是否可用
    if get_memory() is None:
        return []
    
    # 构建对话内容
    conversation = f"""
用户: {user_message}

AI: {ai_response}
"""
    
    # 使用较小的模型降低成本
    llm = create_llm_simple(model="gpt-4o-mini", temperature=0)
    
    messages = [
        SystemMessage(content=MEMORY_EXTRACTOR_PROMPT),
        HumanMessage(content=f"请分析以下对话，提取值得记忆的内容:\n\n{conversation}")
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # 解析 JSON
        # 处理可能的 markdown 代码块
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        memories = json.loads(content)
        
        if not isinstance(memories, list):
            return []
        
        # 过滤低重要性的记忆
        memories = [m for m in memories if m.get("importance", 0) >= 0.3]
        
        # 存储到记忆库
        stored_count = 0
        for mem in memories:
            try:
                add_memory(
                    content=mem.get("content", ""),
                    memory_type=mem.get("type", "episodic"),
                    importance=mem.get("importance", 0.5),
                    emotion_tags=mem.get("emotion_tags", []),
                    entity_refs=mem.get("entity_refs", []),
                    source_session=session_id
                )
                stored_count += 1
            except Exception as e:
                print(f"[Memory] 存储失败: {e}")
        
        if stored_count > 0:
            print(f"[Memory] 提取并存储了 {stored_count} 条记忆")
        
        return memories
        
    except json.JSONDecodeError:
        print("[Memory] JSON 解析失败")
        return []
    except Exception as e:
        print(f"[Memory] 提取失败: {e}")
        return []


def process_conversation_for_memory(
    user_message: str,
    ai_response: str,
    session_id: str = None
) -> int:
    """处理对话并提取记忆的便捷函数。
    
    Returns:
        存储的记忆数量
    """
    memories = extract_memories(user_message, ai_response, session_id)
    return len(memories)
