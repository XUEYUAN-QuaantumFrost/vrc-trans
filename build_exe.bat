@echo off
title Build EXE - VRC Translate
color 0E
echo ============================================================
echo    VRC Translate - Build Standalone EXE
echo ============================================================
echo.
echo  This will install all dependencies and build VRC_Translate.exe
echo  May take 5-15 minutes.
echo  Output: dist\VRC_Translate.exe (single file)
echo.
echo  IMPORTANT: Make sure Python 3.10+ is installed and in PATH.
echo.
pause
echo.
echo [1/6] Checking Python...
python --version
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
echo [OK] Python ready
echo.
echo [2/6] Installing dependencies (requirements.txt)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Retrying with China mirror...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to install dependencies!
        echo Please screenshot the error above and send for help.
        echo.
        pause
        exit /b 1
    )
)
echo [OK] Dependencies ready
echo.
echo [3/6] Installing PyInstaller...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo Retrying with China mirror...
    pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to install PyInstaller!
        echo.
        pause
        exit /b 1
    )
)
echo [OK] PyInstaller ready
echo.
echo [4/6] Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo [OK] Cleaned
echo.
echo [5/6] Building EXE with spec file...
echo This may take several minutes, please wait...
echo.
pyinstaller --noconfirm VRC_Translate.spec
if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo [ERROR] Build failed!
    echo ============================================================
    echo.
    echo Please scroll UP to see the actual error message.
    echo Common issues:
    echo   - Missing DLL or module
    echo   - Antivirus blocking PyInstaller
    echo   - Not enough disk space
    echo.
    echo Screenshot the error and send for help.
    echo.
    pause
    exit /b 1
)
echo [OK] Build successful
echo.
echo [6/6] Copying additional files...
if exist dist (
    copy app.ico dist\app.ico >nul 2>&1
    copy README.md dist\README.md >nul 2>&1
    echo [OK] Icon and docs copied
)
echo.
echo ============================================================
echo    Build Complete!
echo ============================================================
echo.
echo  EXE location: dist\VRC_Translate.exe
echo.
echo  First run will automatically download:
echo    - sherpa-onnx model (size depends on chosen model, 80MB~1GB)
echo    - FFmpeg (if needed)
echo.
echo  To distribute: send dist\VRC_Translate.exe + app.ico + README.md
echo.
echo  To create installer:
echo    1. Install Inno Setup from https://jrsoftware.org/isdl.php
echo    2. Open install.iss in Inno Setup Compiler
echo    3. Click Build -^> Compile
echo.
pause
