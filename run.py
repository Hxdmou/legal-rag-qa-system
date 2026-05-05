import streamlit as st
import os
import tempfile
import json
from datetime import datetime
from rag import llm_an, load_multiple_documents, chunk2vector, llm_chain, embeddings
# 对话历史保存路径
CHAT_HISTORY_FILE = "chat_history.json"
def save_uploaded_file(uploaded_file):
    """保存上传的文件到临时目录"""
    try:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"文件保存失败: {str(e)}")
        return None
def load_chat_history():
    """加载对话历史"""
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []
def save_chat_history(history):
    """保存对话历史"""
    try:
        with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存对话历史失败: {str(e)}")
def clear_chat_history():
    """清空对话历史"""
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)
    st.session_state.chat_history = []
    st.session_state.messages = []
def interactive():
    st.set_page_config(
        page_title="RAG智能问答系统",
        page_icon="📚",
        layout="wide"
    )

    st.title("📚 RAG 智能问答系统")
    st.markdown("基于检索增强生成技术，支持 **TXT**、**PDF**、**Excel** 等多种文档格式")

    # 初始化session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = load_chat_history()
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = None
    if 'current_files' not in st.session_state:
        st.session_state.current_files = []
    # 侧边栏
    with st.sidebar:
        st.header("📁 文档管理")

        # 文件上传
        uploaded_files = st.file_uploader(
            "上传文档（支持多选）",
            type=['txt', 'pdf', 'xlsx', 'xls'],
            accept_multiple_files=True,
            help="支持同时上传多个文件，系统会自动建立索引"
        )

        # 本地文件路径
        st.markdown("---")
        st.subheader("或输入本地文件路径")
        local_file_path = st.text_input(
            "文件路径",
            placeholder=r"例如: C:\Users\Documents\文件.pdf",
            help="输入本地文件的完整路径"
        )

        # 处理文件上传
        if uploaded_files or local_file_path:
            with st.spinner("正在处理文档并建立索引..."):
                file_paths = []

                # 处理上传的文件
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        tmp_path = save_uploaded_file(uploaded_file)
                        if tmp_path:
                            file_paths.append(tmp_path)
                            st.success(f"✅ 已加载: {uploaded_file.name}")

                # 处理本地文件
                if local_file_path and os.path.exists(local_file_path):
                    file_paths.append(local_file_path)
                    st.success(f"✅ 已加载本地文件: {os.path.basename(local_file_path)}")
                elif local_file_path:
                    st.error(f"❌ 文件不存在: {local_file_path}")

                # 建立向量索引
                if file_paths:
                    try:
                        if len(file_paths) == 1:
                            from rag import text_chunk
                            docs = text_chunk(file_paths[0])
                        else:
                            docs = load_multiple_documents(file_paths)

                        st.session_state.vector_store = chunk2vector(docs, embeddings)
                        st.session_state.current_files = file_paths
                        st.success("✅ 文档索引建立完成！")
                    except Exception as e:
                        st.error(f"建立索引失败: {str(e)}")

        # 显示当前加载的文件
        if st.session_state.current_files:
            st.markdown("---")
            st.subheader("📄 当前文档")
            for fp in st.session_state.current_files:
                st.text(f"• {os.path.basename(fp)}")

        # 对话历史管理
        st.markdown("---")
        st.subheader("💬 对话历史")

        if st.session_state.chat_history:
            st.info(f"已有 {len(st.session_state.chat_history)} 条历史对话")

            # 展开显示历史对话
            with st.expander("📋 查看历史对话记录", expanded=False):
                for i, chat in enumerate(reversed(st.session_state.chat_history), 1):
                    st.markdown(f"**对话 {len(st.session_state.chat_history) - i + 1}**")
                    st.markdown(f"📅 {chat['timestamp']}")
                    st.markdown(f"**问题:** {chat['question']}")
                    st.markdown(f"**回答:** {chat['answer']}")
                    st.markdown("---")

            if st.button("🗑️ 清空历史", type="secondary"):
                clear_chat_history()
                st.success("对话历史已清空")
                st.rerun()
        else:
            st.info("暂无对话历史")
    # 主界面 - 对话区域
    if st.session_state.vector_store is None:
        st.info("👈 请先在左侧上传文档或输入文件路径")

        # 使用说明
        st.markdown("---")
        st.subheader("📖 如何使用RAG智能问答系统")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **操作步骤:**

            1. 📤 **上传文档**
               在左侧上传TXT、PDF或Excel文件，或输入本地文件路径

            2. ⏳ **等待索引**
               系统会自动处理文档并建立向量索引

            3. 💬 **开始提问**
               在下方输入框输入你的问题

            4. 📝 **获取答案**
               系统会基于文档内容生成回答
            """)

        with col2:
            st.markdown("""
            **支持的文件格式:**

            - 📄 TXT文本文件
            - 📑 PDF文档
            - 📊 Excel表格（.xlsx, .xls）

            **功能特点:**

            - ✅ 支持多文件同时上传
            - ✅ 支持本地文件路径输入
            - ✅ 智能文本分块和向量化
            - ✅ 基于文档内容的精准回答
            - ✅ 多轮对话历史记录
            - ✅ 对话历史自动保存
            """)
    else:
        # 显示对话历史
        st.markdown("---")
        st.subheader("💬 对话")

        # 显示历史消息
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # 用户输入
        if question := st.chat_input("请输入您的问题..."):
            # 添加用户消息
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            # 生成回答
            with st.chat_message("assistant"):
                with st.spinner("AI 正在思考..."):
                    try:
                        chain = llm_chain(st.session_state.vector_store)
                        answer = chain.invoke(question)
                        st.markdown(answer)

                        # 保存到对话历史
                        st.session_state.messages.append({"role": "assistant", "content": answer})

                        # 保存到文件
                        st.session_state.chat_history.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "question": question,
                            "answer": answer
                        })
                        save_chat_history(st.session_state.chat_history)

                    except Exception as e:
                        st.error(f"处理出错: {str(e)}")
if __name__ == "__main__":
    interactive()