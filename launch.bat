@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "ERRLOG=%~dp0startup_error.log"
set "PY_CMD="

REM 按优先级查找无窗口 Python 启动方式
where py >nul 2>&1 && set "PY_CMD=py -3w"
if not defined PY_CMD where pythonw >nul 2>&1 && set "PY_CMD=pythonw"
if not defined PY_CMD (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        set "PYTHON_EXE=%%i"
        goto :found_python
    )
)
:found_python
if not defined PY_CMD if defined PYTHON_EXE (
    set "PYW_EXE=%PYTHON_EXE:python.exe=pythonw.exe%"
    if exist "%PYW_EXE%" set "PY_CMD="%PYW_EXE%""
)

if not defined PY_CMD (
    echo [%date% %time%] 未找到 Python。请安装 Python 3.9+ 并勾选 "Add python.exe to PATH"。>> "%ERRLOG%"
    echo 也可尝试安装时勾选 "py launcher"。>> "%ERRLOG%"
    mshta "javascript:alert('未找到 Python，请安装 Python 3.9+ 并勾选 Add to PATH。\n详情见 startup_error.log');close()"
    exit /b 1
)

echo [%date% %time%] 启动命令: %PY_CMD% main.py >> "%ERRLOG%"
%PY_CMD% main.py 2>> "%ERRLOG%"
if errorlevel 1 (
    mshta "javascript:alert('程序启动失败，请打开 startup_error.log 查看错误');close()"
    exit /b 1
)
exit /b 0
