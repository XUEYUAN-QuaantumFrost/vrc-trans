"""
AI 代聊窗口模块
- 根据用户意图生成符合场景的社交话语
- 支持语气选择、目标语言、预设模板
- 生成结果可编辑后发送到 OSC
- 支持多家 AI：DeepSeek / OpenAI(ChatGPT) / Azure OpenAI / 自定义
- 默认继承全局 AI 配置，也可独立设置
- 增强：自动代聊模式、聊天记录、人设设定、双语输出
"""
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTextEdit, QGroupBox, QMessageBox,
    QGridLayout, QCheckBox, QSpinBox, QSlider
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QPalette
from i18n import tr
from ai_client import AIClient, PROVIDER_INFO, get_provider_label

# 语气选项
TONE_OPTIONS = [
    ("friendly", "aichat_tone_friendly"),
    ("formal", "aichat_tone_formal"),
    ("humorous", "aichat_tone_humorous"),
    ("shy", "aichat_tone_shy"),
    ("cool", "aichat_tone_cool"),
]

# 目标语言列表
TARGET_LANGUAGES = [
    "中文", "繁體中文", "日语", "韩语", "英语", "法语", "德语",
    "俄语", "西班牙语", "阿拉伯语", "蒙古语", "葡萄牙语", "意大利语",
    "越南语", "泰语",
]

# 预设模板：(key, 意图描述)
PRESETS = [
    ("aichat_preset_greeting", "跟旁边的人打个招呼，友好一点"),
    ("aichat_preset_thanks", "表达感谢"),
    ("aichat_preset_apology", "道歉"),
    ("aichat_preset_goodbye", "告别"),
    ("aichat_preset_compliment", "夸赞对方"),
    ("aichat_preset_friend", "请求加好友"),
    ("aichat_preset_play", "邀请对方一起玩"),
]

# API 模式选项：(key, label_key, provider)
API_MODES = [
    ("inherit", "aichat_mode_inherit", None),
    ("deepseek", "aichat_mode_deepseek", "deepseek"),
    ("openai", "aichat_mode_openai", "openai"),
    ("azure", "aichat_mode_azure", "azure"),
    ("custom", "aichat_mode_custom", "custom"),
]


