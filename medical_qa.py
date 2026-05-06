import streamlit as st
import os
import tempfile
from rag import load_multiple_documents, chunk2vector, llm_chain, embeddings
from langchain_community.vectorstores import FAISS
from config.settings import Config, SYSTEM_CONFIGS
from chat_history import save_chat_history, load_chat_history, delete_chat_history, format_conversation

SYSTEM_NAME = "medical"
DEFAULT_INDEX_DIR = "medical_faiss_index"

def save_uploaded_file(uploaded_file):
    try:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"文件保存失败: {str(e)}")
        return None

def load_default_index():
    """尝试加载预置的知识库索引"""
    if os.path.exists(DEFAULT_INDEX_DIR):
        try:
            vector_store = FAISS.load_local(DEFAULT_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
            return vector_store, True
        except Exception as e:
            st.warning(f"加载预置索引失败: {str(e)}")
            return None, False
    return None, False

def interactive():
    config = SYSTEM_CONFIGS["medical"]

    st.set_page_config(
        page_title=f"{config['name']}",
        page_icon=config["icon"],
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
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
            background: #e6ffed;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid #11998e;
        }
        .feature-card {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.8rem;
        }
        .feature-title {
            color: #11998e;
            font-size: 1.1rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="main-header">
            <h1>{config['icon']} {config['name']}</h1>
            <p>{config['description']} | 版本: {Config.VERSION}</p>
        </div>
    """, unsafe_allow_html=True)

    # 初始化会话状态
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = None
    if 'current_files' not in st.session_state:
        st.session_state.current_files = []
    if 'engine_initialized' not in st.session_state:
        st.session_state.engine_initialized = False
    if 'show_history' not in st.session_state:
        st.session_state.show_history = False

    # 尝试加载预置索引
    if not st.session_state.engine_initialized and not st.session_state.vector_store:
        with st.spinner("🔄 正在加载医疗知识库..."):
            vector_store, success = load_default_index()
            if success and vector_store:
                st.session_state.vector_store = vector_store
                st.session_state.engine_initialized = True
                st.session_state.current_files = ["医疗健康知识库"]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
            <div class="medical-card">
            <strong>💡 温馨提示</strong>
            <p>本系统提供的健康信息仅供参考，不能替代专业医疗建议。如有健康问题，请咨询专业医生。</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### 💬 医疗问答")

        for message in st.session_state.get('messages', []):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("请输入您的健康问题..."):
            if not st.session_state.get('engine_initialized'):
                st.warning("⚠️ 请先上传医疗文档或等待知识库加载")
                return

            if 'messages' not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                    with st.spinner("🏥 正在分析健康信息..."):
                        try:
                            chain = llm_chain(st.session_state.vector_store)
                            answer = chain.invoke(prompt)
                            st.markdown(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                            
                            # 添加医疗免责声明
                            st.markdown("""
                            ---
                            ⚠️ **医疗免责声明**
                            
                            🚨 本回答仅供参考，不构成医疗诊断。如有身体不适，请及时就医。
                            """)
                        except Exception as e:
                            error_msg = f"回答失败: {str(e)}"
                            st.error(error_msg)
                            if 'messages' in st.session_state:
                                st.session_state.messages.append({"role": "assistant", "content": error_msg})

    with col2:
        st.subheader("📋 系统功能")

        features = [
            ("📄 健康文档", "支持上传健康指南、医学手册等"),
            ("💬 智能问诊", "基于医学知识的健康问答"),
            ("🏥 症状分析", "提供症状解读和健康建议"),
            ("💊 用药指导", "药品信息查询和用药建议"),
            ("📝 历史记录", "对话记录本地存储，随时查看"),
            ("🔒 隐私保护", "所有数据仅本地处理，保障隐私安全")
        ]

        for title, desc in features:
            st.markdown(f"""
                <div class="feature-card">
                <div class="feature-title">{title}</div>
                <p style="color: #666; font-size: 0.9rem;">{desc}</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📊 系统状态")
        if st.session_state.get('engine_initialized'):
            st.success("✅ 系统就绪")
            st.info(f"📚 已加载文档: {len(st.session_state.get('current_files', []))}")
        else:
            st.warning("⚠️ 请先上传医疗文档")

        st.markdown("---")
        if st.button("💾 保存当前对话", type="secondary", use_container_width=True):
            if st.session_state.get('messages'):
                success = save_chat_history(st.session_state.messages, SYSTEM_NAME)
                if success:
                    st.success("✅ 对话已保存")
                else:
                    st.error("❌ 保存失败")

        if st.button("📝 查看历史对话", type="secondary", use_container_width=True):
            st.session_state.show_history = not st.session_state.show_history

        if st.button("🗑️ 清空对话", type="secondary", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        if st.button("🔄 重置系统", type="secondary", use_container_width=True):
            st.session_state.vector_store = None
            st.session_state.current_files = []
            st.session_state.engine_initialized = False
            st.session_state.messages = []
            st.rerun()

    # 历史对话面板
    if st.session_state.show_history:
        st.markdown("---")
        st.subheader("📝 历史对话记录")
        
        history = load_chat_history(SYSTEM_NAME)
        
        if history:
            history.reverse()
            
            for conv in history:
                with st.expander(f"📅 {conv['timestamp'][:19]} | {len(conv['messages'])} 条消息"):
                    st.code(format_conversation(conv), language='text')
                    
                    col_save, col_delete = st.columns(2)
                    with col_save:
                        if st.button(f"🔄 恢复对话 {conv['id']}", use_container_width=True):
                            st.session_state.messages = conv['messages'].copy()
                            st.session_state.show_history = False
                            st.success("✅ 对话已恢复")
                            st.rerun()
                    with col_delete:
                        if st.button(f"🗑️ 删除 {conv['id']}", use_container_width=True):
                            delete_chat_history(SYSTEM_NAME, conv['id'])
                            st.success("✅ 已删除")
                            st.rerun()
            
            if st.button("🗑️ 清空所有历史", type="primary", use_container_width=True):
                delete_chat_history(SYSTEM_NAME)
                st.success("✅ 已清空所有历史")
                st.rerun()
        else:
            st.info("暂无历史对话记录")

    st.markdown("---")
    st.markdown(f"""
        <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <strong>{config['icon']} {config['name']}</strong> | 版本 {Config.VERSION} | 仅供健康参考，不替代专业医疗建议
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header(f"🏥 医疗系统控制")

        st.markdown("---")
        st.subheader("📁 医疗文档管理")

        uploaded_files = st.file_uploader(
            "上传健康文档",
            type=Config.SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            help=f"支持格式: {', '.join(Config.SUPPORTED_FILE_TYPES)} | 最大 {Config.MAX_FILE_SIZE//(1024*1024)}MB"
        )

        if uploaded_files or st.session_state.get('current_files'):
            with st.spinner("🏥 正在处理医疗文档..."):
                file_paths = []

                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        tmp_path = save_uploaded_file(uploaded_file)
                        if tmp_path:
                            file_paths.append(tmp_path)
                            st.success(f"✅ {uploaded_file.name}")

                if file_paths:
                    try:
                        docs = load_multiple_documents(file_paths)
                        if st.session_state.get('vector_store'):
                            new_vector_store = chunk2vector(docs, embeddings)
                            st.session_state.vector_store.merge_from(new_vector_store)
                        else:
                            st.session_state.vector_store = chunk2vector(docs, embeddings)

                        st.session_state.current_files.extend([os.path.basename(p) for p in file_paths])
                        st.session_state.engine_initialized = True
                        st.success(f"🎉 已添加 {len(docs)} 份医疗文档")
                    except Exception as e:
                        st.error(f"❌ 处理失败: {str(e)}")

if __name__ == "__main__":
    interactive()
