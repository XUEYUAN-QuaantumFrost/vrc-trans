# -*- coding: utf-8 -*-
"""
VRC Translate 融合版主界面
- 整合托盘快捷功能 + 常用设置
- 翻译控制、字幕外观、语音识别、OSC、TTS 全在一个窗口
- 滚动区域，分组组织
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QListWidget, QListWidgetItem, QScrollArea,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox, QLineEdit,
    QCheckBox, QSlider, QColorDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QBrush, QPen


# ============================================================
#  状态指示灯
# ============================================================
class StatusIndicator(QWidget):
    """状态指示灯（绿=运行中，灰=已停止，黄=加载中）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor("#666666")
        self.setFixedSize(14, 14)

    def set_status(self, status):
        colors = {
            "running": QColor("#4CAF50"),
            "stopped": QColor("#666666"),
            "loading": QColor("#FFC107"),
        }
        self._color = colors.get(status, QColor("#666666"))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        glow = self._color.lighter(150)
        glow.setAlpha(60)
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(-2, -2, 18, 18)
        painter.setBrush(QBrush(self._color))
        painter.drawEllipse(1, 1, 12, 12)


# ============================================================
#  图标功能按钮
# ============================================================
class IconButton(QPushButton):
    """图标+文字的功能按钮"""
    def __init__(self, icon_text, label, parent=None):
        super().__init__(parent)
        self._icon_text = icon_text
        self._label = label
        self.setFixedSize(72, 64)
        self.setCursor(Qt.PointingHandCursor)
        self._hover = False
        self.setStyleSheet(self._style(False))

    def enterEvent(self, event):
        self._hover = True
        self.setStyleSheet(self._style(True))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.setStyleSheet(self._style(False))
        super().leaveEvent(event)

    def _style(self, hover):
        bg = "rgba(255,255,255,0.08)" if hover else "rgba(255,255,255,0.03)"
        border = "rgba(255,255,255,0.15)" if hover else "rgba(255,255,255,0.06)"
        return f"""
            QPushButton {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 10px;
                color: #E0E0E0;
                font-size: 10px;
                padding: 4px;
                text-align: center;
            }}
        """

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        icon_font = QFont()
        icon_font.setPointSize(18)
        painter.setFont(icon_font)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(self.rect().adjusted(0, -4, 0, 0), Qt.AlignHCenter | Qt.AlignTop, self._icon_text)
        label_font = QFont()
        label_font.setPointSize(8)
        painter.setFont(label_font)
        painter.setPen(QColor("#AAAAAA"))
        painter.drawText(self.rect().adjusted(0, 38, 0, -4), Qt.AlignHCenter | Qt.AlignBottom, self._label)


# ============================================================
#  iOS 风格开关
# ============================================================
class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self._checked = False
        self._label = label
        self.setFixedHeight(32)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label_widget = QLabel(label)
        self.label_widget.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        layout.addWidget(self.label_widget)
        layout.addStretch()
        self.switch_widget = _SwitchWidget()
        self.switch_widget.toggled.connect(self._on_toggled)
        layout.addWidget(self.switch_widget)

    def _on_toggled(self, checked):
        self._checked = checked
        self.toggled.emit(checked)

    def setChecked(self, checked):
        self._checked = checked
        self.switch_widget.setChecked(checked)

    def isChecked(self):
        return self._checked


class _SwitchWidget(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._hover = False
        self.setFixedSize(40, 22)
        self.setCursor(Qt.PointingHandCursor)

    def setChecked(self, checked):
        self._checked = checked
        self.update()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self._checked:
            track_color = QColor("#4CAF50")
        else:
            track_color = QColor("#555555") if not self._hover else QColor("#666666")
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 1, 40, 20, 10, 10)
        x = 20 if self._checked else 2
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(x, 3, 16, 16)


