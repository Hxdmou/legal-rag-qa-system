import streamlit as st
import os
import tempfile
from rag import load_multiple_documents, chunk2vector, llm_chain, embeddings
from langchain_community.vectorstores import FAISS
from config.settings import Config, SYSTEM_CONFIGS
from chat_history import save_chat_history, load_chat_history, delete_chat_history, format_conversation

SYSTEM_NAME = "finance"
DEFAULT_INDEX_DIR = "finance_faiss_index"

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
    config = SYSTEM_CONFIGS["finance"]

    st.set_page_config(
        page_title=f"{config['name']}",
        page_icon=config["icon"],
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
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
        .finance-card {
            background: #fff8e6;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid #fa709a;
        }
        .feature-card {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.8rem;
        }
        .feature-title {
            color: #fa709a;
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
        with st.spinner("🔄 正在加载金融知识库..."):
            vector_store, success = load_default_index()
            if success and vector_store:
                st.session_state.vector_store = vector_store
                st.session_state.engine_initialized = True
                st.session_state.current_files = ["金融投资知识库"]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
            <strong style="color: white; font-size: 1.1rem;">⚠️ 投资风险提示</strong>
            <p style="color: white; margin: 0.5rem 0 0 0;">
            ⚠️ 本系统提供的金融信息仅供参考，<strong>不构成投资建议或盈利承诺</strong>。
            <br>
            投资有风险，理财需谨慎。请根据自身风险承受能力做出投资决策。
            </p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### 💬 金融问答")

        for message in st.session_state.get('messages', []):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("请输入您的金融问题..."):
            if not st.session_state.get('engine_initialized'):
                st.warning("⚠️ 请先上传金融文档或等待知识库加载")
                return

            if 'messages' not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("💰 正在分析金融信息..."):
                    try:
                        chain = llm_chain(st.session_state.vector_store)
                        answer = chain.invoke(prompt)
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                        
                        # 添加金融风险提示
                        st.markdown("""
                        ---
                        ⚠️ **投资风险提示**
                        
                        ⚠️ 投资有风险，理财需谨慎。本文内容不构成投资建议。
                        """)
                    except Exception as e:
                        error_msg = f"回答失败: {str(e)}"
                        st.error(error_msg)
                        if 'messages' in st.session_state:
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})

    with col2:
        st.subheader("📋 系统功能")

        features = [
            ("� 金融文档", "支持上传投资报告、理财指南等"),
            ("💬 智能问答", "基于金融知识的投资问答"),
            ("💰 投资分析", "提供投资建议和市场分析"),
            ("📈 行情解读", "解读金融市场行情和趋势"),
            ("� 历史记录", "对话记录本地存储，随时查看"),
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
            st.warning("⚠️ 请先上传金融文档")

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
        <strong>{config['icon']} {config['name']}</strong> | 版本 {Config.VERSION} | 投资有风险，入市需谨慎
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header(f"💰 金融系统控制")

        st.markdown("---")
        st.subheader("📁 金融文档管理")

        uploaded_files = st.file_uploader(
            "上传金融文档",
            type=Config.SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            help=f"支持格式: {', '.join(Config.SUPPORTED_FILE_TYPES)} | 最大 {Config.MAX_FILE_SIZE//(1024*1024)}MB"
        )

        if uploaded_files or st.session_state.get('current_files'):
            with st.spinner("💰 正在处理金融文档..."):
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
                        st.success(f"🎉 已添加 {len(docs)} 份金融文档")
                    except Exception as e:
                        st.error(f"❌ 处理失败: {str(e)}")

if __name__ == "__main__":
    interactive()
