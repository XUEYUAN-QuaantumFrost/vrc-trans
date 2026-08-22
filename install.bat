@echo off
title VRC Translate Subtitle - Install
color 0B

echo ============================================================
echo    VRC Translate Subtitle - One Click Install
echo ============================================================
echo.
echo  This script will install everything automatically:
echo    1. Check Python
echo    2. Install Python packages
echo    3. Check/Install FFmpeg
echo    4. Check C++ Runtime
echo    5. Create desktop shortcut
echo.
pause

echo.
echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
echo [OK] Python installed

echo.
echo [2/5] Installing Python packages...
echo Fixing setuptools version for webrtcvad compatibility...
pip install "setuptools<80"
pip install -r "%~dp0requirements.txt"
if %errorlevel% neq 0 (
    echo Retrying with China mirror...
    pip install -r "%~dp0requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
)
echo [OK] Packages installed

echo.
echo [3/5] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo FFmpeg not found, trying winget install...
    winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo.
        echo [WARNING] Failed to install FFmpeg via winget.
        echo Please download manually: https://www.gyan.dev/ffmpeg/builds/
        echo Extract and add the bin folder to system PATH.
        echo.
    ) else (
        echo [OK] FFmpeg installed (restart terminal to take effect)
    )
) else (
    echo [OK] FFmpeg found
)

echo.
echo [4/5] Checking C++ Runtime...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Installed >nul 2>&1
if %errorlevel% neq 0 (
    echo VC++ 2015-2022 Runtime not found, downloading...
    powershell -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile '%TEMP%\vc_redist.x64.exe'"
    if exist "%TEMP%\vc_redist.x64.exe" (
        echo Installing C++ Runtime...
        start /wait "%TEMP%\vc_redist.x64.exe" /install /quiet /norestart
        echo [OK] C++ Runtime installed
    ) else (
        echo [WARNING] Download failed. Please install manually:
        echo https://aka.ms/vs/17/release/vc_redist.x64.exe
    )
) else (
    echo [OK] C++ Runtime found
)

echo.
echo [5/5] Creating desktop shortcut...
echo @echo off > "%USERPROFILE%\Desktop\VRC_Translate.bat"
echo cd /d "%~dp0" >> "%USERPROFILE%\Desktop\VRC_Translate.bat"
echo python main.py >> "%USERPROFILE%\Desktop\VRC_Translate.bat"
echo pause >> "%USERPROFILE%\Desktop\VRC_Translate.bat"
echo [OK] Desktop shortcut created

echo.
echo ============================================================
echo    Installation Complete!
echo ============================================================
echo.
echo  How to use:
echo    1. Double-click "VRC_Translate.bat" on desktop to start
echo    2. Right-click tray icon - Settings - enter API Key and device ID
echo    3. To find device ID: run list_devices.py
echo.
pause
