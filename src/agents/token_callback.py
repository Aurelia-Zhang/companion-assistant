"""
文件名: token_callback.py
功能: LangChain 回调处理器，自动记录 token 使用量
在系统中的角色:
    - 监听 LLM 调用完成事件
    - 提取 token 使用信息并保存

核心逻辑:
    1. 继承 BaseCallbackHandler
    2. 实现 on_llm_end 回调
    3. 保存 token 使用记录
"""

from datetime import datetime
from typing import Any, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from src.models.token_usage import TokenUsage, calculate_cost
from src.memory.token_store import save_usage


class TokenTrackingCallback(BaseCallbackHandler):
    """Token 追踪回调处理器。"""
    
    def __init__(self, agent_id: Optional[str] = None):
        self.agent_id = agent_id
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM 调用完成时记录 token 使用量。"""
        try:
            # 尝试从多个位置获取 token 使用信息
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            model = "gpt-4o-mini"
            
            # 方式1: 从 llm_output 获取 (老版本)
            llm_output = response.llm_output or {}
            token_usage = llm_output.get("token_usage", {})
            
            if token_usage:
                prompt_tokens = token_usage.get("prompt_tokens", 0)
                completion_tokens = token_usage.get("completion_tokens", 0)
                total_tokens = token_usage.get("total_tokens", 0)
                model = llm_output.get("model_name", model)
            
            # 方式2: 从 generations 中的 response_metadata 获取 (新版本)
            if not total_tokens and response.generations:
                for gen_list in response.generations:
                    for gen in gen_list:
                        if hasattr(gen, 'message') and hasattr(gen.message, 'response_metadata'):
                            meta = gen.message.response_metadata
                            if 'token_usage' in meta:
                                usage = meta['token_usage']
                                prompt_tokens = usage.get('prompt_tokens', 0)
                                completion_tokens = usage.get('completion_tokens', 0)
                                total_tokens = usage.get('total_tokens', 0)
                            if 'model_name' in meta:
                                model = meta['model_name']
                            break
            
            if not total_tokens:
                return
            
            # 计算成本
            cost = calculate_cost(model, prompt_tokens, completion_tokens)
            
            # 保存记录
            usage = TokenUsage(
                timestamp=datetime.now(),
                model=model,
                agent_id=self.agent_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost
            )
            save_usage(usage)
            
        except Exception as e:
            # 回调失败不应影响主流程
            print(f"[Token Callback] Error: {e}")


def get_token_callback(agent_id: Optional[str] = None) -> TokenTrackingCallback:
    """获取 token 追踪回调实例。"""
    return TokenTrackingCallback(agent_id=agent_id)
