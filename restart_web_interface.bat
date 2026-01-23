@echo off
echo ========================================
echo  Restarting Unitree Go2 Web Interface
echo ========================================
echo.
echo Stopping any running instances...

REM Kill any running Python processes with web_interface.py
taskkill /F /FI "WINDOWTITLE eq *web_interface.py*" 2>nul

timeout /t 2 /nobreak >nul

echo.
echo Starting web server...
echo Open http://localhost:5000 in your browser
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python web_interface.py

pause

