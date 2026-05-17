import streamlit as st
import os
import tempfile
from rag import (
    load_multiple_documents,
    chunk2vector,
    llm_chain,
    llm_chain_stream,
    stream_answer,
    get_embeddings,
    get_llm
)
from langchain_community.vectorstores import FAISS
from config.settings import Config, SYSTEM_CONFIGS
from chat_history import save_chat_history, load_chat_history, delete_chat_history, format_conversation
from logger import get_operation_logger
from export_utils import export_conversation_to_markdown, export_conversation_to_text, create_backup, restore_backup, list_backups
from batch_processor import create_batch_interface
from document_visualizer import create_document_viewer, get_document_summary, create_document_export

SYSTEM_NAME = "e-commerce"
DEFAULT_INDEX_DIR = "e_commerce_faiss_index"

op_logger = get_operation_logger(SYSTEM_NAME)

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
    if os.path.exists(DEFAULT_INDEX_DIR):
        try:
            embeddings = get_embeddings()
            vector_store = FAISS.load_local(DEFAULT_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
            return vector_store, True, f"成功加载预置索引"
        except Exception as e:
            return None, False, f"加载预置索引失败: {str(e)}"
    return None, False, "未找到预置索引目录。您可以上传文档创建新的知识库，或运行 python build_index.py 构建预置索引"

def save_index_to_disk(vector_store, index_dir=DEFAULT_INDEX_DIR):
    try:
        vector_store.save_local(index_dir)
        return True, f"索引已保存到 {index_dir}"
    except Exception as e:
        return False, f"保存索引失败: {str(e)}"

def process_files(file_paths):
    try:
        docs = load_multiple_documents(file_paths)
        if docs:
            if st.session_state.get("vector_store"):
                new_vector = chunk2vector(docs, get_embeddings())
                st.session_state.vector_store.merge_from(new_vector)
            else:
                st.session_state.vector_store = chunk2vector(docs, get_embeddings())
            return len(docs)
        return 0
    except Exception as e:
        st.error(f"文档处理失败: {str(e)}")
        return 0

def main():
    st.set_page_config(
        page_title="🛒 电商零售智能问答系统",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "engine_initialized" not in st.session_state:
        st.session_state.engine_initialized = False
    if "current_files" not in st.session_state:
        st.session_state.current_files = []
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7
    if "top_k" not in st.session_state:
        st.session_state.top_k = 5
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "index_load_status" not in st.session_state:
        st.session_state.index_load_status = "未加载"

    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    .status-active { background-color: #28a745; }
    .status-inactive { background-color: #dc3545; }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## 🛒 电商零售问答系统")
        st.markdown("---")

        with st.expander("📂 预置知识库", expanded=True):
            st.markdown("""<div class="sidebar-section"><h3>加载预训练索引</h3></div>""", unsafe_allow_html=True)

            if st.button("🔄 加载预置索引", use_container_width=True):
                with st.spinner("正在加载..."):
                    vector_store, success, msg = load_default_index()
                    if success and vector_store:
                        st.session_state.vector_store = vector_store
                        st.session_state.engine_initialized = True
                        st.session_state.current_files = ["预置知识库"]
                        st.session_state.index_load_status = "已加载预置索引"
                        op_logger.log_index_loaded(DEFAULT_INDEX_DIR)
                        st.success(f"✅ {msg}")
                    else:
                        st.warning(f"⚠️ {msg}")

            index_exists = os.path.exists(DEFAULT_INDEX_DIR)
            st.info(f"📂 预置索引: {'已存在' if index_exists else '不存在'}")

            if st.session_state.engine_initialized and st.session_state.vector_store:
                if st.button("💾 保存当前索引", use_container_width=True):
                    success, msg = save_index_to_disk(st.session_state.vector_store)
                    if success:
                        op_logger.log_index_saved(DEFAULT_INDEX_DIR)
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")

        with st.expander("📤 上传文档", expanded=False):
            uploaded_files = st.file_uploader(
                "选择文档",
                type=["txt", "pdf", "docx", "xlsx", "xls"],
                accept_multiple_files=True,
                help="支持TXT、PDF、Word、Excel格式"
            )

            if uploaded_files:
                if st.button("📚 处理文档", use_container_width=True):
                    with st.spinner("正在处理文档..."):
                        file_paths = []
                        for file in uploaded_files:
                            path = save_uploaded_file(file)
                            if path:
                                file_paths.append(path)

                        if file_paths:
                            doc_count = process_files(file_paths)
                            if doc_count > 0:
                                st.session_state.current_files = [f.name for f in uploaded_files]
                                st.session_state.engine_initialized = True
                                st.success(f"✅ 成功处理 {doc_count} 份文档")
                                op_logger.log_documents_processed(len(file_paths))

            if st.session_state.current_files:
                st.markdown("**当前知识库文件：**")
                for f in st.session_state.current_files:
                    st.text(f"• {f}")

        with st.expander("⚙️ 参数设置", expanded=False):
            st.session_state.temperature = st.slider(
                "🌡️ 温度参数",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.temperature,
                step=0.1,
                help="值越高回答越多样化，越低越确定性"
            )

            st.session_state.top_k = st.slider(
                "📊 检索数量",
                min_value=1,
                max_value=10,
                value=st.session_state.top_k,
                help="从知识库中检索的相关文档数量"
            )

        with st.expander("💬 历史记录", expanded=False):
            if st.button("🗑️ 清空当前记录", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

            saved_histories = list_backups(SYSTEM_NAME)
            if saved_histories:
                selected = st.selectbox("选择历史记录", ["当前记录"] + saved_histories)
                if selected != "当前记录":
                    if st.button("📂 加载选中记录"):
                        history = load_chat_history(SYSTEM_NAME, selected)
                        if history:
                            st.session_state.chat_history = history
                            st.success("历史记录已加载")
                            st.rerun()

        st.markdown("---")
        st.markdown("### 📋 系统状态")
        status_color = "status-active" if st.session_state.engine_initialized else "status-inactive"
        st.markdown(f"<span class='{status_color}'></span> 知识库引擎: {'已就绪' if st.session_state.engine_initialized else '未就绪'}", unsafe_allow_html=True)
        st.markdown(f"📄 索引状态: {st.session_state.index_load_status}")

    st.markdown('<h1 class="main-header">🛒 电商零售智能问答系统</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">基于RAG技术的电商零售知识问答平台，支持商品咨询、购物指南、售后服务等</p>', unsafe_allow_html=True)

    st.markdown("---")

    if not st.session_state.engine_initialized:
        st.warning("⚠️ 请先加载预置索引或上传文档知识库")
        st.markdown("""
        ### 🚀 快速开始
        1. 点击左侧 **🔄 加载预置索引** 按钮
        2. 或在 **📤 上传文档** 中上传您的知识库文件
        3. 然后在下方输入您的问题
        """)
    else:
        question = st.chat_input("请输入您的问题...", key="chat_input")

        if question:
            with st.chat_message("user"):
                st.markdown(question)

            st.session_state.chat_history.append({"role": "user", "content": question})

            with st.spinner("正在思考..."):
                try:
                    context_docs = st.session_state.vector_store.similarity_search(question, k=st.session_state.top_k)

                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        full_response = ""

                        for chunk in llm_chain_stream(question, context_docs, st.session_state.temperature):
                            full_response += chunk
                            message_placeholder.markdown(full_response + "▌")

                        message_placeholder.markdown(full_response)

                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})

                    with st.expander("📖 参考文档"):
                        for i, doc in enumerate(context_docs, 1):
                            st.markdown(f"**文档 {i}:**")
                            st.markdown(f"来源: {doc.metadata.get('source', '未知')}")
                            st.markdown(f"内容: {doc.page_content[:200]}...")
                            st.markdown("---")

                    op_logger.log_question_answered(question, len(context_docs))

                except Exception as e:
                    st.error(f"回答生成失败: {str(e)}")

        if st.session_state.chat_history:
            st.markdown("### 💬 对话历史")
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.markdown(msg["content"])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(msg["content"])

    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>电商零售智能问答系统 v2.1.0 | 基于RAG技术构建</p>
        <p>如有问题，请联系系统管理员</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
