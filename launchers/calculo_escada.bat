@echo off
echo A iniciar o Calculo de Escadas...
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -Uri http://localhost:8508/_stcore/health -TimeoutSec 1 | Out-Null; Start-Process http://localhost:8508; exit 0 } catch { exit 1 }"
if %ERRORLEVEL%==0 exit /b 0
python -m streamlit run ..\src\escada\app.py --browser.gatherUsageStats false --server.fileWatcherType none --server.showEmailPrompt false --server.address localhost --server.port 8508 --logger.level error
