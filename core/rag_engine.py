import os
from typing import List, Dict, Any, Optional
from langchain.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredExcelLoader,
    Docx2txtLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough, RunnableParallel
from config.settings import Config
from utils.logger import Logger
from utils.security import SecurityManager

class RAGEngine:
    """企业级RAG引擎核心"""
    
    def __init__(self):
        self.embeddings = self._init_embeddings()
        self.llm = self._init_llm()
        self.vector_store = None
        self.security_manager = SecurityManager()
    
    def _init_embeddings(self):
        """初始化向量嵌入模型"""
        try:
            return OpenAIEmbeddings(
                model=Config.EMBEDDING_MODEL,
                openai_api_key=Config.LLM_API_KEY,
                openai_api_base=Config.LLM_BASE_URL
            )
        except Exception as e:
            Logger.log_error(f"初始化嵌入模型失败: {str(e)}", "RAGEngine", e)
            raise
    
    def _init_llm(self):
        """初始化大语言模型"""
        try:
            return ChatOpenAI(
                model_name=Config.LLM_MODEL_NAME,
                openai_api_key=Config.LLM_API_KEY,
                openai_api_base=Config.LLM_BASE_URL,
                max_tokens=Config.LLM_MAX_TOKENS,
                temperature=Config.LLM_TEMPERATURE
            )
        except Exception as e:
            Logger.log_error(f"初始化LLM失败: {str(e)}", "RAGEngine", e)
            raise
    
    def load_document(self, file_path: str) -> List[Any]:
        """加载单个文档"""
        try:
            ext = file_path.split('.')[-1].lower()
            
            if ext == 'txt':
                loader = TextLoader(file_path, encoding='utf-8')
            elif ext == 'pdf':
                loader = PyPDFLoader(file_path)
            elif ext in ['xlsx', 'xls']:
                loader = UnstructuredExcelLoader(file_path)
            elif ext == 'docx':
                loader = Docx2txtLoader(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {ext}")
            
            docs = loader.load()
            Logger.log_info(f"文档加载成功: {file_path}", "RAGEngine")
            return docs
        except Exception as e:
            Logger.log_error(f"加载文档失败: {str(e)}", "RAGEngine", e)
            raise
    
    def load_multiple_documents(self, file_paths: List[str]) -> List[Any]:
        """加载多个文档"""
        all_docs = []
        for file_path in file_paths:
            if self.security_manager.is_allowed_file_type(file_path):
                docs = self.load_document(file_path)
                all_docs.extend(docs)
            else:
                Logger.log_warning(f"文件类型不允许: {file_path}", "RAGEngine")
        
        Logger.log_info(f"共加载 {len(all_docs)} 个文档", "RAGEngine")
        return all_docs
    
    def chunk_documents(self, docs: List[Any]) -> List[Any]:
        """文档分块处理"""
        try:
            if not docs:
                raise ValueError("文档列表为空")
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=Config.CHUNK_SIZE,
                chunk_overlap=Config.CHUNK_OVERLAP,
                length_function=len
            )
            
            chunks = text_splitter.split_documents(docs)
            Logger.log_info(f"文档分块完成: {len(chunks)} 块", "RAGEngine")
            return chunks
        except Exception as e:
            Logger.log_error(f"文档分块失败: {str(e)}", "RAGEngine", e)
            raise
    
    def build_vector_store(self, docs: List[Any]) -> FAISS:
        """构建向量存储"""
        try:
            chunks = self.chunk_documents(docs)
            
            if not chunks:
                raise ValueError("文档分块后为空")
            
            vector_store = FAISS.from_documents(
                documents=chunks,
                embedding=self.embeddings
            )
            
            Logger.log_info("向量存储构建完成", "RAGEngine")
            self.vector_store = vector_store
            return vector_store
        except Exception as e:
            Logger.log_error(f"构建向量存储失败: {str(e)}", "RAGEngine", e)
            raise
    
    def query_expansion(self, question: str) -> List[str]:
        """查询扩展，生成多个相关查询"""
        expansions = [question]
        
        # 添加同义词和变体
        expansions.append(f"关于{question}的详细信息")
        expansions.append(f"{question}是什么")
        expansions.append(f"{question}的定义")
        expansions.append(f"{question}的解释")
        
        return expansions[:3]  # 返回前3个扩展查询
    
    def create_qa_chain(self, system_prompt: str = "") -> Any:
        """创建问答链"""
        try:
            if not self.vector_store:
                raise ValueError("向量存储未初始化")
            
            # 构建检索器
            retriever = self.vector_store.as_retriever(
                search_kwargs={"k": Config.TOP_K}
            )
            
            # 构建提示词模板
            default_prompt = """
            你是一个专业的问答助手。请根据提供的上下文信息回答问题。
            如果你不知道答案，直接说"我不知道"。

            问题：{question}
            上下文：{context}

            回答：
            """
            
            prompt_template = ChatPromptTemplate.from_template(
                system_prompt if system_prompt else default_prompt
            )
            
            # 构建检索增强链
            def retrieve_with_expansion(question):
                expanded_queries = self.query_expansion(question)
                all_docs = []
                seen_docs = set()
                
                for query in expanded_queries:
                    docs = self.vector_store.similarity_search(query, k=Config.TOP_K)
                    for doc in docs:
                        doc_id = f"{doc.metadata.get('source', '')}:{doc.page_content[:100]}"
                        if doc_id not in seen_docs:
                            seen_docs.add(doc_id)
                            all_docs.append(doc)
                        if len(all_docs) >= Config.TOP_K:
                            break
                    if len(all_docs) >= Config.TOP_K:
                        break
                
                return "\n\n".join([doc.page_content for doc in all_docs])
            
            chain = (
                RunnableParallel({
                    "context": retrieve_with_expansion,
                    "question": RunnablePassthrough()
                })
                | prompt_template
                | self.llm
                | StrOutputParser()
            )
            
            Logger.log_info("问答链创建完成", "RAGEngine")
            return chain
        except Exception as e:
            Logger.log_error(f"创建问答链失败: {str(e)}", "RAGEngine", e)
            raise
    
    def answer_question(self, question: str, system_prompt: str = "") -> str:
        """回答问题"""
        try:
            if not self.vector_store:
                return "请先上传文档并建立索引"
            
            chain = self.create_qa_chain(system_prompt)
            answer = chain.invoke(question)
            
            Logger.log_info(f"问题回答完成: {question[:30]}...", "RAGEngine")
            return answer
        except Exception as e:
            Logger.log_error(f"回答问题失败: {str(e)}", "RAGEngine", e)
            return f"回答问题时发生错误: {str(e)}"
    
    def save_vector_store(self, path: str):
        """保存向量存储到本地"""
        try:
            if self.vector_store:
                self.vector_store.save_local(path)
                Logger.log_info(f"向量存储已保存: {path}", "RAGEngine")
        except Exception as e:
            Logger.log_error(f"保存向量存储失败: {str(e)}", "RAGEngine", e)
            raise
    
    def load_vector_store(self, path: str):
        """从本地加载向量存储"""
        try:
            self.vector_store = FAISS.load_local(
                path,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True
            )
            Logger.log_info(f"向量存储已加载: {path}", "RAGEngine")
        except Exception as e:
            Logger.log_error(f"加载向量存储失败: {str(e)}", "RAGEngine", e)
            raise
