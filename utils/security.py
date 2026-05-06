import os
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from config.settings import Config
from utils.logger import Logger

class SecurityManager:
    """企业级安全管理工具"""
    
    def __init__(self):
        self.rate_limits: Dict[str, Dict[str, int]] = {}
        self.max_requests = Config.RATE_LIMIT
        self.time_window = 60  # 60秒窗口
    
    def generate_session_id(self) -> str:
        """生成唯一会话ID"""
        return str(uuid.uuid4())
    
    def generate_doc_id(self, filename: str) -> str:
        """基于文件名生成文档ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_value = hashlib.md5(filename.encode()).hexdigest()[:8]
        return f"doc_{hash_value}_{timestamp}"
    
    def is_allowed_file_type(self, filename: str) -> bool:
        """检查文件类型是否允许"""
        ext = filename.split('.')[-1].lower()
        return ext in Config.SUPPORTED_FILE_TYPES
    
    def check_file_size(self, file_size: int) -> bool:
        """检查文件大小是否在限制内"""
        return file_size <= Config.MAX_FILE_SIZE
    
    def check_rate_limit(self, client_ip: str) -> bool:
        """检查请求频率限制"""
        now = datetime.now().timestamp()
        
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = {"count": 0, "start_time": now}
        
        record = self.rate_limits[client_ip]
        
        # 如果时间窗口已过，重置计数器
        if now - record["start_time"] > self.time_window:
            record["count"] = 0
            record["start_time"] = now
        
        # 检查是否超过限制
        if record["count"] >= self.max_requests:
            Logger.log_warning(f"请求频率超限: {client_ip}", "Security")
            return False
        
        record["count"] += 1
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """清理文件名，防止路径遍历攻击"""
        # 移除路径分隔符和危险字符
        dangerous_chars = ['/', '\\', '..', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        return filename
    
    def validate_path(self, path: str) -> bool:
        """验证路径是否安全"""
        # 检查是否包含路径遍历
        if '..' in path or '//' in path:
            return False
        # 检查是否为绝对路径
        if os.path.isabs(path):
            return False
        return True
    
    def generate_api_key(self) -> str:
        """生成API密钥"""
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()

class TokenManager:
    """企业级Token管理"""
    
    def __init__(self):
        self.tokens: Dict[str, Dict[str, Any]] = {}
    
    def create_token(self, user_id: str, expires_hours: int = 24) -> str:
        """创建访问Token"""
        token = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        self.tokens[token] = {
            "user_id": user_id,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        Logger.log_info(f"Token已创建: {user_id}", "TokenManager")
        return token
    
    def validate_token(self, token: str) -> Optional[str]:
        """验证Token是否有效"""
        if token not in self.tokens:
            return None
        
        token_data = self.tokens[token]
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        
        if datetime.now() > expires_at:
            del self.tokens[token]
            Logger.log_warning("Token已过期", "TokenManager")
            return None
        
        return token_data["user_id"]
    
    def revoke_token(self, token: str):
        """撤销Token"""
        if token in self.tokens:
            del self.tokens[token]
            Logger.log_info("Token已撤销", "TokenManager")
    
    def cleanup_expired_tokens(self):
        """清理过期Token"""
        now = datetime.now()
        expired_tokens = []
        
        for token, data in self.tokens.items():
            expires_at = datetime.fromisoformat(data["expires_at"])
            if now > expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.tokens[token]
