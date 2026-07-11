@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 正在检查 PyInstaller...
python -m pip install pyinstaller -q
if errorlevel 1 (
    echo 安装 PyInstaller 失败，请确认已安装 Python 并加入 PATH。
    pause
    exit /b 1
)

echo 开始打包 Prekikoeru-KM.exe ...
python build.py
if errorlevel 1 (
    echo 打包失败。
    pause
    exit /b 1
)

echo.
echo 完成。启动文件：dist\Prekikoeru-KM.exe
pause
