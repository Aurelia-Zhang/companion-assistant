"""
生成 VAPID 密钥对的脚本
运行: uv run python scripts/generate_vapid_keys.py
"""

import subprocess
import sys

def generate_keys():
    """生成 VAPID 密钥对。"""
    print("=" * 50)
    print("VAPID 密钥生成")
    print("=" * 50)
    
    try:
        from py_vapid import Vapid
        
        vapid = Vapid()
        vapid.generate_keys()
        
        print("\n请将以下内容添加到 .env 文件:\n")
        print(f"VAPID_PUBLIC_KEY={vapid.public_key.decode('utf-8') if isinstance(vapid.public_key, bytes) else vapid.public_key}")
        print(f"VAPID_PRIVATE_KEY={vapid.private_key.decode('utf-8') if isinstance(vapid.private_key, bytes) else vapid.private_key}")
        
    except ImportError:
        # 使用 pywebpush 的方式
        from pywebpush import webpush
        import base64
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        
        # 生成 ECDSA 密钥对
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        public_key = private_key.public_key()
        
        # 导出为 base64url 格式
        private_bytes = private_key.private_numbers().private_value.to_bytes(32, 'big')
        private_b64 = base64.urlsafe_b64encode(private_bytes).rstrip(b'=').decode('utf-8')
        
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        public_b64 = base64.urlsafe_b64encode(public_bytes).rstrip(b'=').decode('utf-8')
        
        print("\n请将以下内容添加到 .env 文件:\n")
        print(f"VAPID_PUBLIC_KEY={public_b64}")
        print(f"VAPID_PRIVATE_KEY={private_b64}")
    
    print("\n" + "=" * 50)
    print("记得将 VAPID_PUBLIC_KEY 也配置到前端!")
    print("=" * 50)


if __name__ == "__main__":
    generate_keys()
