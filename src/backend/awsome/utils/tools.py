import base64
from awsome.settings import get_config
from cryptography.fernet import Fernet
import hashlib

class EncryptionTool:
    def __init__(self):
        # 从配置中获取盐值并编码为字节
        self.SALT = get_config("extra.salt").encode()
        # 生成密钥，使用盐值来增强安全性
        self.key = self.generate_key()
        self.cipher = Fernet(self.key)

    def generate_key(self) -> bytes:
        """生成基于盐的密钥"""
        # 使用 SHA-256 哈希函数生成密钥
        return base64.urlsafe_b64encode(hashlib.sha256(self.SALT).digest())

    def encrypt(self, password: str) -> str:
        """加密密码"""
        password_bytes = password.encode()
        encrypted_password = self.cipher.encrypt(password_bytes)
        return encrypted_password.decode()

    def decrypt(self, encrypted_password: str) -> str:
        """解密密码"""
        encrypted_bytes = encrypted_password.encode()
        decrypted_password = self.cipher.decrypt(encrypted_bytes)
        return decrypted_password.decode()

    def get_key(self) -> str:
        """获取密钥"""
        return self.key.decode()


# 示例使用
if __name__ == "__main__":
    tool = EncryptionTool()

    # 加密密码
    password = "你好"
    encrypted = tool.encrypt(password)
    print(f"Encrypted: {encrypted}")

    # 解密密码
    decrypted = tool.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")

    # 输出密钥
    print(f"Key: {tool.get_key()}")