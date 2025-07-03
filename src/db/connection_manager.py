import json
import os
from typing import List, Dict, Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
import secrets
import sys
from db.utils import data_path

CONNECTIONS_FILE = data_path('connections.json.enc')
KEY_FILE = data_path('key.bin.enc')
SALT_FILE = data_path('key.salt')

class ConnectionManager:
    def __init__(self, password: str = None):
        self.connections: List[Dict] = []
        self.fernet = None
        self.password = password
        self._init_fernet()
        self.load_connections()

    def _init_fernet(self):
        # 主密码加密密钥逻辑
        if not os.path.exists(KEY_FILE):
            # 首次使用，生成密钥并用主密码加密
            key = Fernet.generate_key()
            salt = secrets.token_bytes(16)
            os.makedirs(os.path.dirname(SALT_FILE), exist_ok=True)
            with open(SALT_FILE, 'wb') as f:
                f.write(salt)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100_000,
                backend=default_backend()
            )
            if not self.password:
                raise Exception('首次使用必须设置主密码')
            pwd_key = base64.urlsafe_b64encode(kdf.derive(self.password.encode('utf-8')))
            fernet_pwd = Fernet(pwd_key)
            enc_key = fernet_pwd.encrypt(key)
            with open(KEY_FILE, 'wb') as f:
                f.write(enc_key)
            self.fernet = Fernet(key)
        else:
            # 已有密钥文件，需主密码解密
            if not self.password:
                raise Exception('需要主密码解锁')
            with open(SALT_FILE, 'rb') as f:
                salt = f.read()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100_000,
                backend=default_backend()
            )
            pwd_key = base64.urlsafe_b64encode(kdf.derive(self.password.encode('utf-8')))
            fernet_pwd = Fernet(pwd_key)
            with open(KEY_FILE, 'rb') as f:
                enc_key = f.read()
            try:
                key = fernet_pwd.decrypt(enc_key)
            except InvalidToken:
                raise Exception('主密码错误，无法解锁密钥')
            self.fernet = Fernet(key)

    def load_connections(self):
        if os.path.exists(CONNECTIONS_FILE):
            with open(CONNECTIONS_FILE, 'rb') as f:
                enc_data = f.read()
            try:
                data = self.fernet.decrypt(enc_data)
                self.connections = json.loads(data.decode('utf-8'))
            except (InvalidToken, Exception):
                self.connections = []
        else:
            self.connections = []

    def save_connections(self):
        data = json.dumps(self.connections, ensure_ascii=False, indent=2).encode('utf-8')
        enc_data = self.fernet.encrypt(data)
        with open(CONNECTIONS_FILE, 'wb') as f:
            f.write(enc_data)

    def add_connection(self, conn_info: Dict):
        self.connections.append(conn_info)
        self.save_connections()

    def remove_connection(self, index: int):
        if 0 <= index < len(self.connections):
            self.connections.pop(index)
            self.save_connections()

    def update_connection(self, index: int, conn_info: Dict):
        if 0 <= index < len(self.connections):
            self.connections[index] = conn_info
            self.save_connections()

    def get_connections(self) -> List[Dict]:
        return self.connections

    def get_connection(self, index: int) -> Optional[Dict]:
        if 0 <= index < len(self.connections):
            return self.connections[index]
        return None 