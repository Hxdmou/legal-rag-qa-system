@echo off
chcp 65001 >nul

echo ========================================
echo    RAG系统 - 选择性启动
echo ========================================
echo.
echo 请选择要启动的系统（可多选，用逗号分隔）：
echo.
echo 1 - 通用RAG智能问答系统 (端口 7861)
echo 2 - 法律知识问答系统 (端口 7869)
echo 3 - 教育知识问答系统 (端口 7870)
echo 4 - 医疗健康问答系统 (端口 7871)
echo 5 - 金融知识问答系统 (端口 7872)
echo 6 - IT技术问答系统 (端口 7873)
echo.
echo 7 - 启动全部系统
echo 0 - 退出
echo.
echo ========================================
echo.

set /p choice=请输入数字选择 (如: 1,3,6):

if "%choice%"=="0" exit /b

if "%choice%"=="7" (
    goto start_all
)

echo.
echo 正在启动所选系统...
echo.

if "%choice%"=="" (
    echo 未选择任何系统，退出。
    pause
    exit /b
)

:: 分割用户输入并启动对应的服务
for %%a in (%choice%) do (
    if "%%a"=="1" (
        echo [1/6] 启动 通用RAG智能问答系统...
        start "RAG通用" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run run.py --server.port 7861 --server.headless true"
    )
    if "%%a"=="2" (
        echo [2/6] 启动 法律知识问答系统...
        start "RAG法律" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run legal_qa.py --server.port 7869 --server.headless true"
    )
    if "%%a"=="3" (
        echo [3/6] 启动 教育知识问答系统...
        start "RAG教育" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run education_qa.py --server.port 7870 --server.headless true"
    )
    if "%%a"=="4" (
        echo [4/6] 启动 医疗健康问答系统...
        start "RAG医疗" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run medical_qa.py --server.port 7871 --server.headless true"
    )
    if "%%a"=="5" (
        echo [5/6] 启动 金融知识问答系统...
        start "RAG金融" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run finance_qa.py --server.port 7872 --server.headless true"
    )
    if "%%a"=="6" (
        echo [6/6] 启动 IT技术问答系统...
        start "RAGIT" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run tech_qa.py --server.port 7873 --server.headless true"
    )
)

timeout /t 3 /nobreak >nul
echo.
echo 启动完成！
echo.
pause
exit /b

:start_all
echo 启动全部6个系统...
echo.

start "RAG通用" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run run.py --server.port 7861 --server.headless true"
timeout /t 2 /nobreak >nul

start "RAG法律" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run legal_qa.py --server.port 7869 --server.headless true"
timeout /t 2 /nobreak >nul

start "RAG教育" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run education_qa.py --server.port 7870 --server.headless true"
timeout /t 2 /nobreak >nul

start "RAG医疗" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run medical_qa.py --server.port 7871 --server.headless true"
timeout /t 2 /nobreak >nul

start "RAG金融" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run finance_qa.py --server.port 7872 --server.headless true"
timeout /t 2 /nobreak >nul

start "RAGIT" cmd /k "cd /d f:\个人作品\legal-rag-qa-system && streamlit run tech_qa.py --server.port 7873 --server.headless true"

echo.
echo 全部系统已启动！
echo.
pause