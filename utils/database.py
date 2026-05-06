import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from config.settings import Config
from utils.logger import Logger

class ChatHistoryManager:
    """企业级对话历史管理"""
    
    def __init__(self):
        self.history_dir = Config.CHAT_HISTORY_DIR
        Config.ensure_directories()
    
    def get_history_path(self, session_id: str) -> str:
        """获取会话历史文件路径"""
        return os.path.join(self.history_dir, f"{session_id}.json")
    
    def save_history(self, session_id: str, messages: List[Dict[str, Any]]):
        """保存会话历史"""
        try:
            history_data = {
                "session_id": session_id,
                "messages": messages,
                "updated_at": datetime.now().isoformat()
            }
            with open(self.get_history_path(session_id), 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            Logger.log_info(f"会话历史已保存: {session_id}", "ChatHistory")
        except Exception as e:
            Logger.log_error(f"保存会话历史失败: {str(e)}", "ChatHistory", e)
            raise
    
    def load_history(self, session_id: str) -> List[Dict[str, Any]]:
        """加载会话历史"""
        try:
            path = self.get_history_path(session_id)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("messages", [])
            return []
        except Exception as e:
            Logger.log_error(f"加载会话历史失败: {str(e)}", "ChatHistory", e)
            return []
    
    def delete_history(self, session_id: str):
        """删除会话历史"""
        try:
            path = self.get_history_path(session_id)
            if os.path.exists(path):
                os.remove(path)
                Logger.log_info(f"会话历史已删除: {session_id}", "ChatHistory")
        except Exception as e:
            Logger.log_error(f"删除会话历史失败: {str(e)}", "ChatHistory", e)
            raise
    
    def list_histories(self) -> List[Dict[str, Any]]:
        """列出所有会话历史"""
        try:
            histories = []
            for filename in os.listdir(self.history_dir):
                if filename.endswith(".json"):
                    session_id = filename[:-5]
                    path = self.get_history_path(session_id)
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        histories.append({
                            "session_id": session_id,
                            "updated_at": data.get("updated_at", ""),
                            "message_count": len(data.get("messages", []))
                        })
            return sorted(histories, key=lambda x: x["updated_at"], reverse=True)
        except Exception as e:
            Logger.log_error(f"列出会话历史失败: {str(e)}", "ChatHistory", e)
            return []

class VectorStoreManager:
    """企业级向量存储管理"""
    
    def __init__(self):
        self.vector_dir = Config.VECTOR_STORE_DIR
        Config.ensure_directories()
    
    def get_vector_path(self, doc_id: str) -> str:
        """获取向量存储路径"""
        return os.path.join(self.vector_dir, doc_id)
    
    def save_vector(self, doc_id: str, vector_data: Any):
        """保存向量数据"""
        try:
            path = self.get_vector_path(doc_id)
            os.makedirs(path, exist_ok=True)
            # 这里应该根据实际的向量库类型进行保存
            # 实际实现需要根据使用的向量库进行调整
            Logger.log_info(f"向量数据已保存: {doc_id}", "VectorStore")
        except Exception as e:
            Logger.log_error(f"保存向量数据失败: {str(e)}", "VectorStore", e)
            raise
    
    def load_vector(self, doc_id: str) -> Optional[Any]:
        """加载向量数据"""
        try:
            path = self.get_vector_path(doc_id)
            if os.path.exists(path):
                Logger.log_info(f"向量数据已加载: {doc_id}", "VectorStore")
                return path
            return None
        except Exception as e:
            Logger.log_error(f"加载向量数据失败: {str(e)}", "VectorStore", e)
            return None
    
    def delete_vector(self, doc_id: str):
        """删除向量数据"""
        try:
            path = self.get_vector_path(doc_id)
            if os.path.exists(path):
                shutil.rmtree(path)
                Logger.log_info(f"向量数据已删除: {doc_id}", "VectorStore")
        except Exception as e:
            Logger.log_error(f"删除向量数据失败: {str(e)}", "VectorStore", e)
            raise
    
    def list_vectors(self) -> List[str]:
        """列出所有向量存储"""
        try:
            vectors = []
            for item in os.listdir(self.vector_dir):
                path = os.path.join(self.vector_dir, item)
                if os.path.isdir(path):
                    vectors.append(item)
            return vectors
        except Exception as e:
            Logger.log_error(f"列出向量存储失败: {str(e)}", "VectorStore", e)
            return []
