"""
关于窗口
- 软件版本信息
- 依赖库版本（方便排查问题）
- 联系开发者
"""
import os
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QTabWidget, QWidget, QFormLayout, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QDesktopServices
from PyQt5.QtCore import QUrl

APP_VERSION = "2.1.0"
APP_NAME = "VRChat 实时翻译悬浮字幕"

# 开发者联系信息（可自行修改）
DEVELOPER_INFO = {
    "name": "开发者",
    "email": "your_email@example.com",
    "github": "",
    "bilibili": "",
    "qq": "",
    "discord": "",
}


def get_library_versions() -> dict:
    """获取所有依赖库的版本号"""
    versions = {}

    # Python 版本
    versions["Python"] = sys.version.split()[0]

    # 当前模型信息
    try:
        from config import Config
        cfg = Config()
        model_name = cfg.get("whisper_model", "small")
        device = cfg.get("whisper_device", "cpu")
        compute_type = cfg.get("compute_type", "int8")
        versions["当前模型"] = f"{model_name} ({device}/{compute_type})"
    except Exception:
        versions["当前模型"] = "未知"

    # 尝试导入各个库并获取版本
    libs = [
        ("PyQt5", "PyQt5.QtCore", "PYQT_VERSION_STR"),
        ("faster-whisper", "faster_whisper", "__version__"),
        ("ctranslate2", "ctranslate2", "__version__"),
        ("numpy", "numpy", "__version__"),
        ("webrtcvad", "webrtcvad", "__version__"),
        ("requests", "requests", "__version__"),
        ("sounddevice", "sounddevice", "__version__"),
        ("edge-tts", "edge_tts", "__version__"),
    ]

    for name, module_path, attr in libs:
        try:
            mod = __import__(module_path, fromlist=[attr])
            versions[name] = getattr(mod, attr, "未知")
        except Exception:
            versions[name] = "未安装"

    # pyttsx3
    try:
        import pyttsx3
        versions["pyttsx3"] = getattr(pyttsx3, "__version__", "已安装")
    except Exception:
        versions["pyttsx3"] = "未安装"

    # 操作系统
    versions["操作系统"] = f"{os.name} / {sys.platform}"

    return versions


class AboutDialog(QDialog):
    """关于窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setMinimumSize(520, 480)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel(APP_NAME)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        version = QLabel(f"版本 v{APP_VERSION}")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: gray;")
        layout.addWidget(version)

        layout.addSpacing(10)

        # Tab
        tabs = QTabWidget()
        tabs.addTab(self._version_tab(), "版本信息")
        tabs.addTab(self._contact_tab(), "联系开发者")
        layout.addWidget(tabs)

        # 关闭按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _version_tab(self) -> QWidget:
        """版本信息 Tab"""
        w = QWidget()
        layout = QVBoxLayout(w)

        hint = QLabel("以下是所有依赖库的版本，遇到问题时可将此页截图发给开发者排查。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(hint)

        versions = get_library_versions()
        form = QFormLayout()
        for name, ver in versions.items():
            label = QLabel(name)
            value = QLineEdit(ver)
            value.setReadOnly(True)
            value.setStyleSheet("background: #f5f5f5; border: 1px solid #ddd; padding: 2px;")
            form.addRow(label, value)
        layout.addLayout(form)

        return w

    def _contact_tab(self) -> QWidget:
        """联系开发者 Tab"""
        w = QWidget()
        layout = QVBoxLayout(w)

        hint = QLabel("遇到问题或有建议，欢迎通过以下方式联系：")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        form = QFormLayout()

        # 邮箱
        if DEVELOPER_INFO.get("email"):
            email_label = QLabel(f'<a href="mailto:{DEVELOPER_INFO["email"]}">{DEVELOPER_INFO["email"]}</a>')
            email_label.setOpenExternalLinks(True)
            form.addRow("邮箱：", email_label)

        # GitHub
        if DEVELOPER_INFO.get("github"):
            gh_label = QLabel(f'<a href="{DEVELOPER_INFO["github"]}">{DEVELOPER_INFO["github"]}</a>')
            gh_label.setOpenExternalLinks(True)
            form.addRow("GitHub：", gh_label)

        # B站
        if DEVELOPER_INFO.get("bilibili"):
            form.addRow("哔哩哔哩：", QLabel(DEVELOPER_INFO["bilibili"]))

        # QQ
        if DEVELOPER_INFO.get("qq"):
            form.addRow("QQ：", QLabel(DEVELOPER_INFO["qq"]))

        # Discord
        if DEVELOPER_INFO.get("discord"):
            form.addRow("Discord：", QLabel(DEVELOPER_INFO["discord"]))

        # 如果都没填，显示提示
        if not any(DEVELOPER_INFO.values()):
            empty = QLabel("（开发者尚未填写联系方式）")
            empty.setStyleSheet("color: gray;")
            form.addRow(empty)

        layout.addLayout(form)
        layout.addStretch()

        return w
