@echo off
chcp 65001 >nul
title VRChat翻译工具 - 卸载

echo ========================================
echo   VRChat 实时翻译悬浮字幕 - 卸载程序
echo ========================================
echo.

echo [1/4] 正在停止程序...
taskkill /f /im VRC_Translate.exe 2>nul
taskkill /f /im python.exe 2>nul
timeout /t 1 /nobreak >nul

echo [2/4] 正在删除配置和模型...
if exist "%APPDATA%\vrc_trans" (
    rmdir /s /q "%APPDATA%\vrc_trans"
    echo   已删除 %APPDATA%\vrc_trans
) else (
    echo   配置目录不存在，跳过
)

echo [3/4] 正在删除程序文件...
cd /d "%~dp0"
if exist "VRC_Translate.exe" (
    echo   请手动删除本文件夹中的所有文件
) else (
    echo   源码模式运行，无需删除程序文件
)

echo [4/4] 卸载完成！
echo.
echo ========================================
echo   感谢使用！
echo   配置和模型已全部删除。
echo   如不再需要，请手动删除本文件夹。
echo ========================================
echo.
pause
