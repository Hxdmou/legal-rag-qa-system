import logging
import os
from config.settings import Config

class Logger:
    """企业级日志管理工具"""
    
    _loggers = {}
    
    @staticmethod
    def get_logger(name: str = "RAG_SYSTEM") -> logging.Logger:
        """获取日志实例"""
        if name in Logger._loggers:
            return Logger._loggers[name]
        
        # 确保日志目录存在
        Config.ensure_directories()
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # 避免重复添加处理器
        if logger.handlers:
            Logger._loggers[name] = logger
            return logger
        
        # 创建格式化器
        formatter = logging.Formatter(Config.LOG_FORMAT)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 创建文件处理器
        log_file = os.path.join(Config.LOG_DIR, f"{name.lower()}.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        Logger._loggers[name] = logger
        return logger
    
    @staticmethod
    def log_info(message: str, context: str = ""):
        """记录信息日志"""
        logger = Logger.get_logger()
        if context:
            logger.info(f"[{context}] {message}")
        else:
            logger.info(message)
    
    @staticmethod
    def log_error(message: str, context: str = "", exception: Exception = None):
        """记录错误日志"""
        logger = Logger.get_logger()
        if context:
            log_message = f"[{context}] {message}"
        else:
            log_message = message
        
        if exception:
            logger.error(log_message, exc_info=True)
        else:
            logger.error(log_message)
    
    @staticmethod
    def log_warning(message: str, context: str = ""):
        """记录警告日志"""
        logger = Logger.get_logger()
        if context:
            logger.warning(f"[{context}] {message}")
        else:
            logger.warning(message)
    
    @staticmethod
    def log_debug(message: str, context: str = ""):
        """记录调试日志"""
        logger = Logger.get_logger()
        if context:
            logger.debug(f"[{context}] {message}")
        else:
            logger.debug(message)
