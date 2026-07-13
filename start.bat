@echo off
chcp 65001 >nul
cd /d "%~dp0\src"
"..\venv\Scripts\python.exe" "main.py" %*
echo.
echo 按任意键退出...
pause >nul