class AIChatWindow(QWidget):
    """AI 代聊窗口"""
    generate_done_signal = pyqtSignal(str)

    def __init__(self, config, controller, parent=None):
        super().__init__(parent)
        self.config = config
        self.controller = controller
        self._generating = False
        self._auto_mode = False
        self._pending_text = ""  # 自动模式下累积的文本
        self._silence_timer = QTimer(self)
        self._silence_timer.setSingleShot(True)
        self._silence_timer.timeout.connect(self._auto_send)

        self.setWindowTitle(tr("aichat_title"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowStaysOnTopHint
        )
        # 窗口透明度
        opacity = float(self.config.get("aichat_window_opacity", 0.92))
        self.setWindowOpacity(opacity)

        self._build_ui()
        self._load_values()
        self.generate_done_signal.connect(self._on_generate_done)

        # 连接语音识别结果信号（自动模式用）
        if hasattr(self.controller, 'speech_result_signal'):
            self.controller.speech_result_signal.connect(self._on_speech_result)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # === 聊天记录区域（半透明） ===
        chat_group = QGroupBox("聊天记录")
        chat_layout = QVBoxLayout(chat_group)
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setMinimumHeight(180)
        self.chat_history.setStyleSheet(
            "QTextEdit { background: rgba(30, 30, 40, 200); "
            "color: #E0E0E0; border: 1px solid #555; border-radius: 6px; "
            "font-size: 13px; }"
        )
        chat_layout.addWidget(self.chat_history)
        layout.addWidget(chat_group)

        # === 自动代聊控制 ===
        auto_group = QGroupBox("自动代聊")
        auto_layout = QVBoxLayout(auto_group)

        auto_row = QHBoxLayout()
        self.auto_checkbox = QCheckBox("开启自动代聊（拾取语音自动回复）")
        self.auto_checkbox.stateChanged.connect(self._toggle_auto_mode)
        auto_row.addWidget(self.auto_checkbox)
        auto_row.addStretch()
        auto_layout.addLayout(auto_row)

        # 人设设定
        persona_row = QHBoxLayout()
        persona_row.addWidget(QLabel("人设/地区："))
        self.persona_edit = QLineEdit()
        self.persona_edit.setPlaceholderText("例如：我是中国人，用中文日语交流")
        persona_row.addWidget(self.persona_edit)
        auto_layout.addLayout(persona_row)

        # 选项行
        opt_row = QHBoxLayout()
        self.bilingual_checkbox = QCheckBox("双语输出")
        opt_row.addWidget(self.bilingual_checkbox)

        opt_row.addWidget(QLabel("最大字数："))
        self.max_chars_spin = QSpinBox()
        self.max_chars_spin.setRange(20, 200)
        self.max_chars_spin.setValue(60)
        opt_row.addWidget(self.max_chars_spin)

        opt_row.addWidget(QLabel("停顿发送(ms)："))
        self.silence_spin = QSpinBox()
        self.silence_spin.setRange(500, 5000)
        self.silence_spin.setSingleStep(100)
        self.silence_spin.setValue(1500)
        opt_row.addWidget(self.silence_spin)

        opt_row.addStretch()
        auto_layout.addLayout(opt_row)

        # 待发送文本显示
        pending_row = QHBoxLayout()
        pending_row.addWidget(QLabel("待发送："))
        self.pending_label = QLabel("（无）")
        self.pending_label.setStyleSheet("color: #888; font-style: italic;")
        self.pending_label.setWordWrap(True)
        pending_row.addWidget(self.pending_label)
        pending_row.addStretch()
        auto_layout.addLayout(pending_row)

        layout.addWidget(auto_group)

        # === 手动输入区域 ===
        intent_group = QGroupBox()
        intent_layout = QVBoxLayout(intent_group)
        intent_label = QLabel(tr("aichat_intent"))
        intent_layout.addWidget(intent_label)
        self.intent_edit = QLineEdit()
        self.intent_edit.setPlaceholderText(tr("aichat_intent_placeholder"))
        self.intent_edit.returnPressed.connect(self._generate)
        intent_layout.addWidget(self.intent_edit)
        layout.addWidget(intent_group)

        # 预设模板按钮
        preset_group = QGroupBox()
        preset_layout = QGridLayout(preset_group)
        preset_layout.setSpacing(4)
        for i, (key, desc) in enumerate(PRESETS):
            btn = QPushButton(tr(key))
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, d=desc: self._apply_preset(d))
            preset_layout.addWidget(btn, i // 4, i % 4)
        layout.addWidget(preset_group)

        # 选项行
        options_row = QHBoxLayout()
        options_row.setSpacing(8)
        # 语气
        tone_col = QVBoxLayout()
        tone_col.addWidget(QLabel(tr("aichat_tone")))
        self.tone_combo = QComboBox()
        for code, key in TONE_OPTIONS:
            self.tone_combo.addItem(tr(key), code)
        tone_col.addWidget(self.tone_combo)
        options_row.addLayout(tone_col)
        # 目标语言
        lang_col = QVBoxLayout()
        lang_col.addWidget(QLabel(tr("aichat_target_lang")))
        self.target_combo = QComboBox()
        self.target_combo.addItems(TARGET_LANGUAGES)
        lang_col.addWidget(self.target_combo)
        options_row.addLayout(lang_col)
        options_row.addStretch()
        layout.addLayout(options_row)

        # AI 提供商配置
        api_group = QGroupBox(tr("aichat_api_group"))
        api_layout = QVBoxLayout(api_group)
        # 提供商选择
        api_mode_row = QHBoxLayout()
        api_mode_row.addWidget(QLabel(tr("aichat_api_mode")))
        self.api_mode_combo = QComboBox()
        for key, label_key, _ in API_MODES:
            self.api_mode_combo.addItem(tr(label_key), key)
        self.api_mode_combo.currentIndexChanged.connect(self._toggle_api_config)
        api_mode_row.addWidget(self.api_mode_combo)
        api_mode_row.addStretch()
        api_layout.addLayout(api_mode_row)
        # 通用配置
        self.common_api_widget = QWidget()
        common_layout = QVBoxLayout(self.common_api_widget)
        common_layout.setContentsMargins(0, 0, 0, 0)
        key_row = QHBoxLayout()
        key_row.addWidget(QLabel(tr("aichat_api_key")))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("sk- ...")
        key_row.addWidget(self.api_key_edit)
        common_layout.addLayout(key_row)
        base_row = QHBoxLayout()
        base_row.addWidget(QLabel(tr("aichat_api_base")))
        self.api_base_edit = QLineEdit()
        base_row.addWidget(self.api_base_edit)
        common_layout.addLayout(base_row)
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel(tr("aichat_api_model")))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        model_row.addWidget(self.model_combo)
        common_layout.addLayout(model_row)
        api_layout.addWidget(self.common_api_widget)
        # Azure 专用配置
        self.azure_widget = QWidget()
        azure_layout = QVBoxLayout(self.azure_widget)
        azure_layout.setContentsMargins(0, 0, 0, 0)
        ep_row = QHBoxLayout()
        ep_row.addWidget(QLabel(tr("aichat_azure_endpoint")))
        self.azure_endpoint_edit = QLineEdit()
        self.azure_endpoint_edit.setPlaceholderText("https://xxx.openai.azure.com")
        ep_row.addWidget(self.azure_endpoint_edit)
        azure_layout.addLayout(ep_row)
        dep_row = QHBoxLayout()
        dep_row.addWidget(QLabel(tr("aichat_azure_deployment")))
        self.azure_deployment_edit = QLineEdit()
        self.azure_deployment_edit.setPlaceholderText("你的部署名")
        dep_row.addWidget(self.azure_deployment_edit)
        azure_layout.addLayout(dep_row)
        api_layout.addWidget(self.azure_widget)
        # 提示文字
        self.api_hint = QLabel("")
        self.api_hint.setStyleSheet("color: gray; font-size: 10px;")
        self.api_hint.setWordWrap(True)
        api_layout.addWidget(self.api_hint)
        layout.addWidget(api_group)

        # 生成按钮
        self.generate_btn = QPushButton(tr("aichat_generate"))
        self.generate_btn.setFixedHeight(36)
        self.generate_btn.setStyleSheet(
            "QPushButton { background: #4A90D9; color: white; border: none; "
            "border-radius: 6px; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background: #5BA0E9; }"
            "QPushButton:disabled { background: #888; }"
        )
        self.generate_btn.clicked.connect(self._generate)
        layout.addWidget(self.generate_btn)

        # 结果预览
        result_group = QGroupBox()
        result_layout = QVBoxLayout(result_group)
        result_label = QLabel(tr("aichat_result"))
        result_layout.addWidget(result_label)
        self.result_edit = QTextEdit()
        self.result_edit.setMaximumHeight(80)
        result_layout.addWidget(self.result_edit)
        layout.addWidget(result_group)

        # 发送按钮
        self.send_btn = QPushButton(tr("aichat_send"))
        self.send_btn.setFixedHeight(36)
        self.send_btn.setStyleSheet(
            "QPushButton { background: #5CB85C; color: white; border: none; "
            "border-radius: 6px; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background: #6DC86D; }"
            "QPushButton:disabled { background: #888; }"
        )
        self.send_btn.clicked.connect(self._send)
        layout.addWidget(self.send_btn)

    def _load_values(self):
        # 语气
        tone = self.config.get("aichat_default_tone", "friendly")
        for i, (code, _) in enumerate(TONE_OPTIONS):
            if code == tone:
                self.tone_combo.setCurrentIndex(i)
                break
        # 目标语言
        default_lang = self.config.get("aichat_default_target_lang", "")
        if not default_lang:
            default_lang = self.config.get("mic_target_lang", "日语")
        idx = self.target_combo.findText(default_lang)
        if idx >= 0:
            self.target_combo.setCurrentIndex(idx)
        # API 模式
        aichat_provider = self.config.get("aichat_provider", "")
        mode = aichat_provider if aichat_provider else "inherit"
        idx = self.api_mode_combo.findData(mode)
        if idx >= 0:
            self.api_mode_combo.setCurrentIndex(idx)
        # 加载独立配置
        self.api_key_edit.setText(self.config.get("aichat_api_key", ""))
        self.api_base_edit.setText(self.config.get("aichat_api_base", ""))
        self.model_combo.setEditText(self.config.get("aichat_model", ""))
        self.azure_endpoint_edit.setText(self.config.get("aichat_azure_endpoint", ""))
        self.azure_deployment_edit.setText(self.config.get("aichat_azure_deployment", ""))
        self._toggle_api_config()
        # 增强功能
        self.persona_edit.setText(self.config.get("aichat_persona", ""))
        self.bilingual_checkbox.setChecked(self.config.get("aichat_bilingual", True))
        self.max_chars_spin.setValue(int(self.config.get("aichat_max_chars", 60)))
        self.silence_spin.setValue(int(self.config.get("aichat_silence_timeout", 1500)))
        self.auto_checkbox.setChecked(self.config.get("aichat_auto_mode", False))

    def _toggle_api_config(self):
        mode = self.api_mode_combo.currentData()
        is_inherit = (mode == "inherit")
        is_azure = (mode == "azure")
        self.common_api_widget.setVisible(not is_inherit)
        self.azure_widget.setVisible(is_azure and not is_inherit)
        if is_inherit:
            provider = self.config.get("ai_provider", "deepseek")
            label = get_provider_label(provider)
            self.api_hint.setText(tr("aichat_inherit_hint").replace("{provider}", label))
        else:
            self.api_hint.setText("")
            info = PROVIDER_INFO.get(mode, {})
            if not self.api_base_edit.text().strip():
                self.api_base_edit.setPlaceholderText(info.get("default_base", ""))
            self.model_combo.clear()
            for m in info.get("recommended_models", []):
                self.model_combo.addItem(m)
            if not self.model_combo.currentText().strip():
                self.model_combo.setEditText(info.get("default_model", ""))
            if is_azure:
                self.api_hint.setText(tr("aichat_azure_hint"))

    def _toggle_auto_mode(self, state):
        """切换自动代聊模式"""
        self._auto_mode = (state == Qt.Checked)
        self.config.set("aichat_auto_mode", self._auto_mode)
        if self._auto_mode:
            self._append_chat("系统", "自动代聊已开启，正在监听语音...")
        else:
            self._silence_timer.stop()
            self._pending_text = ""
            self.pending_label.setText("（无）")
            self._append_chat("系统", "自动代聊已关闭")

    def _on_speech_result(self, text):
        """收到语音识别结果（自动模式）"""
        if not self._auto_mode or self._generating:
            return
        text = text.strip()
        if not text:
            return
        # 累积文本
        if self._pending_text:
            self._pending_text += " " + text
        else:
            self._pending_text = text
        self.pending_label.setText(self._pending_text)
        # 重置停顿计时器
        timeout = self.silence_spin.value()
        self._silence_timer.start(timeout)

    def _auto_send(self):
        """停顿超时，自动发送给 AI"""
        if not self._pending_text or self._generating:
            return
        text = self._pending_text
        self._pending_text = ""
        self.pending_label.setText("（无）")
        self._append_chat("对方", text)
        # 暂停语音识别（AI 生成期间不拾取）
        self._pause_speech()
        # 自动生成回复
        self.intent_edit.setText(text)
        self._generate(auto_send=True)

    def _pause_speech(self):
        """暂停语音识别"""
        if hasattr(self.controller, '_stop_speech'):
            try:
                self.controller._stop_speech()
            except Exception:
                pass

    def _resume_speech(self):
        """恢复语音识别"""
        if hasattr(self.controller, '_start_speech'):
            try:
                self.controller._start_speech()
            except Exception:
                pass

    def _append_chat(self, role, text):
        """添加聊天记录"""
        color_map = {
            "对方": "#FFB347",
            "AI": "#87CEEB",
            "我": "#90EE90",
            "系统": "#888888",
        }
        color = color_map.get(role, "#FFFFFF")
        self.chat_history.append(
            f'<span style="color:{color}; font-weight:bold;">[{role}]</span> '
            f'<span style="color:#E0E0E0;">{text}</span>'
        )
        # 滚动到底部
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _apply_preset(self, desc):
        self.intent_edit.setText(desc)

    def _get_ai_client(self):
        mode = self.api_mode_combo.currentData()
        if mode == "inherit":
            provider = self.config.get("ai_provider", "deepseek")
            return AIClient(
                provider=provider,
                api_key=self.config.get("ai_api_key", ""),
                api_base=self.config.get("ai_api_base", ""),
                model=self.config.get("ai_model", ""),
                azure_endpoint=self.config.get("ai_azure_endpoint", ""),
                azure_deployment=self.config.get("ai_azure_deployment", ""),
                azure_api_version=self.config.get("ai_azure_api_version", "2024-02-15-preview"),
            )
        else:
            return AIClient(
                provider=mode,
                api_key=self.api_key_edit.text().strip(),
                api_base=self.api_base_edit.text().strip(),
                model=self.model_combo.currentText().strip(),
                azure_endpoint=self.azure_endpoint_edit.text().strip(),
                azure_deployment=self.azure_deployment_edit.text().strip(),
            )

    def _save_aichat_config(self):
        mode = self.api_mode_combo.currentData()
        if mode == "inherit":
            self.config.set("aichat_provider", "")
            self.config.set("aichat_api_key", "")
            self.config.set("aichat_api_base", "")
            self.config.set("aichat_model", "")
            self.config.set("aichat_azure_endpoint", "")
            self.config.set("aichat_azure_deployment", "")
        else:
            self.config.set("aichat_provider", mode)
            self.config.set("aichat_api_key", self.api_key_edit.text().strip())
            self.config.set("aichat_api_base", self.api_base_edit.text().strip())
            self.config.set("aichat_model", self.model_combo.currentText().strip())
            self.config.set("aichat_azure_endpoint", self.azure_endpoint_edit.text().strip())
            self.config.set("aichat_azure_deployment", self.azure_deployment_edit.text().strip())
        # 保存增强配置
        self.config.set("aichat_persona", self.persona_edit.text().strip())
        self.config.set("aichat_bilingual", self.bilingual_checkbox.isChecked())
        self.config.set("aichat_max_chars", self.max_chars_spin.value())
        self.config.set("aichat_silence_timeout", self.silence_spin.value())

    def _generate(self, auto_send=False):
        if self._generating:
            return
        intent = self.intent_edit.text().strip()
        if not intent:
            return
        client = self._get_ai_client()
        if not client.is_ready():
            QMessageBox.warning(self, tr("aichat_title"), tr("aichat_no_api"))
            self._resume_speech()
            return
        tone_code = self.tone_combo.currentData()
        target_lang = self.target_combo.currentText()
        self._generating = True
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText(tr("aichat_generating"))
        self.result_edit.clear()
        self._auto_send_flag = auto_send

        def _worker():
            result = self._call_ai(client, intent, tone_code, target_lang)
            self.generate_done_signal.emit(result)
        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _call_ai(self, client, intent, tone_code, target_lang):
        try:
            tone_name = dict(TONE_OPTIONS).get(tone_code, "friendly")
            persona = self.persona_edit.text().strip()
            max_chars = self.max_chars_spin.value()
            bilingual = self.bilingual_checkbox.isChecked()

            system_prompt = (
                f"你是 VRChat 社交助手，正在代替用户进行社交对话。\n"
                f"用户人设：{persona}\n"
                f"对方说了：{intent}\n"
                f"请以用户的身份生成一句自然的回复。\n"
                f"要求：\n"
                f"1. 简短（不超过{max_chars}个字符）\n"
                f"2. 口语化，符合{tone_name}语气\n"
                f"3. 只输出回复内容本身，不要加解释、引号或前缀\n"
                f"4. 自然热情，符合 VRChat 社交场景\n"
            )
            if bilingual:
                system_prompt += (
                    f"5. 用{target_lang}回复，并在括号里附上中文翻译，格式：{target_lang}内容（中文翻译）\n"
                )
            else:
                system_prompt += f"5. 用{target_lang}回复\n"

            result = client.chat(
                system_prompt=system_prompt,
                user_message=intent,
                temperature=0.8,
            )
            return result if result else "[Error] AI 返回为空"
        except Exception as e:
            print(f"[AIChat] 生成失败: {e}")
            return f"[Error] {e}"

    def _on_generate_done(self, result):
        self._generating = False
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText(tr("aichat_generate"))
        self.result_edit.setPlainText(result)

        # 自动模式下自动发送
        if getattr(self, '_auto_send_flag', False):
            self._auto_send_flag = False
            if not result.startswith("[Error]"):
                self._append_chat("AI", result)
                self._send()
            else:
                self._append_chat("系统", f"生成失败：{result}")
                self._resume_speech()
        else:
            # 手动模式也恢复语音识别（如果之前暂停了）
            self._resume_speech()

    def _send(self):
        text = self.result_edit.toPlainText().strip()
        if not text:
            return
        target_lang = self.target_combo.currentText()
        self._save_aichat_config()
        # 添加到历史记录
        if hasattr(self.controller, 'history_window') and self.controller.history_window:
            self.controller.history_window.add_entry(
                original=text,
                translated=text,
                source="aichat",
                target_lang=target_lang,
            )
        # 发送到 OSC
        if hasattr(self.controller, '_send_osc_bilingual'):
            self.controller._send_osc_bilingual(text, text)
        elif self.controller.osc:
            self.controller.osc.send_chatbox(text, send_immediately=True)
        # 显示在悬浮窗
        self.controller.show_text_signal.emit(text, "")
        # 保存默认设置
        self.config.set("aichat_default_tone", self.tone_combo.currentData())
        self.config.set("aichat_default_target_lang", target_lang)
        # 自动模式下发送完恢复语音识别
        if self._auto_mode:
            self._resume_speech()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        # 关闭窗口时恢复语音识别
        self._resume_speech()
