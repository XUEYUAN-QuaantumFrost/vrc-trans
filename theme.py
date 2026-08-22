"""
主题管理模块
- 支持深色/浅色/跟随系统
- 默认深色
"""
import os
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings

# 深色主题 QSS
DARK_THEME = """
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: "微软雅黑", "Segoe UI", Arial;
}
QMainWindow, QDialog {
    background-color: #2b2b2b;
}
QLabel {
    background-color: transparent;
    color: #e0e0e0;
}
QPushButton {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 16px;
}
QPushButton:hover {
    background-color: #4c4c4c;
    border-color: #666666;
}
QPushButton:pressed {
    background-color: #2c2c2c;
}
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px;
    selection-background-color: #094771;
}
QComboBox {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px 28px 4px 8px;
    min-height: 20px;
}
QComboBox:hover {
    border-color: #0078d4;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border-left: 1px solid #555555;
    border-top-right-radius: 2px;
    border-bottom-right-radius: 2px;
    background-color: #4a4a4a;
}
QComboBox::drop-down:hover {
    background-color: #5a5a5a;
}
QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}
QComboBox QAbstractItemView {
    background-color: #2b2b2b;
    color: #e0e0e0;
    border: 1px solid #555555;
    selection-background-color: #094771;
}
QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    border-radius: 3px;
    background-color: #3c3c3c;
}
QCheckBox::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
    /* 对号用白色，确保在蓝色背景上可见 */
    color: white;
}
QRadioButton {
    color: #e0e0e0;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    border-radius: 8px;
    background-color: #3c3c3c;
}
QRadioButton::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}
QSpinBox, QDoubleSpinBox {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 3px;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #3c3c3c;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -5px 0;
    background: #0078d4;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #0078d4;
    border-radius: 3px;
}
QTabWidget::pane {
    border: 1px solid #555555;
    background-color: #2b2b2b;
}
QTabBar::tab {
    background-color: #3c3c3c;
    color: #e0e0e0;
    padding: 8px 16px;
    border: 1px solid #555555;
    border-bottom: none;
}
QTabBar::tab:selected {
    background-color: #2b2b2b;
    border-bottom: 2px solid #0078d4;
}
QTabBar::tab:hover:!selected {
    background-color: #4c4c4c;
}
QGroupBox {
    border: 1px solid #555555;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 8px;
    color: #e0e0e0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 10px;
}
QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #666666;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QMenu {
    background-color: #2b2b2b;
    color: #e0e0e0;
    border: 1px solid #555555;
}
QMenu::item {
    padding: 6px 24px;
}
QMenu::item:selected {
    background-color: #094771;
}
QProgressBar {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 3px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 2px;
}
QToolTip {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #555555;
    padding: 4px;
}
/* 字幕窗口保持透明，不被主题覆盖 */
FloatingSubtitle, StrokeLabel {
    background-color: transparent;
}
/* 历史记录窗口保持透明 */
HistoryWindow {
    background-color: transparent;
}
"""

# 浅色主题 QSS（跟随系统时用）
LIGHT_THEME = """
QWidget {
    font-family: "微软雅黑", "Segoe UI", Arial;
}
"""


def is_system_dark() -> bool:
    """检测系统是否为深色模式（Windows）"""
    if sys.platform != "win32":
        return False
    try:
        settings = QSettings(
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
            QSettings.NativeFormat
        )
        return settings.value("AppsUseLightTheme", 1) == 0
    except Exception:
        return False


def apply_theme(app: QApplication, theme: str = "dark"):
    """
    应用主题
    theme: "dark" / "light" / "system"
    """
    if theme == "system":
        theme = "dark" if is_system_dark() else "light"

    if theme == "dark":
        app.setStyleSheet(DARK_THEME)
    else:
        app.setStyleSheet(LIGHT_THEME)
