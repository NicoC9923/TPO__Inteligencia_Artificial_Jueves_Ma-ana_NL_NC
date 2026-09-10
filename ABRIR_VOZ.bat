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
echo   Ojo: servidor_voz.py tiene que estar corriendo antes de esto
echo   (otra ventana con "py -3 servidor_voz.py"), si no la pagina no carga.
echo.

if defined CHROME (
    echo   Abriendo Chrome en %URL%
    start "" "%CHROME%" "%URL%"
) else (
    echo   No se encontro Chrome instalado en las rutas habituales.
    echo   Probando por PATH / registro de Windows...
    start chrome "%URL%"
    echo.
    echo   Si se abrio Brave u otro navegador en vez de Chrome, el
    echo   reconocimiento de voz NO va a andar (error "network"): abri
    echo   %URL% a mano en Chrome.
)

endlocal
