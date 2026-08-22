"""
Windows 深色标题栏支持
调用 Windows API 让原生标题栏跟随深色模式
"""
import sys


def set_dark_title_bar(window):
    """设置窗口标题栏为深色（Windows 10 1809+）"""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        # 获取窗口句柄
        hwnd = int(window.winId())
        if not hwnd:
            return

        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 10 1809+)
        # DWMWA_MICA_EFFECT = 1029 (Windows 11，可选)
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = wintypes.BOOL(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception:
        pass  # 非 Windows 或 API 不可用时静默失败


def apply_dark_to_all_windows():
    """给所有已创建的顶层窗口设置深色标题栏"""
    if sys.platform != "win32":
        return
    try:
        from PyQt5.QtWidgets import QApplication
        for w in QApplication.topLevelWidgets():
            if w.isVisible():
                set_dark_title_bar(w)
    except Exception:
        pass
