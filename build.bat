@echo off
REM ============================================================
REM  Compilation de DIP Toolkit Pro  ->  dist\DIP Toolkit Pro.exe
REM  Prerequis : Python 3.12 installe (lanceur "py")
REM ============================================================
cd /d "%~dp0"

if not exist .venv (
    echo [1/3] Creation de l'environnement virtuel Python 3.12...
    py -3.12 -m venv .venv
    if errorlevel 1 (
        echo ERREUR : Python 3.12 introuvable. Installez-le depuis python.org
        pause
        exit /b 1
    )
)

echo [2/3] Installation des dependances...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
if errorlevel 1 (
    echo ERREUR pendant l'installation des dependances.
    pause
    exit /b 1
)

echo [3/3] Compilation...
pyinstaller --noconfirm --clean "DIP Toolkit Pro.spec"
if errorlevel 1 (
    echo ERREUR pendant la compilation.
    pause
    exit /b 1
)

echo.
echo Termine : dist\DIP Toolkit Pro.exe
pause
