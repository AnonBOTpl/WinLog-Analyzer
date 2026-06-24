@echo off
title Instalowanie WinLog Analyzer
echo ============================================
echo        WinLog Analyzer - Instalacja
echo ============================================
echo.

where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Brak UV. Instaluje...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo [OK] UV zainstalowane. Otworz nowy terminal i uruchom install.bat ponownie.
    pause
    exit /b
)

echo [1/2] Tworzenie wirtualnego srodowiska...
if not exist ".venv" (
    uv venv
) else (
    echo [INFO] Srodowisko juz istnieje.
)

echo [2/2] Instalowanie zaleznosci...
uv sync

echo.
echo ============================================
echo    Instalacja zakonczona!
echo    Uzyj start.bat aby uruchomic.
echo ============================================
pause
