@echo off
chcp 65001 >nul
echo ========================================
echo   RAG知识问答系统 - 一键启动
echo ========================================
echo.
echo 正在启动服务...
echo.

start "" cmd /k "streamlit run run.py --server.port 7861"

timeout /t 2 /nobreak >nul

start "" cmd /k "streamlit run medical_qa_fixed.py --server.port 7869"

echo 服务正在启动中，请稍候...
timeout /t 5 /nobreak >nul

echo 正在打开浏览器...
start http://localhost:7861
start http://localhost:7869

echo.
echo 启动完成！
echo 通用RAG问答系统: http://localhost:7861
echo 法律知识问答系统: http://localhost:7869
echo.
echo 按任意键退出...
pause >nul
