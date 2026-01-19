"""
生成 VAPID 密钥对
"""
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import base64

# 生成 ECDSA 密钥对
private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
public_key = private_key.public_key()

# 导出私钥
private_bytes = private_key.private_numbers().private_value.to_bytes(32, 'big')
private_b64 = base64.urlsafe_b64encode(private_bytes).rstrip(b'=').decode('utf-8')

# 导出公钥
public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)
public_b64 = base64.urlsafe_b64encode(public_bytes).rstrip(b'=').decode('utf-8')

print("=" * 60)
print("复制以下内容到 Render 的环境变量:")
print("=" * 60)
print()
print(f"VAPID_PUBLIC_KEY={public_b64}")
print()
print(f"VAPID_PRIVATE_KEY={private_b64}")
print()
print("=" * 60)
