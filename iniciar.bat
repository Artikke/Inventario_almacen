@echo off
echo ==========================================
echo    PROESA - Sistema de Inventario
echo ==========================================
echo.
echo Iniciando servidor...
echo Abre tu navegador en: http://localhost:8502
echo.
cd /d "%~dp0"
python app.py
pause
