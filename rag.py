import streamlit as st
import os.path
import time
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredExcelLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
from langchain_community.embeddings import DashScopeEmbeddings
'''
如果需要使用OpenAI密钥对 请解除这部分注释 并将42-47行部分阿里云的llm和embedding加载部分注释掉
load_dotenv('/Users/kane/PycharmProjects/rag_demo/.env')
openai_endpoint: str = os.getenv('OPENAI_ENDPOINT')
openai_api_key: str = os.getenv('OPENAI_API_KEY')
openai_api_version: str = os.getenv('OPENAI_API_VERSION')
openai_deployment: str = os.getenv('OPENAI_DEPLOYMENT')
embedding_deployment: str = os.getenv('EMBEDDING_DEPLOYMENT')
embedding_api_version: str = os.getenv('EMBEDDING_API_VERSION')
embedding_api_key: str = os.getenv('EMBEDDING_API_KEY')
embedding_endpoint: str = os.getenv('EMBEDDING_ENDPOINT')
llm = ChatOpenAI(
    deployment=openai_deployment,
    openai_api_version=openai_api_version,
    endpoint=openai_endpoint,
    api_key=openai_api_key,
)
embeddings = OpenAIEmbeddings(
    openai_api_version=embedding_api_version,
    base_url=embedding_endpoint,
    api_key=embedding_api_key,
    deployment=embedding_deployment
 )
'''
dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
if not dashscope_api_key:
    raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")

embeddings = DashScopeEmbeddings(
    model="text-embedding-v2",
    dashscope_api_key=dashscope_api_key)
llm = ChatOpenAI(base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
                 api_key=dashscope_api_key,
                 model="qwen2.5-72b-instruct", temperature=0.7)
def load_document(file_path):
    """
    根据文件类型加载文档，支持 txt、pdf、xlsx、xls 格式
    """
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.txt':
        loader = TextLoader(file_path, encoding='utf-8')
    elif file_extension == '.pdf':
        loader = PyPDFLoader(file_path)
    elif file_extension in ['.xlsx', '.xls']:
        loader = UnstructuredExcelLoader(file_path, mode="elements")
    else:
        raise ValueError(f"不支持的文件格式: {file_extension}，仅支持 .txt, .pdf, .xlsx, .xls")

    docs = loader.load()
    print(f"已加载文件: {file_path}, 类型: {file_extension}, 文档数: {len(docs)}")
    if docs:
        print(f"第一条文档元数据: {docs[0].metadata}")
    return docs
def text_chunk(file_path):
    """
    加载文件并按文本分割成 chunks
    """
    docs = load_document(file_path)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = text_splitter.split_documents(docs)
    return chunks
def load_multiple_documents(file_paths):
    """
    加载多个文档文件，支持混合类型
    file_paths: 文件路径列表
    """
    all_docs = []
    for file_path in file_paths:
        try:
            docs = load_document(file_path)
            all_docs.extend(docs)
        except Exception as e:
            print(f"加载文件失败 {file_path}: {str(e)}")

    return all_docs
def chunk2vector(docs, embeddings):
    if not docs:
        raise ValueError("文档列表为空，无法创建向量存储")
    
    print(f"正在分割 {len(docs)} 个文档...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = text_splitter.split_documents(docs)
    
    print(f"文档分割完成，共 {len(chunks)} 个 chunks")

    if not chunks:
        raise ValueError("文档分割后为空，无法创建向量存储")

    print("正在创建FAISS向量索引...")
    vector = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings
        )
    print("向量索引创建完成")
    return vector
def query_expansion(question):
    """
    扩展用户查询，提高检索准确性
    """
    expansion_template = """你是一个查询扩展专家，你的任务是将用户的问题扩展为多个相关的查询，以提高信息检索的准确性。
    原始问题: {question}
    请提供3个不同角度的扩展查询，每个查询都应该与原始问题相关，但从不同的角度表达。
    例如，如果原始问题是"如何治疗感冒"，扩展查询可以是：
    1. 感冒的常见治疗方法有哪些
    2. 感冒的药物治疗方案
    3. 感冒的自然疗法和家庭护理
    输出格式：
    1. 扩展查询1
    2. 扩展查询2
    3. 扩展查询3"""

    expansion_prompt = ChatPromptTemplate.from_template(expansion_template)
    expansion_chain = expansion_prompt | llm | StrOutputParser()
    expanded_queries = expansion_chain.invoke({"question": question})

    queries = []
    for line in expanded_queries.split('\n'):
        line = line.strip()
        if line and line[0].isdigit() and '.' in line:
            queries.append(line.split('.', 1)[1].strip())

    if not queries:
        queries = [question]
    else:
        queries.insert(0, question)

    return queries
def llm_chain(vector):
    template = """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know.
    Question: {question}
    Context: {context}
    Answer:"""
    prompt = ChatPromptTemplate.from_template(template)

    def retrieve_with_expansion(question):
        expanded_queries = query_expansion(question)

        all_docs = []
        seen_docs = set()

        for query in expanded_queries[:3]:
            docs = vector.similarity_search(query, k=3)

            for doc in docs:
                doc_id = f"{doc.metadata.get('source', '')}:{doc.page_content[:100]}"
                if doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    all_docs.append(doc)

                if len(all_docs) >= 5:
                    break

            if len(all_docs) >= 5:
                break

        return all_docs

    chain = (
            RunnableParallel({"context": retrieve_with_expansion, "question": RunnablePassthrough()})
            | prompt
            | llm
            | StrOutputParser()
    )
    return chain
