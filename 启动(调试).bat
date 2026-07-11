@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 调试模式：如有报错会显示在下方，按任意键关闭
echo.
python main.py
echo.
pause
