"""
RSA 加密工具模块
提供 RSA 密钥对生成、公钥获取和密码解密功能
"""
import os
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend


class RSAUtils:
    """RSA 加密工具类"""
    
    def __init__(self, private_key_path='instance/rsa_private_key.pem', 
                 public_key_path='instance/rsa_public_key.pem'):
        """
        初始化 RSA 工具
        
        Args:
            private_key_path: 私钥文件路径
            public_key_path: 公钥文件路径
        """
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path
        self._private_key = None
        self._public_key = None
        self._load_or_generate_keys()
    
    def _load_or_generate_keys(self):
        """加载或生成 RSA 密钥对"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.private_key_path), exist_ok=True)
        
        # 尝试加载现有密钥
        if os.path.exists(self.private_key_path) and os.path.exists(self.public_key_path):
            try:
                with open(self.private_key_path, 'rb') as f:
                    self._private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None,
                        backend=default_backend()
                    )
                with open(self.public_key_path, 'rb') as f:
                    self._public_key = serialization.load_pem_public_key(
                        f.read(),
                        backend=default_backend()
                    )
                return
            except Exception as e:
                print(f"[RSA] 加载密钥失败，将重新生成: {str(e)}")
        
        # 生成新密钥对
        self._generate_keys()
    
    def _generate_keys(self):
        """生成新的 RSA 密钥对"""
        # 生成 2048 位 RSA 密钥对
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self._public_key = self._private_key.public_key()
        
        # 保存私钥
        private_pem = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open(self.private_key_path, 'wb') as f:
            f.write(private_pem)
        
        # 保存公钥
        public_pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        with open(self.public_key_path, 'wb') as f:
            f.write(public_pem)
        
        print(f"[RSA] 已生成新的密钥对: {self.private_key_path}, {self.public_key_path}")
    
    def get_public_key_pem(self):
        """
        获取 PEM 格式的公钥字符串
        
        Returns:
            str: PEM 格式的公钥
        """
        public_pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return public_pem.decode('utf-8')
    
    def get_public_key_base64(self):
        """
        获取 Base64 编码的公钥（用于前端使用）
        
        Returns:
            str: Base64 编码的公钥
        """
        public_pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return base64.b64encode(public_pem).decode('utf-8')
    
    def decrypt_password(self, encrypted_password_base64):
        """
        解密 RSA 加密的密码
        
        Args:
            encrypted_password_base64: Base64 编码的加密密码
            
        Returns:
            str: 解密后的明文密码
            
        Raises:
            ValueError: 解密失败时抛出异常
        """
        try:
            # 明确拦截 Postman 等客户端变量未替换的情况（避免误报为 RSA/Base64 padding 问题）
            if isinstance(encrypted_password_base64, str):
                s = encrypted_password_base64.strip()
                if ("{{" in s and "}}" in s) or ("{" in s or "}" in s):
                    raise ValueError("检测到未替换的变量占位符（例如 {{rsa_password}}），请确认已选中正确的 Environment 且预处理脚本已为同一作用域设置变量")
                # 2048-bit RSA 的密文 base64 通常在 300+ 字符；过短基本不可能是有效密文
                if len(s) < 80:
                    raise ValueError("密文过短，疑似未正确加密或变量未生效（请检查 Postman 预处理脚本是否在当前请求执行）")
            # Base64 解码
            encrypted_password = base64.b64decode(encrypted_password_base64)
            
            # RSA 解密
            decrypted_password = self._private_key.decrypt(
                encrypted_password,
                padding.PKCS1v15()
            )
            
            return decrypted_password.decode('utf-8')
        except Exception as e:
            raise ValueError(f"密码解密失败: {str(e)}")


# 全局 RSA 工具实例
_rsa_utils = None


def get_rsa_utils():
    """
    获取全局 RSA 工具实例（单例模式）
    
    Returns:
        RSAUtils: RSA 工具实例
    """
    global _rsa_utils
    if _rsa_utils is None:
        _rsa_utils = RSAUtils()
    return _rsa_utils