def llm_an(file_path, question):
    if not question:
        question = "hello"
    docs = text_chunk(file_path)
    vetcor = chunk2vector(docs, embeddings)
    chain = llm_chain(vetcor)
    answer = chain.invoke(question)
    return answer
def interactive():
    st.title("RAG 检索增强生成系统")

    with st.sidebar:
        st.header("知识库管理")

        operation = st.selectbox(
            "选择操作",
            ["构建新知识库", "添加文档", "查看/删除文档", "清空知识库"]
        )

        if operation == "构建新知识库":
            uploaded_files = st.file_uploader("上传文档", accept_multiple_files=True,
                                         type=["txt", "pdf", "xlsx", "xls"])

            if uploaded_files:
                st.info(f"已上传 {len(uploaded_files)} 个文件")
                for file in uploaded_files:
                    st.write(f"- {file.name}")

            if st.button("构建知识库"):
                if uploaded_files:
                    with st.spinner("正在构建知识库..."):
                        try:
                            temp_dir = "temp_uploads"
                            os.makedirs(temp_dir, exist_ok=True)

                            file_paths = []
                            for file in uploaded_files:
                                file_path = os.path.join(temp_dir, file.name)
                                with open(file_path, "wb") as f:
                                    f.write(file.getbuffer())
                                file_paths.append(file_path)

                            docs = load_multiple_documents(file_paths)

                            if docs:
                                vector_store = chunk2vector(docs, embeddings)
                                vector_store.save_local("faiss_index")
                                st.success("知识库构建成功！")
                            else:
                                st.error("未找到有效文档内容")
                        except Exception as e:
                            st.error(f"构建知识库失败: {str(e)}")
                else:
                    st.warning("请先上传文件")

        elif operation == "添加文档":
            if not os.path.exists("faiss_index"):
                st.warning("请先构建知识库")
            else:
                uploaded_files = st.file_uploader("上传要添加的文档", accept_multiple_files=True,
                                             type=["txt", "pdf", "xlsx", "xls"])

                if uploaded_files:
                    st.info(f"已上传 {len(uploaded_files)} 个文件")
                    for file in uploaded_files:
                        st.write(f"- {file.name}")

                if st.button("添加到知识库"):
                    if uploaded_files:
                        with st.spinner("正在添加文档..."):
                            try:
                                vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

                                temp_dir = "temp_uploads"
                                os.makedirs(temp_dir, exist_ok=True)

                                file_paths = []
                                for file in uploaded_files:
                                    file_path = os.path.join(temp_dir, file.name)
                                    with open(file_path, "wb") as f:
                                        f.write(file.getbuffer())
                                    file_paths.append(file_path)

                                new_docs = load_multiple_documents(file_paths)

                                if new_docs:
                                    text_splitter = RecursiveCharacterTextSplitter(
                                        chunk_size=500,
                                        chunk_overlap=50
                                    )
                                    new_chunks = text_splitter.split_documents(new_docs)

                                    vector_store.add_documents(new_chunks)
                                    vector_store.save_local("faiss_index")
                                    st.success(f"成功添加 {len(new_docs)} 个文档到知识库！")
                                else:
                                    st.error("未找到有效文档内容")
                            except Exception as e:
                                st.error(f"添加文档失败: {str(e)}")
                    else:
                        st.warning("请先上传文件")

        elif operation == "查看/删除文档":
            if not os.path.exists("faiss_index"):
                st.warning("请先构建知识库")
            else:
                try:
                    vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

                    docs = vector_store.docstore.documents.values()

                    source_docs = {}
                    for doc in docs:
                        source = doc.metadata.get('source', '未知')
                        if source not in source_docs:
                            source_docs[source] = []
                        source_docs[source].append(doc)

                    if source_docs:
                        st.info(f"知识库中包含 {len(source_docs)} 个源文件")

                        selected_source = st.selectbox(
                            "选择要删除的文件",
                            list(source_docs.keys())
                        )

                        if st.button("删除选中文件"):
                            with st.spinner("正在删除文档..."):
                                try:
                                    all_doc_ids = list(vector_store.docstore.documents.keys())
                                    docs_to_delete = []
                                    for doc_id, doc in vector_store.docstore.documents.items():
                                        if doc.metadata.get('source') == selected_source:
                                            docs_to_delete.append(doc_id)

                                    vector_store.delete(docs_to_delete)
                                    vector_store.save_local("faiss_index")
                                    st.success(f"成功删除文件: {selected_source}")
                                except Exception as e:
                                    st.error(f"删除文档失败: {str(e)}")
                    else:
                        st.info("知识库为空")
                except Exception as e:
                    st.error(f"加载知识库失败: {str(e)}")

        elif operation == "清空知识库":
            if st.button("清空知识库"):
                if os.path.exists("faiss_index"):
                    import shutil
                    shutil.rmtree("faiss_index")
                    st.success("知识库已清空")
                else:
                    st.info("知识库为空")

    st.header("智能问答")

    if not os.path.exists("faiss_index"):
        st.warning("请先构建知识库")
        return

    try:
        vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        st.error(f"加载知识库失败: {str(e)}")
        return

    question = st.text_input("请输入您的问题:")

    if st.button("获取答案"):
        if question:
            with st.spinner("正在生成答案..."):
                try:
                    chain = llm_chain(vector_store)
                    answer = chain.invoke(question)
                    st.success(answer)
                except Exception as e:
                    st.error(f"生成答案失败: {str(e)}")