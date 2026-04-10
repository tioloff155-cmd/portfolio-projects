@echo off
TITLE OMNIQUANT // INICIAR DASHBOARD IQ DIGITAL
echo =========================================
echo   [+] OMNIQUANT - IQ DIGITAL ENGINE
echo   [+] Iniciando Dashboard Web...
echo   [+] Acesse: http://127.0.0.1:8080
echo =========================================
echo.
cd /d "%~dp0"
.venv\Scripts\python.exe app.py
pause
