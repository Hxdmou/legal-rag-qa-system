import streamlit as st
import os
import tempfile
import uuid
from datetime import datetime
from core.rag_engine import RAGEngine
from config.settings import Config, SYSTEM_CONFIGS
from utils.logger import Logger
from utils.security import SecurityManager

# 初始化组件
rag_engine = RAGEngine()
security_manager = SecurityManager()

def save_uploaded_file(uploaded_file):
    """保存上传的文件到临时目录"""
    try:
        sanitized_name = security_manager.sanitize_filename(uploaded_file.name)
        suffix = os.path.splitext(sanitized_name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        Logger.log_error(f"文件保存失败: {str(e)}", "FileUpload")
        st.error(f"文件保存失败: {str(e)}")
        return None

def generate_session_id():
    """生成唯一会话ID"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = security_manager.generate_session_id()
    return st.session_state.session_id

def interactive():
    """企业级通用RAG智能问答系统"""
    config = SYSTEM_CONFIGS["general"]
    
    st.set_page_config(
        page_title=f"{config['name']} - 企业级",
        page_icon=config["icon"],
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 企业级样式
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
        }
        .main-header h1 {
            color: white;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .main-header p {
            color: rgba(255, 255, 255, 0.8);
            font-size: 1.1rem;
        }
        .feature-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
        }
        .system-info {
            background: #e8f5e9;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 头部区域
    st.markdown(f"""
        <div class="main-header">
            <h1>{config['icon']} {config['name']}</h1>
            <p>{config['description']} | 版本: {Config.VERSION}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 初始化session state
    session_keys = ['messages', 'vector_store', 'current_files', 'engine_initialized']
    for key in session_keys:
        if key not in st.session_state:
            st.session_state[key] = [] if key == 'messages' else None
    
    # 侧边栏 - 企业级控制面板
    with st.sidebar:
        st.header(f"⚙️ 系统控制")
        
        # 文件上传区域
        st.markdown("---")
        st.subheader("📁 文档管理")
        
        uploaded_files = st.file_uploader(
            "上传文档（支持多选）",
            type=Config.SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            help=f"支持格式: {', '.join(Config.SUPPORTED_FILE_TYPES)} | 最大 {Config.MAX_FILE_SIZE//(1024*1024)}MB"
        )
        
        # 本地文件路径
        st.markdown("---")
        st.subheader("📂 本地文件")
        local_file_path = st.text_input(
            "文件路径",
            placeholder=r"例如: C:\Users\Documents\文件.pdf",
            help="输入本地文件的完整路径"
        )
        
        # 处理文件上传
        if uploaded_files or local_file_path:
            with st.spinner("🔄 正在处理文档并建立向量索引..."):
                file_paths = []
                
                # 处理上传的文件
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        if security_manager.check_file_size(uploaded_file.size):
                            tmp_path = save_uploaded_file(uploaded_file)
                            if tmp_path:
                                file_paths.append(tmp_path)
                                st.success(f"✅ {uploaded_file.name}")
                        else:
                            st.error(f"❌ {uploaded_file.name} - 文件过大")
                
                # 处理本地文件
                if local_file_path and os.path.exists(local_file_path):
                    if security_manager.is_allowed_file_type(local_file_path):
                        file_paths.append(local_file_path)
                        st.success(f"✅ 已加载: {os.path.basename(local_file_path)}")
                    else:
                        st.error(f"❌ 文件类型不支持")
                elif local_file_path:
                    st.error(f"❌ 文件不存在")
                
                # 构建向量存储
                if file_paths:
                    try:
                        docs = rag_engine.load_multiple_documents(file_paths)
                        st.session_state.vector_store = rag_engine.build_vector_store(docs)
                        st.session_state.current_files = [os.path.basename(p) for p in file_paths]
                        st.session_state.engine_initialized = True
                        st.success(f"🎉 索引建立完成！共 {len(docs)} 个文档")
                        Logger.log_info(f"向量索引构建完成，{len(file_paths)}个文件", "System")
                    except Exception as e:
                        st.error(f"❌ 索引建立失败: {str(e)}")
                        Logger.log_error(f"索引建立失败: {str(e)}", "System", e)
        
        # 系统状态
        st.markdown("---")
        st.subheader("📊 系统状态")
        if st.session_state.get('engine_initialized'):
            st.markdown("""
                <div class="system-info">
                <strong>✅ 系统状态:</strong> 就绪<br>
                <strong>📚 已加载文件:</strong> {}<br>
                <strong>🔑 会话ID:</strong> {}
                </div>
            """.format(len(st.session_state.current_files), generate_session_id()[:8]), unsafe_allow_html=True)
        else:
            st.warning("⚠️ 请先上传文档建立索引")
        
        # 操作按钮
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ 清空对话", type="secondary"):
                st.session_state.messages = []
        with col2:
            if st.button("🔄 重置系统", type="secondary"):
                st.session_state.vector_store = None
                st.session_state.current_files = []
                st.session_state.engine_initialized = False
                st.session_state.messages = []
                st.rerun()
    
    # 聊天区域
    st.header("💬 智能问答")
    
    # 显示消息历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 用户输入
    if prompt := st.chat_input("请输入您的问题..."):
        # 检查系统是否就绪
        if not st.session_state.get('engine_initialized'):
            st.warning("⚠️ 请先上传文档建立索引")
            return
        
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 生成回答
        with st.chat_message("assistant"):
            with st.spinner("🤔 正在分析..."):
                try:
                    answer = rag_engine.answer_question(prompt)
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    Logger.log_info(f"问答完成: {prompt[:30]}", "Chat")
                except Exception as e:
                    error_msg = f"回答失败: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # 底部信息
    st.markdown("---")
    st.markdown(f"""
        <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <strong>{config['icon']} {config['name']}</strong> | 版本 {Config.VERSION} | 基于 RAG 技术
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    interactive()
