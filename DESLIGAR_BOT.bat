@echo off
TITLE OMNIQUANT // DESLIGAR MOTOR
echo =========================================
echo   [-] DESLIGANDO MOTOR OMNIQUANT HFT
echo   [-] ENVIANDO SINAL DE PARADA...
echo =========================================
python stop_trigger.py
echo.
echo Sinal enviado.
pause
