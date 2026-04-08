@echo off
setlocal EnableExtensions

echo ================================================
echo  Scripts Formula - Pos-instalacao
echo ================================================
echo.

set "APP_ROOT=%~dp0.."
set "PY_EXE="
set "PY_ARGS="

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY_EXE=py"
    set "PY_ARGS=-3"
)

if not defined PY_EXE (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PY_EXE=python"
    )
)

if not defined PY_EXE (
    echo Python nao encontrado no computador.
    echo Instale Python 3.13 e execute este instalador novamente.
    echo Download: https://www.python.org/downloads/release/python-31312/
    start "" "https://www.python.org/downloads/release/python-31312/"
    pause
    exit /b 1
)

echo Atualizando pip...
call :run_python -m pip install --upgrade pip
if errorlevel 1 goto :pip_error

echo Instalando dependencias para todas as funcionalidades...
call :run_python -m pip install --upgrade xlsxwriter pillow streamlit fpdf2
if errorlevel 1 goto :pip_error

echo Copiando scripts para o TQS...
call :run_python "%APP_ROOT%\codigo_fonte\instalar_arquivos_tqs.py"
if errorlevel 1 goto :copy_error

echo.
echo Instalacao finalizada com sucesso.
echo Voce ja pode abrir o programa principal "Scripts Formula".
echo.
exit /b 0

:pip_error
echo.
echo Falha ao instalar dependencias Python.
echo Verifique internet, permissao de escrita e tente novamente.
echo.
pause
exit /b 1

:copy_error
echo.
echo Falha ao copiar arquivos para C:\TQSW\EXEC\PYTHON.
echo Execute como administrador, se necessario, e tente novamente.
echo.
pause
exit /b 1

:run_python
"%PY_EXE%" %PY_ARGS% %*
exit /b %errorlevel%
