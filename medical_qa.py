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

# 医疗领域专业提示词
MEDICAL_PROMPT = """
你是一名专业的医疗健康助手，请根据提供的医疗资料回答问题。

规则：
1. 回答要专业但易懂，避免使用过于晦涩的术语
2. 如果涉及用药建议，请强调咨询医生的重要性
3. 如果问题涉及诊断，请建议用户咨询专业医师
4. 如果不知道答案，直接说"根据现有知识库，无法回答该问题"
5. 在回答末尾必须添加免责声明

问题：{question}
上下文：{context}

回答：
"""

DISCLAIMER = """

⚠️ **医疗免责声明**
本信息仅供参考，不能替代专业医疗建议。在做出任何医疗决策前，请务必咨询执业医师或其他专业医疗人员。
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
        Logger.log_error(f"文件保存失败: {str(e)}", "MedicalQA")
        st.error(f"文件保存失败: {str(e)}")
        return None

def interactive():
    """企业级医疗健康问答系统"""
    config = SYSTEM_CONFIGS["medical"]
    
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
            background: linear-gradient(135deg, #e53935 0%, #ff7043 100%);
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
        .medical-card {
            background: #ffebee;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid #e53935;
        }
        .disclaimer-box {
            background: #fff3e0;
            border-radius: 8px;
            padding: 1.5rem;
            margin-top: 1rem;
            border: 1px solid #ffe0b2;
        }
        .system-info {
            background: #e3f2fd;
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
        st.header(f"🏥 医疗系统控制")
        
        # 文件上传区域
        st.markdown("---")
        st.subheader("📁 医学资料管理")
        
        uploaded_files = st.file_uploader(
            "上传医学文献/健康指南",
            type=Config.SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            help=f"支持格式: {', '.join(Config.SUPPORTED_FILE_TYPES)} | 最大 {Config.MAX_FILE_SIZE//(1024*1024)}MB"
        )
        
        if uploaded_files or st.session_state.get('current_files'):
            with st.spinner("正在处理医学资料..."):
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
                        st.success(f"🎉 已添加 {len(docs)} 份医学资料")
                        Logger.log_info(f"医学资料加载完成，{len(file_paths)}个文件", "MedicalQA")
                    except Exception as e:
                        st.error(f"❌ 处理失败: {str(e)}")
                        Logger.log_error(f"处理医学资料失败: {str(e)}", "MedicalQA", e)
        
        # 系统状态
        st.markdown("---")
        st.subheader("📊 系统状态")
        if st.session_state.get('engine_initialized'):
            st.markdown("""
                <div class="system-info">
                <strong>✅ 系统状态:</strong> 就绪<br>
                <strong>📚 已加载资料:</strong> {}<br>
                <strong>🏥 模式:</strong> 医疗健康问答
                </div>
            """.format(len(st.session_state.current_files)), unsafe_allow_html=True)
        else:
            st.warning("⚠️ 请先上传医学资料")
        
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
    
    # 医疗免责声明
    st.markdown("""
        <div class="disclaimer-box">
        <strong>⚠️ 重要医疗免责声明</strong>
        <p>本系统提供的健康信息仅供参考，不能替代专业医疗建议、诊断或治疗。在做出任何医疗决策前，请务必咨询执业医师或其他专业医疗人员。</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 聊天区域
    st.header("💬 健康咨询")
    
    # 显示消息历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 用户输入
    if prompt := st.chat_input("请输入您的健康问题..."):
        if not st.session_state.get('engine_initialized'):
            st.warning("⚠️ 请先上传医学资料")
            return
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("🏥 正在分析健康资料..."):
                try:
                    answer = rag_engine.answer_question(prompt, MEDICAL_PROMPT)
                    full_answer = answer + DISCLAIMER
                    st.markdown(full_answer)
                    st.session_state.messages.append({"role": "assistant", "content": full_answer})
                    Logger.log_info(f"医疗问答完成: {prompt[:30]}", "MedicalQA")
                except Exception as e:
                    error_msg = f"回答失败: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # 底部信息
    st.markdown("---")
    st.markdown(f"""
        <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <strong>{config['icon']} {config['name']}</strong> | 版本 {Config.VERSION} | 仅供健康知识参考
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    interactive()
