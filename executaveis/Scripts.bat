@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "APP_SCRIPT=..\codigo_fonte\Scripts_Formula.py"

where pythonw >nul 2>nul
if %errorlevel%==0 (
	start "" pythonw "%APP_SCRIPT%"
	exit /b 0
)

where py >nul 2>nul
if %errorlevel%==0 (
	start "" py -3 "%APP_SCRIPT%"
	exit /b 0
)

where python >nul 2>nul
if %errorlevel%==0 (
	start "" python "%APP_SCRIPT%"
	exit /b 0
)

echo Python nao encontrado neste computador.
echo Instale Python 3.13 e execute novamente.
echo Download: https://www.python.org/downloads/release/python-31312/
pause
exit /b 1
