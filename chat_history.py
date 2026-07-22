import os
import json
from datetime import datetime

def save_chat_history(messages, system_name):
    """保存对话历史到本地文件"""
    try:
        history_dir = "chat_histories"
        os.makedirs(history_dir, exist_ok=True)
        
        history_file = os.path.join(history_dir, f"{system_name}_history.json")
        
        # 读取现有历史
        existing_history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    existing_history = json.load(f)
            except:
                existing_history = []
        
        # 创建新对话记录
        new_conversation = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "messages": messages.copy()
        }
        
        # 添加到历史
        existing_history.append(new_conversation)
        
        # 保留最近50条对话记录
        if len(existing_history) > 50:
            existing_history = existing_history[-50:]
        
        # 保存
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(existing_history, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"保存对话历史失败: {str(e)}")
        return False

def load_chat_history(system_name):
    """加载对话历史"""
    try:
        history_file = os.path.join("chat_histories", f"{system_name}_history.json")
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"加载对话历史失败: {str(e)}")
        return []

def delete_chat_history(system_name, conversation_id=None):
    """删除对话历史"""
    try:
        history_file = os.path.join("chat_histories", f"{system_name}_history.json")
        if os.path.exists(history_file):
            if conversation_id:
                # 删除特定对话
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                history = [h for h in history if h['id'] != conversation_id]
                
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
            else:
                # 删除所有历史
                os.remove(history_file)
        return True
    except Exception as e:
        print(f"删除对话历史失败: {str(e)}")
        return False

def format_conversation(conversation):
    """格式化对话记录为可读文本"""
    lines = []
    lines.append(f"📅 {conversation['timestamp']}")
    lines.append(f"🆔 ID: {conversation['id']}")
    lines.append("-" * 50)
    
    for msg in conversation.get('messages', []):
        role = "👤 用户" if msg['role'] == 'user' else "🤖 助手"
        lines.append(f"{role}: {msg['content']}")
        lines.append("")
    
    return "\n".join(lines)
