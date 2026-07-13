@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "ERRLOG=%~dp0startup_error.log"
set "FALLBACK_LOG=%TEMP%\ChitoseExtract_startup.log"
set "PY_CMD="

REM 优先 pythonw（与历史启动日志一致）；py launcher 作为备选
where pythonw >nul 2>&1 && set "PY_CMD=pythonw"
if not defined PY_CMD where py >nul 2>&1 && set "PY_CMD=py -3w"
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
    call :log_line "未找到 Python。请安装 Python 3.9+ 并勾选 Add python.exe to PATH。"
    mshta "javascript:alert('未找到 Python，请安装 Python 3.9+ 并勾选 Add to PATH。\n详情见 startup_error.log 或 %%TEMP%%\\ChitoseExtract_startup.log');close()"
    exit /b 1
)

call :log_line "启动命令: %PY_CMD% main.py"
start "" /B %PY_CMD% main.py
exit /b 0

:log_line
>>"%ERRLOG%" 2>nul echo [%date% %time%] %~1
if errorlevel 1 >>"%FALLBACK_LOG%" echo [%date% %time%] %~1
exit /b 0
