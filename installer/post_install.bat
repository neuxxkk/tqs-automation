@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "PY_EXE="
set "PY_ARGS="

rem Tenta py launcher (descarta free-threading)
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; exit(0 if getattr(sys,'_is_gil_enabled',lambda:True)() else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "PY_EXE=py"
        set "PY_ARGS=-3"
    )
)

if not defined PY_EXE (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; exit(0 if getattr(sys,'_is_gil_enabled',lambda:True)() else 1)" >nul 2>nul
        if not errorlevel 1 set "PY_EXE=python"
    )
)

if not defined PY_EXE (
    where python3 >nul 2>nul
    if not errorlevel 1 (
        python3 -c "import sys; exit(0 if getattr(sys,'_is_gil_enabled',lambda:True)() else 1)" >nul 2>nul
        if not errorlevel 1 set "PY_EXE=python3"
    )
)

if not defined PY_EXE (
    start "" "https://www.python.org/downloads/release/python-31312/"
    exit /b 1
)

rem Abre a GUI de instalacao (pythonw = sem janela de console)
where pythonw >nul 2>nul
if not errorlevel 1 (
    start "" /wait pythonw "%SCRIPT_DIR%post_install_gui.pyw"
) else (
    start "" /wait "%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%post_install_gui.pyw"
)

exit /b %errorlevel%
