import streamlit as st
import os
import tempfile
import json
from datetime import datetime
from rag import llm_an, load_multiple_documents, chunk2vector, llm_chain, embeddings
# 对话历史保存路径
CHAT_HISTORY_FILE = "legal_chat_history.json"
# 知识库存储路径
KNOWLEDGE_BASE_DIR = "legal_knowledge_base"
# 初始化知识库目录
if not os.path.exists(KNOWLEDGE_BASE_DIR):
    os.makedirs(KNOWLEDGE_BASE_DIR)
def save_uploaded_file(uploaded_file):
    """保存上传的文件到知识库目录"""
    try:
        # 保存到知识库目录
        file_path = os.path.join(KNOWLEDGE_BASE_DIR, uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        return file_path
    except Exception as e:
        st.error(f"文件保存失败: {str(e)}")
        return None
def load_chat_history():
    """加载对话历史"""
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"加载对话历史失败: {str(e)}")
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
def get_knowledge_base_files():
    """获取知识库中的文件"""
    if os.path.exists(KNOWLEDGE_BASE_DIR):
        return [f for f in os.listdir(KNOWLEDGE_BASE_DIR) if os.path.isfile(os.path.join(KNOWLEDGE_BASE_DIR, f))]
    return []
def delete_knowledge_file(file_name):
    """删除知识库中的文件"""
    file_path = os.path.join(KNOWLEDGE_BASE_DIR, file_name)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            st.error(f"删除文件失败: {str(e)}")
    return False
def load_knowledge_base():
    """加载整个知识库"""
    files = get_knowledge_base_files()
    if not files:
        return None

    file_paths = [os.path.join(KNOWLEDGE_BASE_DIR, f) for f in files]
    try:
        docs = load_multiple_documents(file_paths)
        if not docs:
            st.warning("知识库文件加载后为空")
            return None
        vector_store = chunk2vector(docs, embeddings)
        return vector_store
    except Exception as e:
        st.error(f"加载知识库失败: {str(e)}")
        return None
def interactive():
    st.set_page_config(
        page_title="法律知识问答系统",
        page_icon="⚖️",
        layout="wide"
    )

    st.title("⚖️ 法律知识问答系统")
    st.markdown("基于检索增强生成技术的法律知识智能问答系统")
    st.markdown("支持上传法律文档，建立知识库，并通过RAG技术回答法律相关问题")

    # 初始化session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = load_chat_history()
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = None
    if 'current_files' not in st.session_state:
        st.session_state.current_files = []
    # 侧边栏 - 知识库管理
    with st.sidebar:
        st.header("📁 知识库管理")

        # 文件上传
        uploaded_files = st.file_uploader(
            "上传法律文档（支持多选）",
            type=['txt', 'pdf', 'xlsx', 'xls'],
            accept_multiple_files=True,
            help="支持同时上传多个法律相关文档，系统会自动添加到知识库"
        )

        # 处理文件上传
        if uploaded_files:
            with st.spinner("正在处理文档并添加到知识库..."):
                for uploaded_file in uploaded_files:
                    file_path = save_uploaded_file(uploaded_file)
                    if file_path:
                        st.success(f"✅ 已添加到知识库: {uploaded_file.name}")

                # 重新加载知识库
                st.session_state.vector_store = load_knowledge_base()
                st.session_state.current_files = get_knowledge_base_files()
                st.success("✅ 知识库更新完成！")

        # 显示当前知识库文件
        if get_knowledge_base_files():
            st.markdown("---")
            st.subheader("📄 知识库文件")

            files_to_delete = []
            for file_name in get_knowledge_base_files():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"• {file_name}")
                with col2:
                    if st.button("🗑️", key=f"delete_{file_name}"):
                        files_to_delete.append(file_name)

            # 处理删除操作
            for file_name in files_to_delete:
                if delete_knowledge_file(file_name):
                    st.success(f"✅ 已删除: {file_name}")
                    # 重新加载知识库
                    st.session_state.vector_store = load_knowledge_base()
                    st.session_state.current_files = get_knowledge_base_files()
                    st.rerun()
        else:
            st.info("知识库为空，请上传法律文档")

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
    st.markdown("---")
    st.subheader("💬 对话")

    # 显示历史消息
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 用户输入
    if question := st.chat_input("请输入您的法律问题..."):
        # 检查知识库是否加载
        if st.session_state.vector_store is None:
            st.error("⚠️ 请先在左侧上传法律文档到知识库，然后再提问")
        else:
            # 添加用户消息
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            # 生成回答
            with st.chat_message("assistant"):
                with st.spinner("AI 正在分析..."):
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
    # 使用说明
    st.markdown("---")
    st.subheader("📖 如何使用法律知识问答系统")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **操作步骤:**

        1. 📤 **上传文档**
           在左侧上传法律相关的TXT、PDF或Excel文件

        2. ⏳ **等待处理**
           系统会自动处理文档并添加到知识库

        3. 💬 **开始提问**
           在下方输入框输入你的法律问题

        4. 📝 **获取答案**
           系统会基于知识库内容生成专业回答
        """)

    with col2:
        st.markdown("""
        **支持的文件格式:**

        - 📄 TXT文本文件
        - 📑 PDF文档
        - 📊 Excel表格（.xlsx, .xls）

        **功能特点:**

        - ✅ 支持多文件同时上传
        - ✅ 智能文本分块和向量化
        - ✅ 基于法律知识库的精准回答
        - ✅ 多轮对话历史记录
        - ✅ 对话历史自动保存
        - ✅ 知识库文件管理（查看和删除）
        """)
if __name__ == "__main__":
    interactive()