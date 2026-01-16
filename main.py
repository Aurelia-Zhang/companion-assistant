"""
文件名: main.py
功能: 项目入口文件，用于测试和运行 Agent
在系统中的角色:
    - 程序的主入口
    - 加载环境变量，初始化 Agent，启动交互循环

核心逻辑:
    1. 加载 .env 文件中的 API 密钥
    2. 进入交互循环：等待用户输入 -> 调用 Agent -> 打印回复
    3. 输入 'quit' 或 'exit' 退出
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()


def main():
    """主函数：运行交互式对话。"""
    # 检查 API 密钥是否配置
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 错误: 请先配置 OPENAI_API_KEY")
        print("   1. 复制 .env.example 为 .env")
        print("   2. 填入你的 OpenAI API 密钥")
        return

    # 延迟导入，确保环境变量已加载
    from src.agents import run_agent

    print("=" * 50)
    print("🤖 AI 陪伴助手 - Hello World 版本")
    print("=" * 50)
    print("输入消息与 AI 对话，输入 'quit' 退出\n")

    while True:
        try:
            # 获取用户输入
            user_input = input("你: ").strip()

            # 检查退出命令
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 再见！")
                break

            # 跳过空输入
            if not user_input:
                continue

            # 调用 Agent 获取回复
            print("AI: ", end="", flush=True)
            response = run_agent(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            print("请检查你的 API 密钥和网络连接\n")


if __name__ == "__main__":
    main()
