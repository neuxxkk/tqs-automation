@echo off
echo A iniciar o Calculo de Beiral...
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -Uri http://localhost:8507/_stcore/health -TimeoutSec 1 | Out-Null; Start-Process http://localhost:8507; exit 0 } catch { exit 1 }"
if %ERRORLEVEL%==0 exit /b 0
python -m streamlit run ..\src\calc_beiral.py --browser.gatherUsageStats false --server.fileWatcherType none --server.showEmailPrompt false --server.address localhost --server.port 8507 --logger.level error
