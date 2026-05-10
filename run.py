import streamlit as st
import os
import tempfile
import json
from rag import load_multiple_documents, chunk2vector, llm_chain, embeddings
from langchain_community.vectorstores import FAISS
from config.settings import Config, SYSTEM_CONFIGS
from chat_history import save_chat_history, load_chat_history, delete_chat_history, format_conversation

SYSTEM_NAME = "general"
DEFAULT_INDEX_DIR = "general_faiss_index"

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
    config = SYSTEM_CONFIGS["general"]

    st.set_page_config(
        page_title=f"{config['name']}",
        page_icon=config["icon"],
        layout="wide",
        initial_sidebar_state="expanded"
    )

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
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.8rem;
        }
        .feature-title {
            color: #667eea;
            font-size: 1.1rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .history-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            cursor: pointer;
        }
        .history-card:hover {
            background: #e9ecef;
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
        with st.spinner("🔄 正在加载预置知识库..."):
            vector_store, success = load_default_index()
            if success and vector_store:
                st.session_state.vector_store = vector_store
                st.session_state.engine_initialized = True
                st.session_state.current_files = ["预置知识库"]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 💬 智能问答")

        for message in st.session_state.get('messages', []):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("请输入您的问题..."):
            if not st.session_state.get('engine_initialized'):
                st.warning("⚠️ 请先上传文档建立索引或等待预置知识库加载")
                return

            if 'messages' not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("🤔 正在分析..."):
                    try:
                        chain = llm_chain(st.session_state.vector_store)
                        answer = chain.invoke(prompt)
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    except Exception as e:
                        error_msg = f"回答失败: {str(e)}"
                        st.error(error_msg)
                        if 'messages' in st.session_state:
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})

    with col2:
        st.subheader("📋 系统功能")

        features = [
            ("📄 多格式支持", "支持TXT、PDF、Excel、Word等文档格式"),
            ("🔍 混合检索", "BM25 + 向量嵌入混合检索，提升准确性"),
            ("💬 智能问答", "基于文档内容的精准问答"),
            ("📜 文本分块", "智能文本分块和向量化处理"),
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
            st.info(f"📚 已加载: {len(st.session_state.get('current_files', []))} 个文档")
        else:
            st.warning("⚠️ 请先上传文档建立索引")

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
            # 按时间倒序排列
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
        <strong>{config['icon']} {config['name']}</strong> | 版本 {Config.VERSION} | 基于 RAG 技术
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header(f"⚙️ 系统控制")

        st.markdown("---")
        st.subheader("📁 文档管理")

        uploaded_files = st.file_uploader(
            "上传文档（支持多选）",
            type=Config.SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            help=f"支持格式: {', '.join(Config.SUPPORTED_FILE_TYPES)} | 最大 {Config.MAX_FILE_SIZE//(1024*1024)}MB"
        )

        st.markdown("---")
        st.subheader("📂 本地文件")
        local_file_path = st.text_input(
            "文件路径",
            placeholder=r"例如: C:\Users\Documents\文件.pdf",
            help="输入本地文件的完整路径"
        )

        if uploaded_files or local_file_path:
            with st.spinner("🔄 正在处理文档并建立向量索引..."):
                file_paths = []

                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        tmp_path = save_uploaded_file(uploaded_file)
                        if tmp_path:
                            file_paths.append(tmp_path)
                            st.success(f"✅ {uploaded_file.name}")

                if local_file_path and os.path.exists(local_file_path):
                    file_paths.append(local_file_path)
                    st.success(f"✅ 已加载: {os.path.basename(local_file_path)}")
                elif local_file_path:
                    st.error(f"❌ 文件不存在")

                if file_paths:
                    try:
                        st.info(f"📄 正在加载 {len(file_paths)} 个文档...")
                        docs = load_multiple_documents(file_paths)
                        
                        if not docs:
                            st.error("❌ 文档加载失败：未找到有效文档内容")
                            return
                        
                        st.info(f"🔄 正在向量化 {len(docs)} 个文档...")
                        st.session_state.vector_store = chunk2vector(docs, embeddings)
                        st.session_state.current_files = [os.path.basename(p) for p in file_paths]
                        st.session_state.engine_initialized = True
                        st.success(f"🎉 索引建立完成！共 {len(docs)} 个文档")
                        
                        # 清理临时文件
                        for fp in file_paths:
                            if fp.startswith(tempfile.gettempdir()):
                                try:
                                    os.remove(fp)
                                except:
                                    pass
                    except ValueError as e:
                        st.error(f"❌ 索引建立失败：{str(e)}")
                    except Exception as e:
                        import traceback
                        st.error(f"❌ 索引建立失败: {str(e)}")
                        st.code(traceback.format_exc(), language='python')

if __name__ == "__main__":
    interactive()