# ============================================================
#  颜色选择按钮
# ============================================================
class ColorButton(QPushButton):
    color_changed = pyqtSignal(str)

    def __init__(self, color_str="#FFFFFF", parent=None):
        super().__init__(parent)
        self._color = QColor(color_str)
        self.setFixedHeight(26)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._choose)
        self._update_style()

    def _update_style(self):
        c = self._color.name()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {c};
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 6px;
                color: {'#000000' if self._color.lightness() > 128 else '#FFFFFF'};
                font-size: 11px;
                padding: 2px 8px;
            }}
            QPushButton:hover {{ border: 1px solid rgba(255,255,255,0.4); }}
        """)
        self.setText(c)

    def color(self):
        return self._color.name()

    def set_color(self, color_str):
        self._color = QColor(color_str)
        self._update_style()

    def _choose(self):
        color = QColorDialog.getColor(self._color, self, "选择颜色")
        if color.isValid():
            self._color = color
            self._update_style()
            self.color_changed.emit(color.name())


# ============================================================
#  主窗口
# ============================================================
class MainWindow(QWidget):
    """VRC Translate 融合版主界面"""
    # 原有信号（保持兼容）
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    history_clicked = pyqtSignal()
    manual_input_clicked = pyqtSignal()
    ai_chat_clicked = pyqtSignal()
    help_clicked = pyqtSignal()
    about_clicked = pyqtSignal()
    quit_clicked = pyqtSignal()
    simul_toggled = pyqtSignal(bool)
    tts_toggled = pyqtSignal(bool)
    subtitle_toggled = pyqtSignal(bool)
    target_lang_changed = pyqtSignal(str)
    translate_engine_changed = pyqtSignal(str)
    # 新增：通用配置变更信号
    config_changed = pyqtSignal()
    # 新增：仅外观变更（不触发模块重载）
    appearance_changed = pyqtSignal()
    # 新增：锁定切换
    lock_toggled = pyqtSignal(bool)
    # 新增：VB-CABLE 安装请求
    install_vbcable_clicked = pyqtSignal()

    # 目标语言列表
    TARGET_LANGS = [
        "中文", "日语", "韩语", "英语", "法语", "德语",
        "俄语", "西班牙语", "阿拉伯语", "蒙古语", "葡萄牙语", "意大利语",
    ]
    # 翻译引擎
    ENGINES = [
        ("AI 翻译（DeepSeek 等）", "deepseek"),
        ("谷歌翻译（免费）", "google"),
        ("百度翻译", "baidu"),
    ]
    # 识别引擎
    RECOGNIZE_ENGINES = [
        ("Sherpa-onnx（推荐）", "sherpa"),
        ("faster-whisper", "faster"),
    ]
    # 音源
    SOURCES = [
        ("电脑声音（VRChat 他人说话）", "computer"),
        ("麦克风（你说的话）", "mic"),
    ]
    # TTS 引擎
    TTS_ENGINES = [
        ("pyttsx3（系统语音）", "pyttsx3"),
        ("edge-tts（微软语音）", "edge"),
        ("火山引擎（豆包）", "volcengine"),
    ]
    # 字幕显示模式
    SUBTITLE_MODES = [
        ("同时显示原文和译文", "both"),
        ("仅显示译文", "translate_only"),
        ("仅显示原文（省 token）", "original_only"),
    ]

    def __init__(self, config, history_window=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.history_window = history_window
        self._running = False
        self._loading = False  # 防止初始化时触发信号
        self._init_ui()
        self._loading = True
        self._load_config()
        self._loading = False
        # 连接历史记录变化信号
        if self.history_window is not None:
            try:
                self.history_window.history_changed.connect(self._refresh_history)
            except Exception:
                pass
            self._refresh_history()

    # ----------------------------------------------------------
    #  UI 构建
    # ----------------------------------------------------------
    def _init_ui(self):
        self.setWindowTitle("VRC Translate")
        self.setFixedSize(560, 880)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E2E;
                color: #E0E0E0;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            }
            QComboBox {
                background-color: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                padding: 4px 8px;
                color: #E0E0E0;
                font-size: 11px;
                min-height: 18px;
            }
            QComboBox:hover { border: 1px solid rgba(255,255,255,0.2); }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox QAbstractItemView {
                background-color: #2A2A3C;
                border: 1px solid rgba(255,255,255,0.15);
                selection-background-color: rgba(76,175,80,0.4);
                outline: none;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                padding: 2px 6px;
                color: #E0E0E0;
                font-size: 11px;
            }
            QLineEdit {
                background-color: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                padding: 4px 8px;
                color: #E0E0E0;
                font-size: 11px;
            }
            QLineEdit:focus { border: 1px solid rgba(76,175,80,0.5); }
            QGroupBox {
                background-color: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 8px;
                font-size: 12px;
                font-weight: bold;
                color: #AAAAAA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }
            QListWidget {
                background-color: rgba(0,0,0,0.15);
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 8px;
                outline: none;
                font-size: 11px;
            }
            QListWidget::item {
                border-bottom: 1px solid rgba(255,255,255,0.04);
                padding: 3px 6px;
            }
            QListWidget::item:hover { background-color: rgba(255,255,255,0.05); }
            QScrollBar:vertical { background: transparent; width: 6px; margin: 4px 0; }
            QScrollBar::handle:vertical { background: rgba(255,255,255,0.15); border-radius: 3px; min-height: 30px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QCheckBox { color: #CCCCCC; font-size: 11px; spacing: 6px; }
            QLabel { color: #AAAAAA; font-size: 11px; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 10)
        root.setSpacing(8)

        # ===== 顶部标题栏 =====
        top = QHBoxLayout()
        title = QLabel("VRC Translate")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF;")
        top.addWidget(title)
        top.addStretch()
        self.status_indicator = StatusIndicator()
        top.addWidget(self.status_indicator)
        self.status_label = QLabel("未运行")
        self.status_label.setStyleSheet("font-size: 11px; color: #888888;")
        top.addWidget(self.status_label)
        root.addLayout(top)

        # ===== 开始/停止按钮 =====
        self.start_btn = QPushButton("▶  开始翻译")
        self.start_btn.setFixedHeight(48)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setStyleSheet(self._start_btn_style(False))
        self.start_btn.clicked.connect(self._on_start_stop)
        root.addWidget(self.start_btn)

        # ===== 快捷功能按钮（移到上方，一打开就能看到）=====
        root.addWidget(self._build_function_group())

        # ===== 滚动区域 =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFocusPolicy(Qt.NoFocus)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(2, 4, 2, 4)
        scroll_layout.setSpacing(8)

        # --- 翻译设置组 ---
        scroll_layout.addWidget(self._build_translate_group())
        # --- 字幕外观组 ---
        scroll_layout.addWidget(self._build_appearance_group())
        # --- 语音识别组 ---
        scroll_layout.addWidget(self._build_speech_group())
        # --- OSC 设置组 ---
        scroll_layout.addWidget(self._build_osc_group())
        # --- TTS 设置组 ---
        scroll_layout.addWidget(self._build_tts_group())
        # --- 功能开关组 ---
        scroll_layout.addWidget(self._build_toggle_group())

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        root.addWidget(scroll, 1)

        # ===== 最近翻译记录 =====
        history_header = QHBoxLayout()
        history_title = QLabel("最近翻译")
        history_title.setStyleSheet("font-size: 11px; color: #888888;")
        history_header.addWidget(history_title)
        history_header.addStretch()
        self.history_count_label = QLabel("")
        self.history_count_label.setStyleSheet("font-size: 10px; color: #555555;")
        history_header.addWidget(self.history_count_label)
        self.history_clear_btn = QPushButton("清空")
        self.history_clear_btn.setFixedHeight(20)
        self.history_clear_btn.setCursor(Qt.PointingHandCursor)
        self.history_clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,80,80,0.12); color: #CC8888; border: none;
                border-radius: 5px; padding: 0 8px; font-size: 10px;
            }
            QPushButton:hover { background: rgba(255,80,80,0.25); color: #FFAAAA; }
        """)
        self.history_clear_btn.clicked.connect(self._on_clear_history)
        history_header.addWidget(self.history_clear_btn)
        root.addLayout(history_header)

        self.history_list = QListWidget()
        self.history_list.setFixedHeight(100)
        self.history_list.setSelectionMode(QListWidget.NoSelection)
        self.history_list.setFocusPolicy(Qt.NoFocus)
        self.history_list.itemClicked.connect(lambda: self.history_clicked.emit())
        self.history_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        root.addWidget(self.history_list)

        # ===== 底部提示 =====
        hint = QLabel("关闭窗口最小化到托盘 · 双击托盘图标切换字幕")
        hint.setStyleSheet("font-size: 9px; color: #444444;")
        hint.setAlignment(Qt.AlignCenter)
        root.addWidget(hint)

    # ----------------------------------------------------------
    #  分组构建
    # ----------------------------------------------------------
    def _build_translate_group(self):
        group = QGroupBox("翻译设置")
        form = QFormLayout(group)
        form.setContentsMargins(14, 18, 14, 10)
        form.setSpacing(6)

        # 翻译引擎
        self.engine_combo = QComboBox()
        for name, key in self.ENGINES:
            self.engine_combo.addItem(name, key)
        self.engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        form.addRow("翻译引擎：", self.engine_combo)

        # 目标语言
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(self.TARGET_LANGS)
        self.lang_combo.currentTextChanged.connect(self._on_lang_changed)
        form.addRow("目标语言：", self.lang_combo)

        # AI API Key（仅 AI 引擎时显示）
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("sk- ...（AI 翻译 API Key）")
        self.api_key_edit.editingFinished.connect(self._on_api_key_changed)
        form.addRow("API Key：", self.api_key_edit)

        # 自定义提示词
        self.prompt_edit = QLineEdit()
        self.prompt_edit.setPlaceholderText("自定义翻译提示词（可选）")
        self.prompt_edit.editingFinished.connect(self._on_prompt_changed)
        form.addRow("提示词：", self.prompt_edit)

        return group

    def _build_appearance_group(self):
        group = QGroupBox("字幕外观")
        form = QFormLayout(group)
        form.setContentsMargins(14, 18, 14, 10)
        form.setSpacing(6)

        # 字体大小
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 48)
        self.font_size_spin.setSuffix(" px")
        self.font_size_spin.valueChanged.connect(self._on_font_size_changed)
        form.addRow("字体大小：", self.font_size_spin)

        # 原文颜色
        self.original_color_btn = ColorButton("#87CEEB")
        self.original_color_btn.color_changed.connect(self._on_original_color_changed)
        form.addRow("原文颜色：", self.original_color_btn)

        # 译文颜色
        self.translate_color_btn = ColorButton("#FFB6C1")
        self.translate_color_btn.color_changed.connect(self._on_translate_color_changed)
        form.addRow("译文颜色：", self.translate_color_btn)

        # 背景颜色
        self.bg_color_btn = ColorButton("#000000")
        self.bg_color_btn.color_changed.connect(self._on_bg_color_changed)
        form.addRow("背景颜色：", self.bg_color_btn)

        # 背景透明度
        opacity_row = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_label = QLabel("40%")
        self.opacity_label.setFixedWidth(36)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_row.addWidget(self.opacity_slider, 1)
        opacity_row.addWidget(self.opacity_label)
        opacity_widget = QWidget()
        opacity_widget.setLayout(opacity_row)
        opacity_widget.setStyleSheet("background: transparent;")
        form.addRow("背景透明度：", opacity_widget)

        # 显示模式
        self.subtitle_mode_combo = QComboBox()
        for name, key in self.SUBTITLE_MODES:
            self.subtitle_mode_combo.addItem(name, key)
        self.subtitle_mode_combo.currentIndexChanged.connect(self._on_subtitle_mode_changed)
        form.addRow("显示模式：", self.subtitle_mode_combo)

        # 锁定位置
        self.lock_switch = ToggleSwitch("锁定字幕位置（鼠标穿透）")
        self.lock_switch.toggled.connect(self._on_lock_toggled)
        form.addRow(self.lock_switch)

        return group

    def _build_speech_group(self):
        group = QGroupBox("语音识别")
        form = QFormLayout(group)
        form.setContentsMargins(14, 18, 14, 10)
        form.setSpacing(6)

        # 双路模式开关
        self.dual_mode_cb = QCheckBox("双向模式（同时识别麦克风 + 电脑声音）")
        self.dual_mode_cb.stateChanged.connect(self._on_dual_mode_changed)
        form.addRow(self.dual_mode_cb)

        # 音源（单路模式）
        self.source_combo = QComboBox()
        for name, key in self.SOURCES:
            self.source_combo.addItem(name, key)
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        form.addRow("音源（单路）：", self.source_combo)

        # 识别引擎
        self.recognize_engine_combo = QComboBox()
        for name, key in self.RECOGNIZE_ENGINES:
            self.recognize_engine_combo.addItem(name, key)
        self.recognize_engine_combo.currentIndexChanged.connect(self._on_recognize_engine_changed)
        form.addRow("识别引擎：", self.recognize_engine_combo)

        # 麦克风设备
        mic_row = QHBoxLayout()
        self.mic_device_combo = QComboBox()
        self.mic_device_combo.setMinimumHeight(22)
        self.mic_device_combo.currentIndexChanged.connect(self._on_mic_device_changed)
        mic_row.addWidget(self.mic_device_combo, 1)
        self.refresh_mic_btn = QPushButton("刷新")
        self.refresh_mic_btn.setFixedWidth(50)
        self.refresh_mic_btn.setFixedHeight(24)
        self.refresh_mic_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_mic_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
                         border-radius: 5px; color: #AAAAAA; font-size: 10px; }
            QPushButton:hover { background: rgba(255,255,255,0.12); }
        """)
        self.refresh_mic_btn.clicked.connect(self._refresh_mic_devices)
        mic_row.addWidget(self.refresh_mic_btn)
        mic_widget = QWidget()
        mic_widget.setLayout(mic_row)
        mic_widget.setStyleSheet("background: transparent;")
        form.addRow("麦克风设备：", mic_widget)

        # 电脑声音设备
        comp_row = QHBoxLayout()
        self.comp_device_combo = QComboBox()
        self.comp_device_combo.setMinimumHeight(22)
        self.comp_device_combo.currentIndexChanged.connect(self._on_comp_device_changed)
        comp_row.addWidget(self.comp_device_combo, 1)
        self.refresh_comp_btn = QPushButton("刷新")
        self.refresh_comp_btn.setFixedWidth(50)
        self.refresh_comp_btn.setFixedHeight(24)
        self.refresh_comp_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_comp_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
                         border-radius: 5px; color: #AAAAAA; font-size: 10px; }
            QPushButton:hover { background: rgba(255,255,255,0.12); }
        """)
        self.refresh_comp_btn.clicked.connect(self._refresh_comp_devices)
        comp_row.addWidget(self.refresh_comp_btn)
        comp_widget = QWidget()
        comp_widget.setLayout(comp_row)
        comp_widget.setStyleSheet("background: transparent;")
        form.addRow("电脑声音设备：", comp_widget)

        return group

    def _build_osc_group(self):
        group = QGroupBox("OSC 发送（VRChat 字幕）")
        form = QFormLayout(group)
        form.setContentsMargins(14, 18, 14, 10)
        form.setSpacing(6)

        # OSC 开关
        self.osc_enabled_cb = QCheckBox("启用 OSC 发送到 VRChat")
        self.osc_enabled_cb.stateChanged.connect(self._on_osc_enabled_changed)
        form.addRow(self.osc_enabled_cb)

        # OSC IP
        self.osc_ip_edit = QLineEdit()
        self.osc_ip_edit.setPlaceholderText("127.0.0.1")
        self.osc_ip_edit.editingFinished.connect(self._on_osc_ip_changed)
        form.addRow("OSC IP：", self.osc_ip_edit)

        # OSC 端口
        self.osc_port_spin = QSpinBox()
        self.osc_port_spin.setRange(1, 65535)
        self.osc_port_spin.valueChanged.connect(self._on_osc_port_changed)
        form.addRow("OSC 端口：", self.osc_port_spin)

        # 双语字幕
        self.osc_bilingual_cb = QCheckBox("发送双语字幕（原文 + 译文）")
        self.osc_bilingual_cb.stateChanged.connect(self._on_osc_bilingual_changed)
        form.addRow(self.osc_bilingual_cb)

        return group

    def _build_tts_group(self):
        group = QGroupBox("TTS 语音朗读")
        form = QFormLayout(group)
        form.setContentsMargins(14, 18, 14, 10)
        form.setSpacing(6)

        # TTS 开关
        self.tts_enabled_cb = QCheckBox("启用 TTS 语音朗读")
        self.tts_enabled_cb.stateChanged.connect(self._on_tts_enabled_changed)
        form.addRow(self.tts_enabled_cb)

        # TTS 引擎
        self.tts_engine_combo = QComboBox()
        for name, key in self.TTS_ENGINES:
            self.tts_engine_combo.addItem(name, key)
        self.tts_engine_combo.currentIndexChanged.connect(self._on_tts_engine_changed)
        form.addRow("TTS 引擎：", self.tts_engine_combo)

        # 朗读速率
        self.tts_rate_spin = QSpinBox()
        self.tts_rate_spin.setRange(50, 400)
        self.tts_rate_spin.setSuffix(" wpm")
        self.tts_rate_spin.valueChanged.connect(self._on_tts_rate_changed)
        form.addRow("朗读速率：", self.tts_rate_spin)

        # 音量
        vol_row = QHBoxLayout()
        self.tts_volume_slider = QSlider(Qt.Horizontal)
        self.tts_volume_slider.setRange(0, 100)
        self.tts_volume_label = QLabel("100%")
        self.tts_volume_label.setFixedWidth(36)
        self.tts_volume_slider.valueChanged.connect(self._on_tts_volume_changed)
        vol_row.addWidget(self.tts_volume_slider, 1)
        vol_row.addWidget(self.tts_volume_label)
        vol_widget = QWidget()
        vol_widget.setLayout(vol_row)
        vol_widget.setStyleSheet("background: transparent;")
        form.addRow("音量：", vol_widget)

        return group

    def _build_toggle_group(self):
        group = QGroupBox("功能开关")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(14, 18, 14, 8)
        layout.setSpacing(2)

        self.toggle_subtitle = ToggleSwitch("显示悬浮字幕")
        self.toggle_subtitle.toggled.connect(self._on_subtitle_toggled)
        layout.addWidget(self.toggle_subtitle)

        self.toggle_simul = ToggleSwitch("同声传译")
        self.toggle_simul.toggled.connect(self._on_simul_toggled)
        layout.addWidget(self.toggle_simul)

        # VB-CABLE 安装按钮
        self.vbcable_btn = QPushButton("🔊 安装 VB-CABLE 虚拟音频线")
        self.vbcable_btn.setFixedHeight(30)
        self.vbcable_btn.setCursor(Qt.PointingHandCursor)
        self.vbcable_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(76,175,80,0.15);
                border: 1px solid rgba(76,175,80,0.3);
                border-radius: 8px;
                color: #81C784;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(76,175,80,0.25);
                border: 1px solid rgba(76,175,80,0.5);
            }
        """)
        self.vbcable_btn.clicked.connect(self.install_vbcable_clicked.emit)
        layout.addWidget(self.vbcable_btn)

        return group

    def _build_function_group(self):
        group = QGroupBox("快捷功能")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 18, 10, 10)
        layout.setSpacing(6)

        btn_row1 = QHBoxLayout()
        btn_row1.setSpacing(6)
        self.btn_settings = IconButton("⚙", "设置")
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        self.btn_history = IconButton("📋", "历史")
        self.btn_history.clicked.connect(self.history_clicked.emit)
        self.btn_manual = IconButton("⌨", "手动输入")
        self.btn_manual.clicked.connect(self.manual_input_clicked.emit)
        self.btn_ai_chat = IconButton("💬", "AI 代聊")
        self.btn_ai_chat.clicked.connect(self.ai_chat_clicked.emit)
        self.btn_help = IconButton("？", "帮助")
        self.btn_help.clicked.connect(self.help_clicked.emit)
        for b in (self.btn_settings, self.btn_history, self.btn_manual, self.btn_ai_chat, self.btn_help):
            btn_row1.addWidget(b)
        layout.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(6)
        self.btn_about = IconButton("ℹ", "关于")
        self.btn_about.clicked.connect(self.about_clicked.emit)
        self.btn_quit = IconButton("⏻", "退出")
        self.btn_quit.clicked.connect(self.quit_clicked.emit)
        btn_row2.addWidget(self.btn_about)
        btn_row2.addStretch()
        btn_row2.addWidget(self.btn_quit)
        layout.addLayout(btn_row2)

        return group

    # ----------------------------------------------------------
    #  样式辅助
    # ----------------------------------------------------------
    def _start_btn_style(self, running):
        if running:
            return """
                QPushButton {
                    background-color: #E53935; color: white;
                    font-size: 16px; font-weight: bold;
                    border: none; border-radius: 12px;
                }
                QPushButton:hover { background-color: #EF5350; }
                QPushButton:pressed { background-color: #C62828; }
            """
        return """
            QPushButton {
                background-color: #4CAF50; color: white;
                font-size: 16px; font-weight: bold;
                border: none; border-radius: 12px;
            }
            QPushButton:hover { background-color: #5CBF60; }
            QPushButton:pressed { background-color: #3D8B40; }
        """

    # ----------------------------------------------------------
    #  配置加载
    # ----------------------------------------------------------
    def _load_config(self):
        c = self.config

        # 翻译设置
        engine = c.get("translate_engine", "deepseek")
        for i in range(self.engine_combo.count()):
            if self.engine_combo.itemData(i) == engine:
                self.engine_combo.setCurrentIndex(i)
                break
        lang = c.get("target_lang", "中文")
        idx = self.lang_combo.findText(lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.api_key_edit.setText(c.get("ai_api_key", "") or c.get("api_key", ""))
        self.prompt_edit.setText(c.get("custom_prompt", ""))

        # 字幕外观
        self.font_size_spin.setValue(c.get("font_size", 18))
        self.original_color_btn.set_color(c.get("original_color", "#87CEEB"))
        self.translate_color_btn.set_color(c.get("translate_color", "#FFB6C1"))
        self.bg_color_btn.set_color(c.get("bg_color", "#000000"))
        self.opacity_slider.setValue(int(c.get("bg_opacity", 0.4) * 100))
        self.opacity_label.setText(f"{int(c.get('bg_opacity', 0.4) * 100)}%")
        mode = c.get("subtitle_display_mode", "both")
        for i in range(self.subtitle_mode_combo.count()):
            if self.subtitle_mode_combo.itemData(i) == mode:
                self.subtitle_mode_combo.setCurrentIndex(i)
                break
        self.lock_switch.setChecked(c.get("locked", False))

        # 语音识别
        self.dual_mode_cb.setChecked(c.get("dual_mode", False))
        source = c.get("record_source", "computer")
        for i in range(self.source_combo.count()):
            if self.source_combo.itemData(i) == source:
                self.source_combo.setCurrentIndex(i)
                break
        rec_engine = c.get("whisper_engine", "sherpa")
        for i in range(self.recognize_engine_combo.count()):
            if self.recognize_engine_combo.itemData(i) == rec_engine:
                self.recognize_engine_combo.setCurrentIndex(i)
                break
        self._refresh_mic_devices()
        self._refresh_comp_devices()

        # OSC
        self.osc_enabled_cb.setChecked(c.get("enable_osc", True))
        self.osc_ip_edit.setText(c.get("osc_ip", "127.0.0.1"))
        self.osc_port_spin.setValue(c.get("osc_port", 9000))
        self.osc_bilingual_cb.setChecked(c.get("enable_osc_bilingual", False))

        # TTS
        self.tts_enabled_cb.setChecked(c.get("tts_enabled", False))
        tts_engine = c.get("tts_engine", "pyttsx3")
        for i in range(self.tts_engine_combo.count()):
            if self.tts_engine_combo.itemData(i) == tts_engine:
                self.tts_engine_combo.setCurrentIndex(i)
                break
        self.tts_rate_spin.setValue(c.get("tts_rate", 200))
        self.tts_volume_slider.setValue(int(c.get("tts_volume", 1.0) * 100))
        self.tts_volume_label.setText(f"{int(c.get('tts_volume', 1.0) * 100)}%")

        # 功能开关
        self.toggle_subtitle.setChecked(c.get("visible", True))
        self.toggle_simul.setChecked(c.get("simultaneous_interpretation_enabled", False))

        # 更新双路模式下的音源控件状态
        self._update_dual_mode_ui()

    def _update_dual_mode_ui(self):
        dual = self.dual_mode_cb.isChecked()
        self.source_combo.setEnabled(not dual)

    # ----------------------------------------------------------
    #  设置变更回调（翻译）
    # ----------------------------------------------------------
    def _on_engine_changed(self, _idx):
        if self._loading:
            return
        engine = self.engine_combo.currentData()
        self.config.set("translate_engine", engine)
        self.translate_engine_changed.emit(engine)
        self.config_changed.emit()

    def _on_lang_changed(self, lang):
        if self._loading:
            return
        self.config.set("target_lang", lang)
        self.target_lang_changed.emit(lang)
        self.config_changed.emit()

    def _on_api_key_changed(self):
        if self._loading:
            return
        self.config.set("ai_api_key", self.api_key_edit.text().strip())
        self.config_changed.emit()

    def _on_prompt_changed(self):
        if self._loading:
            return
        self.config.set("custom_prompt", self.prompt_edit.text().strip())
        self.config_changed.emit()

    # ----------------------------------------------------------
    #  设置变更回调（外观）
    # ----------------------------------------------------------
    def _on_font_size_changed(self, val):
        if self._loading:
            return
        self.config.set("font_size", val)
        self.appearance_changed.emit()

    def _on_original_color_changed(self, color):
        if self._loading:
            return
        self.config.set("original_color", color)
        self.appearance_changed.emit()

    def _on_translate_color_changed(self, color):
        if self._loading:
            return
        self.config.set("translate_color", color)
        self.appearance_changed.emit()

    def _on_bg_color_changed(self, color):
        if self._loading:
            return
        self.config.set("bg_color", color)
        self.appearance_changed.emit()

    def _on_opacity_changed(self, val):
        if self._loading:
            return
        self.opacity_label.setText(f"{val}%")
        self.config.set("bg_opacity", val / 100.0)
        self.appearance_changed.emit()

    def _on_subtitle_mode_changed(self, _idx):
        if self._loading:
            return
        mode = self.subtitle_mode_combo.currentData()
        self.config.set("subtitle_display_mode", mode)
        # 同步设置 show_original / show_translate
        if mode == "both":
            self.config.set("show_original", True)
            self.config.set("show_translate", True)
        elif mode == "original_only":
            self.config.set("show_original", True)
            self.config.set("show_translate", False)
        elif mode == "translate_only":
            self.config.set("show_original", False)
            self.config.set("show_translate", True)
        self.appearance_changed.emit()

    def _on_lock_toggled(self, checked):
        if self._loading:
            return
        self.config.set("locked", checked)
        self.lock_toggled.emit(checked)
        self.appearance_changed.emit()

    # ----------------------------------------------------------
    #  设置变更回调（语音识别）
    # ----------------------------------------------------------
    def _on_dual_mode_changed(self, _state):
        if self._loading:
            return
        self.config.set("dual_mode", self.dual_mode_cb.isChecked())
        self._update_dual_mode_ui()
        self.config_changed.emit()

    def _on_source_changed(self, _idx):
        if self._loading:
            return
        self.config.set("record_source", self.source_combo.currentData())
        self.config_changed.emit()

    def _on_recognize_engine_changed(self, _idx):
        if self._loading:
            return
        self.config.set("whisper_engine", self.recognize_engine_combo.currentData())
        self.config_changed.emit()

    def _refresh_mic_devices(self):
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            self.mic_device_combo.clear()
            self.mic_device_combo.addItem("（系统默认）", -1)
            for i, d in enumerate(devices):
                if d.get("max_input_channels", 0) > 0:
                    name = d.get("name", f"Device {i}")
                    self.mic_device_combo.addItem(f"{i}: {name}", i)
            # 恢复已保存的设备
            saved = self.config.get("device_mic", None)
            if saved is not None:
                for i in range(self.mic_device_combo.count()):
                    if self.mic_device_combo.itemData(i) == saved:
                        self.mic_device_combo.setCurrentIndex(i)
                        break
        except Exception:
            self.mic_device_combo.clear()
            self.mic_device_combo.addItem("（未检测到音频设备）", -1)

    def _on_mic_device_changed(self, _idx):
        if self._loading:
            return
        data = self.mic_device_combo.currentData()
        if data != -1:
            self.config.set("device_mic", data)
            self.config_changed.emit()

    def _refresh_comp_devices(self):
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            self.comp_device_combo.clear()
            self.comp_device_combo.addItem("（系统默认）", -1)
            for i, d in enumerate(devices):
                if d.get("max_input_channels", 0) > 0:
                    name = d.get("name", f"Device {i}")
                    self.comp_device_combo.addItem(f"{i}: {name}", i)
            saved = self.config.get("device_computer", None)
            if saved is not None:
                for i in range(self.comp_device_combo.count()):
                    if self.comp_device_combo.itemData(i) == saved:
                        self.comp_device_combo.setCurrentIndex(i)
                        break
        except Exception:
            self.comp_device_combo.clear()
            self.comp_device_combo.addItem("（未检测到音频设备）", -1)

    def _on_comp_device_changed(self, _idx):
        if self._loading:
            return
        data = self.comp_device_combo.currentData()
        if data != -1:
            self.config.set("device_computer", data)
            self.config_changed.emit()

    # ----------------------------------------------------------
    #  设置变更回调（OSC）
    # ----------------------------------------------------------
    def _on_osc_enabled_changed(self, _state):
        if self._loading:
            return
        self.config.set("enable_osc", self.osc_enabled_cb.isChecked())
        self.config_changed.emit()

    def _on_osc_ip_changed(self):
        if self._loading:
            return
        self.config.set("osc_ip", self.osc_ip_edit.text().strip() or "127.0.0.1")
        self.config_changed.emit()

    def _on_osc_port_changed(self, val):
        if self._loading:
            return
        self.config.set("osc_port", val)
        self.config_changed.emit()

    def _on_osc_bilingual_changed(self, _state):
        if self._loading:
            return
        self.config.set("enable_osc_bilingual", self.osc_bilingual_cb.isChecked())
        self.config_changed.emit()

    # ----------------------------------------------------------
    #  设置变更回调（TTS）
    # ----------------------------------------------------------
    def _on_tts_enabled_changed(self, _state):
        if self._loading:
            return
        enabled = self.tts_enabled_cb.isChecked()
        self.config.set("tts_enabled", enabled)
        self.tts_toggled.emit(enabled)
        self.config_changed.emit()

    def _on_tts_engine_changed(self, _idx):
        if self._loading:
            return
        self.config.set("tts_engine", self.tts_engine_combo.currentData())
        self.config_changed.emit()

    def _on_tts_rate_changed(self, val):
        if self._loading:
            return
        self.config.set("tts_rate", val)
        self.config_changed.emit()

    def _on_tts_volume_changed(self, val):
        if self._loading:
            return
        self.tts_volume_label.setText(f"{val}%")
        self.config.set("tts_volume", val / 100.0)
        self.config_changed.emit()

    # ----------------------------------------------------------
    #  功能开关回调
    # ----------------------------------------------------------
    def _on_subtitle_toggled(self, checked):
        if self._loading:
            return
        self.config.set("visible", checked)
        self.subtitle_toggled.emit(checked)

    def _on_simul_toggled(self, checked):
        if self._loading:
            return
        self.config.set("simultaneous_interpretation_enabled", checked)
        self.simul_toggled.emit(checked)

    # ----------------------------------------------------------
    #  开始/停止
    # ----------------------------------------------------------
    def _on_start_stop(self):
        if self._running:
            self._running = False
            self.start_btn.setText("▶  开始翻译")
            self.start_btn.setStyleSheet(self._start_btn_style(False))
            self.status_indicator.set_status("stopped")
            self.status_label.setText("未运行")
            self.status_label.setStyleSheet("font-size: 11px; color: #888888;")
            self.stop_clicked.emit()
        else:
            self._running = True
            self.start_btn.setText("■  停止翻译")
            self.start_btn.setStyleSheet(self._start_btn_style(True))
            self.status_indicator.set_status("loading")
            self.status_label.setText("启动中…")
            self.status_label.setStyleSheet("font-size: 11px; color: #FFC107;")
            self.start_clicked.emit()
            self.status_indicator.set_status("running")
            self.status_label.setText("运行中")
            self.status_label.setStyleSheet("font-size: 11px; color: #4CAF50;")

    def set_running(self, running):
        if running != self._running:
            self._on_start_stop()

    # ----------------------------------------------------------
    #  内嵌历史记录
    # ----------------------------------------------------------
    def _refresh_history(self):
        self.history_list.clear()
        if self.history_window is None:
            return
        entries = getattr(self.history_window, 'entries', [])
        if not entries:
            item = QListWidgetItem("暂无翻译记录")
            item.setForeground(QColor("#555555"))
            item.setTextAlignment(Qt.AlignCenter)
            self.history_list.addItem(item)
            self.history_count_label.setText("")
            return
        recent = entries[-20:]
        for entry in recent:
            text = self._format_history_entry(entry)
            item = QListWidgetItem(text)
            colors = {"mic": "#87CEEB", "computer": "#FFB6C1",
                      "manual": "#FFD700", "aichat": "#DDA0DD"}
            color = colors.get(getattr(entry, 'source', ''), "#AAAAAA")
            item.setForeground(QColor(color))
            self.history_list.addItem(item)
        self.history_list.scrollToBottom()
        self.history_count_label.setText(f"共 {len(entries)} 条")

    def _format_history_entry(self, entry):
        src_labels = {"mic": "MIC", "computer": "PC", "manual": "输入", "aichat": "AI"}
        src = src_labels.get(getattr(entry, 'source', ''), "?")
        t = getattr(entry, 'time_str', lambda: "")()
        display = getattr(entry, 'translated', '') or getattr(entry, 'original', '') or ""
        if len(display) > 50:
            display = display[:47] + "…"
        orig = getattr(entry, 'original', '')
        if orig and getattr(entry, 'translated', '') and orig != entry.translated:
            if len(orig) > 20:
                orig = orig[:17] + "…"
            return f"{t} [{src}] {orig} → {display}"
        return f"{t} [{src}] {display}"

    def _on_clear_history(self):
        if self.history_window is not None:
            try:
                self.history_window.clear_all()
            except Exception:
                self._refresh_history()
        else:
            self._refresh_history()

    # ----------------------------------------------------------
    #  对外刷新
    # ----------------------------------------------------------
    def refresh(self):
        self._loading = True
        self._load_config()
        self._loading = False
        self._refresh_history()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
