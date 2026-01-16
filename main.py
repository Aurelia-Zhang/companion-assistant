"""
文件名: main.py
功能: 项目入口文件，运行陪伴 Agent 交互
在系统中的角色:
    - 程序的主入口
    - 加载环境变量，启动交互循环
    - 支持多轮对话和快捷命令
    - Phase 2: 集成了快捷状态记录命令

核心逻辑:
    1. 加载 .env 文件中的 API 密钥
    2. 检查用户输入是否是命令 (以 / 开头)
    3. 如果是命令，调用命令解析器处理
    4. 如果是普通消息，调用 Agent 处理
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()


def main():
    """主函数：运行交互式陪伴对话。"""
    # 检查 API 密钥是否配置
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 错误: 请先配置 OPENAI_API_KEY")
        print("   1. 复制 .env.example 为 .env")
        print("   2. 填入你的 OpenAI API 密钥")
        return

    # 延迟导入，确保环境变量已加载
    from src.agents import run_companion, get_conversation_history
    from src.commands import parse_and_execute

    print("=" * 50)
    print("🤖 AI 陪伴助手 - Phase 2 (快捷状态版本)")
    print("=" * 50)
    print("输入消息与 AI 对话")
    print("输入 /help 查看快捷命令")
    print("输入 quit 退出")
    print()
    
    # 默认对话 ID
    current_thread_id = "main_chat"
    print(f"📌 当前对话 ID: {current_thread_id}")
    print()

    while True:
        try:
            # 获取用户输入
            user_input = input("你: ").strip()

            # 检查退出命令
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 再见！你的对话已保存，下次继续~")
                break

            # 跳过空输入
            if not user_input:
                continue

            # 检查是否是快捷命令 (以 / 开头)
            if user_input.startswith("/"):
                result = parse_and_execute(user_input)
                if result.is_command:
                    print(result.message)
                    print()
                    continue
            
            # 内置命令 (不以 / 开头的特殊命令)
            if user_input.lower() == "history":
                history = get_conversation_history(current_thread_id)
                if not history:
                    print("📭 暂无对话历史\n")
                else:
                    print("\n📜 对话历史:")
                    print("-" * 40)
                    for msg in history[-10:]:
                        role = "你" if msg["role"] == "user" else "AI"
                        content = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                        print(f"  {role}: {content}")
                    print("-" * 40)
                    print()
                continue

            if user_input.lower() == "clear":
                import uuid
                current_thread_id = f"chat_{uuid.uuid4().hex[:8]}"
                print(f"✨ 已开始新对话，ID: {current_thread_id}\n")
                continue

            # 调用陪伴 Agent 获取回复
            print("小伴: ", end="", flush=True)
            response = run_companion(user_input, thread_id=current_thread_id)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n\n👋 再见！你的对话已保存，下次继续~")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            print("请检查你的 API 密钥和网络连接\n")


if __name__ == "__main__":
    main()
