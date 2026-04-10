@echo off
TITLE OMNIQUANT // DESLIGAR MOTOR IQ DIGITAL
echo =========================================
echo   [+] ENVIANDO SINAL DE PARADA
echo   [+] O motor encerrara apos trades pendentes
echo =========================================
echo.
cd /d "%~dp0"
.venv\Scripts\python.exe stop_trigger.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Nao foi possivel conectar ao servidor.
)
echo.
pause
