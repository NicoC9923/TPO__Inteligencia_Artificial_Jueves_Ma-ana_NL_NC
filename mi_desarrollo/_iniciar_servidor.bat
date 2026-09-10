@echo off
cd /d "%~dp0"
py -3 servidor_voz.py
echo.
echo   El servidor se cerro. Si fue por un error, mira el mensaje arriba.
pause
