@echo off
echo ============================================================
echo   VRC_Translate Dependency Fix Tool
echo   Uninstall conflicting packages - Clean cache - Reinstall
echo ============================================================
echo.

echo [1/5] Uninstalling conflicting packages...
pip uninstall -y numpy scipy noisereduce ctranslate2 faster-whisper 2>nul
echo.

echo [2/5] Cleaning pip cache...
pip cache purge 2>nul
echo.

echo [3/5] Installing NumPy 1.x (compatible with ctranslate2)...
pip install "numpy>=1.24,<2"
if errorlevel 1 (
    echo.
    echo [ERROR] NumPy install failed! Check your internet connection.
    pause
    exit /b 1
)
echo.

echo [4/5] Installing SciPy and noisereduce (compatible with NumPy 1.x)...
pip install "scipy>=1.11,<1.13" "noisereduce>=3.0.0"
if errorlevel 1 (
    echo.
    echo [ERROR] SciPy/noisereduce install failed! Check your internet connection.
    pause
    exit /b 1
)
echo.

echo [5/5] Verifying dependencies...
python -c "import numpy; print('  NumPy:', numpy.__version__); import scipy; print('  SciPy:', scipy.__version__); import noisereduce as nr; print('  noisereduce:', getattr(nr, '__version__', '?')); print(); print('  All dependencies imported successfully! noisereduce is ready.')"
if errorlevel 1 (
    echo.
    echo [ERROR] Verification failed! Please screenshot the error above and send to developer.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Done! You can now run main.py
echo   The program will auto-detect noisereduce and use it
echo ============================================================
echo.
pause
