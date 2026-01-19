"""
测试邮件发送的脚本
运行: uv run python scripts/test_email.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def test_email():
    """测试邮件发送。"""
    from src.tools.email_tool import send_email
    
    print("=" * 50)
    print("邮件发送测试")
    print("=" * 50)
    
    # 检查配置
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")
    
    if not sender:
        print("❌ 未配置 EMAIL_SENDER")
        return False
    print(f"✅ EMAIL_SENDER: {sender}")
    
    if not password:
        print("❌ 未配置 EMAIL_PASSWORD (授权码)")
        return False
    print(f"✅ EMAIL_PASSWORD: {'*' * 8}")
    
    if not receiver:
        print("❌ 未配置 EMAIL_RECEIVER")
        return False
    print(f"✅ EMAIL_RECEIVER: {receiver}")
    
    print()
    print("发送测试邮件...")
    
    result = send_email(
        subject="测试邮件",
        body="这是一封来自 AI 陪伴助手的测试邮件。\n\n如果你收到了这封邮件，说明邮件功能配置成功！"
    )
    
    if result["success"]:
        print(f"✅ {result['message']}")
        print()
        print("🎉 请检查你的邮箱，确认是否收到测试邮件！")
        return True
    else:
        print(f"❌ {result['message']}")
        return False


if __name__ == "__main__":
    success = test_email()
    sys.exit(0 if success else 1)
