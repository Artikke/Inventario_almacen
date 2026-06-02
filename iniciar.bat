@echo off
echo ==========================================
echo    Sistema de Inventario - Almacen v2.0
echo ==========================================
echo.
echo Iniciando servidor...
echo Abre tu navegador en: http://localhost:8502
echo.
cd /d "%~dp0"
python -m streamlit run app.py --server.port 8502 --server.headless true
pause
