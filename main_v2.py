"""
文件名: main_v2.py
功能: v1.2 新版命令行入口
"""

import os
from dotenv import load_dotenv

load_dotenv()


def main():
    """主入口。"""
    if not os.getenv("OPENAI_API_KEY"):
        print("错误: 请先配置 OPENAI_API_KEY")
        return
    
    from src.agents.chat_manager import get_chat_manager
    from src.models.agent_persona import get_all_agents
    from src.commands import parse_and_execute
    
    manager = get_chat_manager()
    
    print("=" * 50)
    print("AI 陪伴助手 v1.2")
    print("=" * 50)
    print()
    
    try:
        while True:
            if manager.current_session is None:
                print("命令:")
                print("  @Agent名称   - 开始私聊 (如 @小伴)")
                print("  @A @B        - 开始群聊")
                print("  /list        - 查看历史聊天")
                print("  /join <序号> - 进入历史聊天")
                print("  quit         - 退出程序")
                print()
                
                user_input = input("> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == "quit":
                    print("再见!")
                    break
                
                # 处理 /list
                if user_input == "/list":
                    sessions = manager.list_all_sessions()
                    if not sessions:
                        print("暂无历史聊天")
                    else:
                        print("-" * 40)
                        for i, s in enumerate(sessions, 1):
                            print(f"{i}. [{s['type']}] {s['title']}")
                            print(f"   ID: {s['id']}")  # 显示完整 ID
                            print(f"   更新: {s['updated_at']}")
                        print("-" * 40)
                        print("使用 /join <序号> 进入，如 /join 1")
                    print()
                    continue
                
                # 处理 /join (支持序号)
                if user_input.startswith("/join "):
                    param = user_input[6:].strip()
                    sessions = manager.list_all_sessions()
                    
                    # 尝试作为序号
                    try:
                        index = int(param) - 1
                        if 0 <= index < len(sessions):
                            session = manager.join_session(sessions[index]['id'])
                            if session:
                                print(f"已进入: {session.get_display_name()}")
                                print("输入 /history 查看历史, quit 退出聊天")
                                print()
                            continue
                    except ValueError:
                        pass
                    
                    # 尝试作为 ID 前缀
                    for s in sessions:
                        if s['id'].startswith(param):
                            session = manager.join_session(s['id'])
                            if session:
                                print(f"已进入: {session.get_display_name()}")
                                print("输入 /history 查看历史, quit 退出聊天")
                                print()
                            break
                    else:
                        print("未找到该会话，使用 /list 查看")
                    continue
                
                # 处理 @Agent
                if user_input.startswith("@"):
                    agent_ids = manager.parse_at_mentions(user_input)
                    if agent_ids:
                        session = manager.start_new_chat(agent_ids)
                        agents = ", ".join(agent_ids)
                        if session.session_type == "private":
                            print(f"开始与 {agents} 私聊")
                        else:
                            print(f"开始群聊: {agents}")
                        print("输入消息开始聊天, quit 退出")
                        print()
                    else:
                        print("未找到该 Agent")
                        print("可用 Agent:")
                        for agent in get_all_agents():
                            print(f"  @{agent.name} ({agent.id})")
                    continue
                
                # 其他命令
                result = parse_and_execute(user_input)
                if result.is_command:
                    print(result.message)
                    print()
                else:
                    print("未知命令，输入 @Agent 开始聊天")
            
            else:
                # 聊天模式
                user_input = input("你: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == "quit":
                    print("已退出聊天")
                    print()
                    manager.leave_session()
                    continue
                
                # 处理 /history
                if user_input == "/history":
                    messages = manager.get_history()
                    if not messages:
                        print("暂无历史消息")
                    else:
                        print("-" * 40)
                        for msg in messages:
                            time_str = msg.created_at.strftime("%H:%M:%S")
                            if msg.role == "user":
                                print(f"[user {time_str}]")
                            else:
                                print(f"[{msg.agent_id} {time_str}]")
                            print(msg.content)
                            print()
                        print("-" * 40)
                    continue
                
                # 处理 /export
                if user_input == "/export":
                    import json
                    data = manager.export_current_session()
                    filename = f"chat_export_{manager.current_session.id[:8]}.json"
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"已导出到 {filename}")
                    continue
                
                # 处理其他命令
                if user_input.startswith("/"):
                    result = parse_and_execute(user_input)
                    print(result.message)
                    continue
                
                # 发送消息
                responses = manager.send_message(user_input)
                for r in responses:
                    print(f"[{r['agent_name']} {r['timestamp']}]")
                    print(r['content'])
                    print()
    
    except KeyboardInterrupt:
        print("\n再见!")


if __name__ == "__main__":
    main()
