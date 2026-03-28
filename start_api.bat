@echo off
echo ============================================================
echo 🚀 启动智能微习惯追踪器 API 服务
echo ============================================================
echo.
echo 服务启动后，可通过以下地址访问:
echo.
echo    Swagger UI: http://localhost:8000/docs
echo    ReDoc:      http://localhost:8000/redoc
echo.
echo 内网同事访问: http://%COMPUTERNAME%:8000 或 http://[你的IP]:8000
echo.
echo 按 Ctrl+C 停止服务
echo ============================================================
echo.

cd habit_tracker
python api.py

pause
