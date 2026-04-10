@echo off
TITLE OMNIQUANT // LIGAR MOTOR IQ DIGITAL
echo =========================================
echo   [+] INICIANDO MOTOR IQ DIGITAL
echo   [+] CERTIFIQUE-SE QUE O DASHBOARD ESTA RODANDO!
echo =========================================
echo.
cd /d "%~dp0"
.venv\Scripts\python.exe trigger_bot.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Nao foi possivel conectar ao servidor. 
    echo Verifique se o arquivo "1_INICIAR_DASHBOARD.bat" esta aberto.
)
echo.
pause
