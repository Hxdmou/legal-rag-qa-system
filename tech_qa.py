import streamlit as st
import os
import tempfile
from core.rag_engine import RAGEngine
from config.settings import Config, SYSTEM_CONFIGS
from utils.logger import Logger
from utils.security import SecurityManager

# 初始化组件
rag_engine = RAGEngine()
security_manager = SecurityManager()

# IT技术领域专业提示词
TECH_PROMPT = """
你是一名专业的IT技术助手，请根据提供的技术文档回答问题。

规则：
1. 回答要专业且清晰，适合程序员理解
2. 如果涉及代码，请提供完整的代码示例
3. 如果问题涉及技术方案，请提供详细的架构说明
4. 如果不知道答案，直接说"根据现有知识库，无法回答该问题"

问题：{question}
上下文：{context}

回答：
"""

def save_uploaded_file(uploaded_file):
    """保存上传的文件到临时目录"""
    try:
        sanitized_name = security_manager.sanitize_filename(uploaded_file.name)
        suffix = os.path.splitext(sanitized_name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        Logger.log_error(f"文件保存失败: {str(e)}", "TechQA")
        st.error(f"文件保存失败: {str(e)}")
        return None

def interactive():
    """企业级IT技术问答系统"""
    config = SYSTEM_CONFIGS["tech"]
    
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
            background: linear-gradient(135deg, #457b9d 0%, #1d3557 100%);
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
        .tech-card {
            background: #e6f2ff;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid #457b9d;
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
        st.header(f"💻 技术系统控制")
        
        # 文件上传区域
        st.markdown("---")
        st.subheader("📁 技术文档管理")
        
        uploaded_files = st.file_uploader(
            "上传API文档/技术手册",
            type=Config.SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            help=f"支持格式: {', '.join(Config.SUPPORTED_FILE_TYPES)} | 最大 {Config.MAX_FILE_SIZE//(1024*1024)}MB"
        )
        
        if uploaded_files or st.session_state.get('current_files'):
            with st.spinner("正在处理技术文档..."):
                file_paths = []
                
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        if security_manager.check_file_size(uploaded_file.size):
                            tmp_path = save_uploaded_file(uploaded_file)
                            if tmp_path:
                                file_paths.append(tmp_path)
                                st.success(f"✅ {uploaded_file.name}")
                        else:
                            st.error(f"❌ {uploaded_file.name} - 文件过大")
                
                if file_paths:
                    try:
                        docs = rag_engine.load_multiple_documents(file_paths)
                        if st.session_state.get('vector_store'):
                            rag_engine.vector_store = st.session_state.vector_store
                            rag_engine.vector_store.add_documents(docs)
                        else:
                            st.session_state.vector_store = rag_engine.build_vector_store(docs)
                        
                        st.session_state.current_files.extend([os.path.basename(p) for p in file_paths])
                        st.session_state.engine_initialized = True
                        st.success(f"🎉 已添加 {len(docs)} 份技术文档")
                        Logger.log_info(f"技术文档加载完成，{len(file_paths)}个文件", "TechQA")
                    except Exception as e:
                        st.error(f"❌ 处理失败: {str(e)}")
                        Logger.log_error(f"处理技术文档失败: {str(e)}", "TechQA", e)
        
        # 系统状态
        st.markdown("---")
        st.subheader("📊 系统状态")
        if st.session_state.get('engine_initialized'):
            st.markdown("""
                <div class="system-info">
                <strong>✅ 系统状态:</strong> 就绪<br>
                <strong>📚 已加载文档:</strong> {}<br>
                <strong>💻 模式:</strong> IT技术问答
                </div>
            """.format(len(st.session_state.current_files)), unsafe_allow_html=True)
        else:
            st.warning("⚠️ 请先上传技术文档")
        
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
    
    # 技术提示
    st.markdown("""
        <div class="tech-card">
        <strong>💡 开发提示</strong>
        <p>上传您的API文档、技术手册或代码说明后，可以随时提问相关技术问题，系统会基于您的文档进行解答。</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 聊天区域
    st.header("💬 技术问答")
    
    # 显示消息历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 用户输入
    if prompt := st.chat_input("请输入您的技术问题..."):
        if not st.session_state.get('engine_initialized'):
            st.warning("⚠️ 请先上传技术文档")
            return
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("💻 正在分析技术文档..."):
                try:
                    answer = rag_engine.answer_question(prompt, TECH_PROMPT)
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    Logger.log_info(f"技术问答完成: {prompt[:30]}", "TechQA")
                except Exception as e:
                    error_msg = f"回答失败: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # 底部信息
    st.markdown("---")
    st.markdown(f"""
        <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <strong>{config['icon']} {config['name']}</strong> | 版本 {Config.VERSION} | 程序员技术助手
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    interactive()
