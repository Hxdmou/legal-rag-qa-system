@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

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
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python 版本: %PYTHON_VERSION%

rem 检查是否在虚拟环境中
python -c "import sys; print(sys.prefix)" | findstr /i "venv" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 当前在虚拟环境中运行
) else (
    echo ⚠️ 警告: 建议在虚拟环境中运行，避免依赖冲突
)

rem 检查关键依赖是否安装
echo 📦 检查核心依赖...
python -c "import streamlit; import langchain; import faiss" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 核心依赖已安装
) else (
    echo ⚠️ 警告: 部分依赖缺失，正在尝试安装...
    pip install streamlit langchain faiss-cpu -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败，请手动安装 requirements.txt
        pause
        exit /b 1
    )
)

rem 检查端口是否被占用
echo 🔍 检查端口占用情况...
set PORTS=7861 7869 7870 7871 7872 7873
set "PORT_CONFLICT="
for %%p in (%PORTS%) do (
    netstat -ano | findstr /c:":%%p " >nul 2>&1
    if !errorlevel! equ 0 (
        set "PORT_CONFLICT=!PORT_CONFLICT! %%p"
    )
)

if defined PORT_CONFLICT (
    echo ⚠️ 警告: 以下端口已被占用:%PORT_CONFLICT%
    echo    请关闭占用端口的程序，或修改启动端口
)

echo.
echo ========================================

rem ========================================
rem 启动服务
rem ========================================
echo 🚀 正在启动所有服务...
echo.

rem 启动通用RAG智能问答系统
echo [1/6] 启动 📚 通用RAG智能问答系统...
start "" cmd /k "streamlit run run.py --server.port 7861"
if %errorlevel% neq 0 (
    echo ❌ 启动失败，请检查日志
)

timeout /t 3 /nobreak >nul

rem 启动法律知识问答系统
echo [2/6] 启动 ⚖️ 法律知识问答系统...
start "" cmd /k "streamlit run legal_qa.py --server.port 7869"
if %errorlevel% neq 0 (
    echo ❌ 启动失败，请检查日志
)

timeout /t 3 /nobreak >nul

rem 启动教育知识问答系统
echo [3/6] 启动 🎓 教育知识问答系统...
start "" cmd /k "streamlit run education_qa.py --server.port 7870"
if %errorlevel% neq 0 (
    echo ❌ 启动失败，请检查日志
)

timeout /t 3 /nobreak >nul

rem 启动医疗健康问答系统
echo [4/6] 启动 🏥 医疗健康问答系统...
start "" cmd /k "streamlit run medical_qa.py --server.port 7871"
if %errorlevel% neq 0 (
    echo ❌ 启动失败，请检查日志
)

timeout /t 3 /nobreak >nul

rem 启动金融知识问答系统
echo [5/6] 启动 💰 金融知识问答系统...
start "" cmd /k "streamlit run finance_qa.py --server.port 7872"
if %errorlevel% neq 0 (
    echo ❌ 启动失败，请检查日志
)

timeout /t 3 /nobreak >nul

rem 启动IT技术问答系统
echo [6/6] 启动 💻 IT技术问答系统...
start "" cmd /k "streamlit run tech_qa.py --server.port 7873"
if %errorlevel% neq 0 (
    echo ❌ 启动失败，请检查日志
)

echo.
echo ⏳ 服务正在启动中，请稍候...
timeout /t 10 /nobreak >nul

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
echo 📌 企业级功能：
echo    - 统一配置管理
echo    - 企业级日志系统
echo    - 安全管理模块
echo    - 对话历史管理
echo    - 核心RAG引擎
echo.
echo ⚠️ 重要提示：
echo    - 首次启动可能需要下载模型，请耐心等待
echo    - 如果服务无法启动，请检查端口是否被占用
echo    - 如有问题，请查看各服务窗口的错误日志
echo.
echo ========================================
echo 按任意键退出...
pause >nul
