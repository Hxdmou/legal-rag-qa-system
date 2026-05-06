@echo off
chcp 65001 >nul

echo ========================================
echo    RAG智能知识问答系统 - 企业级一键启动
echo ========================================
echo.
echo 版本: 2.0.0
echo 模式: 企业级部署模式
echo.

rem ========================================
rem 环境检查
rem ========================================
echo 🧪 正在检查运行环境...

rem 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 Python，请先安装 Python 3.10+
    echo    下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

rem 检查 Python 版本
python --version
echo.

rem 检查关键依赖是否安装
echo 📦 检查核心依赖...
python -c "import streamlit" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ 警告: streamlit 未安装，正在尝试安装...
    pip install streamlit -i https://pypi.tuna.tsinghua.edu.cn/simple
)

python -c "import langchain" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ 警告: langchain 未安装，正在尝试安装...
    pip install langchain langchain-openai langchain-community -i https://pypi.tuna.tsinghua.edu.cn/simple
)

python -c "import faiss" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ 警告: faiss 未安装，正在尝试安装...
    pip install faiss-cpu -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo ✅ 依赖检查完成
echo.

echo ========================================
echo 🚀 正在启动所有服务...
echo.

rem 启动通用RAG智能问答系统
echo [1/6] 启动 📚 通用RAG智能问答系统...
start "RAG通用" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run run.py --server.port 7861"

timeout /t 2 /nobreak >nul

rem 启动法律知识问答系统
echo [2/6] 启动 ⚖️ 法律知识问答系统...
start "RAG法律" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run legal_qa.py --server.port 7869"

timeout /t 2 /nobreak >nul

rem 启动教育知识问答系统
echo [3/6] 启动 🎓 教育知识问答系统...
start "RAG教育" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run education_qa.py --server.port 7870"

timeout /t 2 /nobreak >nul

rem 启动医疗健康问答系统
echo [4/6] 启动 🏥 医疗健康问答系统...
start "RAG医疗" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run medical_qa.py --server.port 7871"

timeout /t 2 /nobreak >nul

rem 启动金融知识问答系统
echo [5/6] 启动 💰 金融知识问答系统...
start "RAG金融" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run finance_qa.py --server.port 7872"

timeout /t 2 /nobreak >nul

rem 启动IT技术问答系统
echo [6/6] 启动 💻 IT技术问答系统...
start "RAGIT" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run tech_qa.py --server.port 7873"

echo.
echo ⏳ 服务正在启动中，请稍候...
timeout /t 5 /nobreak >nul

echo.
echo 🌐 正在打开浏览器...
start http://localhost:7861
start http://localhost:7869

echo.
echo ========================================
echo           启动完成！
echo ========================================
echo.
echo 📋 系统列表：
echo 📚 通用RAG智能问答系统:    http://localhost:7861
echo ⚖️ 法律知识问答系统:        http://localhost:7869
echo 🎓 教育知识问答系统:        http://localhost:7870
echo 🏥 医疗健康问答系统:        http://localhost:7871
echo 💰 金融知识问答系统:        http://localhost:7872
echo 💻 IT技术问答系统:          http://localhost:7873
echo.
echo ⚠️ 重要提示：
echo    - 首次启动可能需要下载模型，请耐心等待
echo    - 如果服务无法启动，请检查端口是否被占用
echo    - 如有问题，请查看各服务窗口的错误日志
echo.
echo ========================================
echo 按任意键退出...
pause >nul
