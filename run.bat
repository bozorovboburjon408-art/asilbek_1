@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

where python >nul 2>nul
if errorlevel 1 (
    echo Python topilmadi. https://www.python.org dan o'rnating va "Add to PATH" ni belgilang.
    pause & exit /b 1
)

if not exist .venv (
    echo Virtual muhit yaratilmoqda...
    python -m venv .venv || (pause & exit /b 1)
    call .venv\Scripts\activate.bat
    python -m pip install -q --upgrade pip
    pip install -q -r requirements.txt || (pause & exit /b 1)
) else (
    call .venv\Scripts\activate.bat
)

if "%ANTHROPIC_API_KEY%"=="" (
    if exist .env (
        for /f "usebackq tokens=1,* delims==" %%a in (".env") do if "%%a"=="ANTHROPIC_API_KEY" set "ANTHROPIC_API_KEY=%%b"
    )
)
if "%ANTHROPIC_API_KEY%"=="" (
    set /p ANTHROPIC_API_KEY=ANTHROPIC_API_KEY kiriting: 
)

set "PROMPT=%~1"
if "%PROMPT%"=="" set /p PROMPT=Nima chizish kerak? 

python main.py "%PROMPT%" %2 %3 %4
echo.
pause
