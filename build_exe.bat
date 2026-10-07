@echo off
cd /d "%~dp0"
python -m venv .venv-build
call .venv-build\Scripts\activate.bat
pip install -q -r requirements.txt pyinstaller || exit /b 1
pyinstaller --noconfirm --onefile --windowed --name CorelAgent ^
  --hidden-import win32com.client --hidden-import pythoncom gui.py || exit /b 1
echo.
echo Tayyor: dist\CorelAgent.exe
pause
