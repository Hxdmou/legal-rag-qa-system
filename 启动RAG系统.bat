@echo off
chcp 65001 >nul
echo ========================================
echo    RAG智能知识问答系统 - 企业级一键启动
echo ========================================
echo.
echo 版本: 2.0.0
echo 模式: 企业级部署模式
echo.
echo 正在启动所有服务...
echo.

rem 启动通用RAG智能问答系统
echo [1/6] 启动 📚 通用RAG智能问答系统...
start "" cmd /k "streamlit run run.py --server.port 7861"

timeout /t 3 /nobreak >nul

rem 启动法律知识问答系统
echo [2/6] 启动 ⚖️ 法律知识问答系统...
start "" cmd /k "streamlit run medical_qa_fixed.py --server.port 7869"

timeout /t 3 /nobreak >nul

rem 启动教育知识问答系统
echo [3/6] 启动 🎓 教育知识问答系统...
start "" cmd /k "streamlit run education_qa.py --server.port 7870"

timeout /t 3 /nobreak >nul

rem 启动医疗健康问答系统
echo [4/6] 启动 🏥 医疗健康问答系统...
start "" cmd /k "streamlit run medical_qa.py --server.port 7871"

timeout /t 3 /nobreak >nul

rem 启动金融知识问答系统
echo [5/6] 启动 💰 金融知识问答系统...
start "" cmd /k "streamlit run finance_qa.py --server.port 7872"

timeout /t 3 /nobreak >nul

rem 启动IT技术问答系统
echo [6/6] 启动 💻 IT技术问答系统...
start "" cmd /k "streamlit run tech_qa.py --server.port 7873"

echo.
echo 服务正在启动中，请稍候...
timeout /t 10 /nobreak >nul

echo.
echo ⚡ 正在打开浏览器...
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
echo    - 统一配置管理 (config/settings.py)
echo    - 企业级日志系统 (utils/logger.py)
echo    - 安全管理模块 (utils/security.py)
echo    - 对话历史管理 (utils/database.py)
echo    - 核心RAG引擎 (core/rag_engine.py)
echo.
echo ========================================
echo 按任意键退出...
pause >nul