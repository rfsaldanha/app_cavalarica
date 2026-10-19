@echo off
setlocal
title Onde estao nossas doencas?
cd /d "%~dp0"

py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 (
    py -3 "%~dp0servidor_local.py"
    goto fim
)

python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 (
    python "%~dp0servidor_local.py"
    goto fim
)

echo Instale o Python 3.10 ou superior para iniciar o painel:
echo https://www.python.org/downloads/windows/
echo Se o instalador oferecer "Add python.exe to PATH", marque essa opcao.
echo Depois da instalacao, abra este arquivo novamente.
pause
exit /b 1

:fim
if errorlevel 1 pause
endlocal
