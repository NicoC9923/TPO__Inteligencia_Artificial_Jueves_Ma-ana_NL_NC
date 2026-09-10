@echo off
setlocal

set "URL=http://127.0.0.1:8080"
set "CHROME="

REM Busca Chrome en las rutas habituales. Necesita ser Chrome (no el
REM navegador por defecto): Brave y otros forks de Chromium no traen la
REM clave de Google que hace falta para el reconocimiento de voz, y
REM fallan con "network" aunque la red este bien.
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"

echo.
echo   Si todavia no abriste INICIAR_SIMULADOR.bat, el robot no se va a
echo   mover, pero la pagina y el reconocimiento de voz andan igual.
echo.
echo   Iniciando servidor_voz.py en una ventana aparte...
start "Servidor de voz" "%~dp0mi_desarrollo\_iniciar_servidor.bat"

echo   Esperando a que levante el servidor...
ping -n 4 127.0.0.1 >nul

if not defined CHROME goto :sinchrome

echo   Abriendo Chrome en %URL%
start "" "%CHROME%" "%URL%"
goto :fin

:sinchrome
echo   No se encontro Chrome instalado en las rutas habituales.
echo   Probando por PATH / registro de Windows...
start chrome "%URL%"
echo.
echo   Si se abrio Brave u otro navegador en vez de Chrome, el
echo   reconocimiento de voz NO va a andar (error "network"): abri
echo   %URL% a mano en Chrome.

:fin
endlocal
