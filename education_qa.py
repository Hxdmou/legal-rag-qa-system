import streamlit as st
import os
import tempfile
import json
from datetime import datetime
from rag import llm_an, load_multiple_documents, chunk2vector, llm_chain, embeddings

# 对话历史保存路径
CHAT_HISTORY_FILE = "chat_history_education.json"

def save_uploaded_file(uploaded_file):
    try:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"文件保存失败: {str(e)}")
        return None

def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_chat_history(history):
    try:
        with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存对话历史失败: {str(e)}")

def clear_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)
    st.session_state.chat_history = []
    st.session_state.messages = []

def interactive():
    st.set_page_config(
        page_title="教育知识问答系统",
        page_icon="🎓",
        layout="wide"
    )

    st.title("🎓 教育知识问答系统")
    st.markdown("专为学生和教育工作者打造的智能学习助手，支持上传教材、课件等学习资料")

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
        st.header("📁 学习资料管理")
        
        uploaded_files = st.file_uploader(
            "上传学习资料（支持多选）",
            type=['txt', 'pdf', 'xlsx', 'xls'],
            accept_multiple_files=True,
            help="支持教材、课件、笔记等多种格式"
        )

        st.markdown("---")
        st.subheader("或输入本地文件路径")
        local_file_path = st.text_input(
            "文件路径",
            placeholder=r"例如: C:\Users\Documents\教材.pdf",
            help="输入本地文件的完整路径"
        )

        if uploaded_files or local_file_path:
            with st.spinner("正在处理学习资料并建立索引..."):
                file_paths = []
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        tmp_path = save_uploaded_file(uploaded_file)
                        if tmp_path:
                            file_paths.append(tmp_path)
                            st.success(f"✅ 已加载: {uploaded_file.name}")

                if local_file_path and os.path.exists(local_file_path):
                    file_paths.append(local_file_path)
                    st.success(f"✅ 已加载本地文件: {os.path.basename(local_file_path)}")
                elif local_file_path:
                    st.error(f"❌ 文件不存在: {local_file_path}")

                if file_paths:
                    try:
                        docs = load_multiple_documents(file_paths)
                        if docs:
                            vector_store = chunk2vector(docs, embeddings)
                            st.session_state.vector_store = vector_store
                            st.session_state.current_files = [os.path.basename(p) for p in file_paths]
                            st.success("🎉 学习资料索引建立成功！")
                        else:
                            st.error("❌ 未找到有效内容")
                    except Exception as e:
                        st.error(f"处理文件失败: {str(e)}")

        st.markdown("---")
        if st.button("清空对话历史"):
            clear_chat_history()
            st.success("对话历史已清空")

        if st.session_state.current_files:
            st.markdown("### 当前加载的文件")
            for f in st.session_state.current_files:
                st.write(f"- {f}")

    # 主聊天区域
    st.markdown("---")
    st.header("💬 学习问答")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("输入您的学习问题..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if st.session_state.vector_store is not None:
                with st.spinner("正在思考..."):
                    try:
                        chain = llm_chain(st.session_state.vector_store)
                        response = chain.invoke(prompt)
                        st.markdown(response)
                        
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                        chat_entry = {
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "question": prompt,
                            "answer": response
                        }
                        st.session_state.chat_history.append(chat_entry)
                        save_chat_history(st.session_state.chat_history)
                    except Exception as e:
                        st.error(f"回答失败: {str(e)}")
            else:
                st.warning("请先上传学习资料")

if __name__ == "__main__":
    interactive()
