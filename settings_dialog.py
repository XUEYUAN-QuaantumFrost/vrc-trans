"""
设置对话框（多语言版）
包含：翻译设置、OSC设置、语音识别、悬浮窗外观、其他设置
"""
from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QCheckBox, QPushButton, QColorDialog, QFontDialog, QGroupBox,
    QFormLayout, QSlider, QTextEdit, QFileDialog, QMessageBox, QListWidget,
    QProgressBar, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
from i18n import tr, LANGUAGES
from ai_client import PROVIDER_INFO, get_provider_label


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None, recognizer=None):
        super().__init__(parent)
        self.config = config
        self.recognizer = recognizer  # 用于实时音量指示器
        self._volume_timer = None
        self.setWindowTitle(tr("dialog_title"))
        self.setMinimumWidth(620)
        self.setMinimumHeight(400)
        self.resize(680, 800)  # 默认大小，内容多可滚动
        # 设置窗口图标
        try:
            import os
            from PyQt5.QtGui import QIcon
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
        self._build_ui()
        # 给所有下拉框设置强焦点和最大可见项，避免弹出菜单被遮挡
        # 注意：必须在 _build_ui() 之后执行，否则此时还没有子控件
        for combo in self.findChildren(QComboBox):
            combo.setFocusPolicy(Qt.StrongFocus)
            combo.setMaxVisibleItems(15)
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        # 给每个 tab 包一层滚动区域，内容多时可滚动
        from PyQt5.QtWidgets import QScrollArea
        def _wrap_scroll(widget):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(widget)
            scroll.setFocusPolicy(Qt.NoFocus)  # 避免滚动区域抢夺下拉框焦点
            return scroll
        tabs.addTab(_wrap_scroll(self._build_translate_tab()), tr("tab_translate"))
        tabs.addTab(_wrap_scroll(self._build_osc_tab()), tr("tab_osc"))
        tabs.addTab(_wrap_scroll(self._build_speech_tab()), tr("tab_speech"))
        tabs.addTab(_wrap_scroll(self._build_simul_tab()), "同声传译")
        tabs.addTab(_wrap_scroll(self._build_appearance_tab()), tr("tab_appearance"))
        tabs.addTab(_wrap_scroll(self._build_other_tab()), tr("tab_other"))
        layout.addWidget(tabs)

        # 底部按钮
        btn_layout = QHBoxLayout()
        import_btn = QPushButton(tr("config_import"))
        import_btn.clicked.connect(self._import_config)
        btn_layout.addWidget(import_btn)
        export_btn = QPushButton(tr("config_export"))
        export_btn.clicked.connect(self._export_config)
        btn_layout.addWidget(export_btn)
        reset_btn = QPushButton(tr("config_reset"))
        reset_btn.setStyleSheet("color: #d9534f;")
        reset_btn.clicked.connect(self._reset_config)
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        ok_btn = QPushButton(tr("btn_ok"))
        cancel_btn = QPushButton(tr("btn_cancel"))
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    # ========== 翻译引擎切换 ==========
    def _on_translate_engine_changed(self, index):
        """翻译引擎切换时显示/隐藏对应配置"""
        engine = self.translate_engine_combo.currentData()
        is_ai = (engine == "deepseek")
        is_baidu = (engine == "baidu")

        # AI 配置区域
        self.ai_provider_combo.setVisible(is_ai)
        self.ai_config_widget.setVisible(is_ai)
        self.ai_azure_widget.setVisible(is_ai and self.ai_provider_combo.currentData() == "azure")

        # 百度配置
        self.baidu_widget.setVisible(is_baidu)

    def _on_ai_provider_changed(self, index):
        """AI 提供商切换时保存当前配置、加载新提供商配置"""
        # 先保存当前提供商的配置
        old_provider = getattr(self, '_current_ai_provider', None)
        if old_provider:
            self._save_provider_config(old_provider)

        provider = self.ai_provider_combo.currentData()
        self._current_ai_provider = provider
        info = PROVIDER_INFO.get(provider, {})
        is_azure = (provider == "azure")

        # Azure 专用配置显示
        self.ai_azure_widget.setVisible(is_azure)
        self.ai_base_row_widget.setVisible(not is_azure)
        self.ai_model_row_widget.setVisible(not is_azure)

        # 从配置字典加载该提供商的保存值
        saved = self._load_provider_config(provider)
        self.ai_api_key_edit.setText(saved.get("api_key", ""))
        self.ai_base_edit.setText(saved.get("api_base", ""))
        self.ai_azure_endpoint_edit.setText(saved.get("azure_endpoint", ""))
        self.ai_azure_deployment_edit.setText(saved.get("azure_deployment", ""))

        # 更新模型推荐列表
        self.ai_model_combo.clear()
        recommended = info.get("recommended_models", [])
        for m in recommended:
            self.ai_model_combo.addItem(m)
        saved_model = saved.get("model", "")
        default_model = info.get("default_model", "")
        if saved_model and saved_model in recommended:
            self.ai_model_combo.setEditText(saved_model)
        elif saved_model and not recommended:
            # 自定义提供商，没有推荐列表，直接用保存的
            self.ai_model_combo.setEditText(saved_model)
        else:
            self.ai_model_combo.setEditText(default_model)
        # API 地址占位符
        if not self.ai_base_edit.text().strip():
            self.ai_base_edit.setPlaceholderText(info.get("default_base", ""))

    def _update_volume_meter(self):
        """更新音量指示器（VRC 风格，说话时有反应）"""
        try:
            if self.recognizer is not None and hasattr(self, 'volume_meter'):
                # 下拉框弹出时跳过更新，避免进度条刷新抢走焦点导致下拉列表闪退
                for combo in self.findChildren(QComboBox):
                    if combo.view().isVisible():
                        return
                vol = self.recognizer.get_current_volume()
                display_vol = min(100, int(vol * 1000))
                self.volume_meter.setValue(display_vol)
        except Exception:
            pass  # 音量更新失败静默忽略，不影响主程序

    def closeEvent(self, event):
        """关闭窗口时停止音量定时器"""
        if self._volume_timer is not None:
            self._volume_timer.stop()
        super().closeEvent(event)

    def _save_provider_config(self, provider):
        """保存指定提供商的配置到字典"""
        configs = self.config.get("ai_provider_configs", {}) or {}
        configs[provider] = {
            "api_key": self.ai_api_key_edit.text().strip(),
            "api_base": self.ai_base_edit.text().strip(),
            "model": self.ai_model_combo.currentText().strip(),
            "azure_endpoint": self.ai_azure_endpoint_edit.text().strip() if hasattr(self, 'ai_azure_endpoint_edit') else "",
            "azure_deployment": self.ai_azure_deployment_edit.text().strip() if hasattr(self, 'ai_azure_deployment_edit') else "",
        }
        self.config.set("ai_provider_configs", configs)

    def _load_provider_config(self, provider):
        """从字典加载指定提供商的配置"""
        configs = self.config.get("ai_provider_configs", {}) or {}
        return configs.get(provider, {})

    # ========== 翻译 Tab ==========
    def _build_translate_tab(self):
        w = QWidget()
        form = QFormLayout(w)

        # 界面语言
        self.lang_combo = QComboBox()
        self.lang_combo.setToolTip("选择程序界面显示语言")
        native_names = [
            ("auto", tr("lang_auto")),
            ("zh", "简体中文"),
            ("zh-tw", "繁體中文"),
            ("en", "English"),
            ("ja", "日本語"),
            ("ko", "한국어"),
            ("fr", "Français"),
            ("de", "Deutsch"),
            ("es", "Español"),
            ("ru", "Русский"),
            ("pt", "Português"),
        ]
        for code, name in native_names:
            self.lang_combo.addItem(name, code)
        form.addRow(tr("language") + ":", self.lang_combo)

        # 翻译引擎
        self.translate_engine_combo = QComboBox()
        self.translate_engine_combo.setToolTip("选择翻译服务提供商：AI翻译（DeepSeek/OpenAI等）/谷歌翻译/百度翻译")
        self.translate_engine_combo.addItem(tr("engine_ai"), "deepseek")
        self.translate_engine_combo.addItem(tr("engine_google"), "google")
        self.translate_engine_combo.addItem(tr("engine_baidu"), "baidu")
        self.translate_engine_combo.currentIndexChanged.connect(self._on_translate_engine_changed)
        form.addRow(tr("translate_engine") + ":", self.translate_engine_combo)

        # AI 提供商
        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.setToolTip("选择AI翻译服务商，不同服务商需要对应的API Key")
        for key, info in PROVIDER_INFO.items():
            self.ai_provider_combo.addItem(info["label"], key)
        self.ai_provider_combo.currentIndexChanged.connect(self._on_ai_provider_changed)
        form.addRow(tr("ai_provider") + ":", self.ai_provider_combo)

        # AI 配置区域
        self.ai_config_widget = QWidget()
        ai_layout = QVBoxLayout(self.ai_config_widget)
        ai_layout.setContentsMargins(0, 0, 0, 0)
        ai_layout.setSpacing(6)

        # API Key
        key_row = QHBoxLayout()
        key_row.addWidget(QLabel(tr("api_key")))
        self.ai_api_key_edit = QLineEdit()
        self.ai_api_key_edit.setEchoMode(QLineEdit.Password)
        self.ai_api_key_edit.setPlaceholderText("sk- ...")
        key_row.addWidget(self.ai_api_key_edit)
        ai_layout.addLayout(key_row)

        # API 地址
        self.ai_base_row_widget = QWidget()
        base_row = QHBoxLayout(self.ai_base_row_widget)
        base_row.setContentsMargins(0, 0, 0, 0)
        base_row.addWidget(QLabel(tr("api_base")))
        self.ai_base_edit = QLineEdit()
        base_row.addWidget(self.ai_base_edit)
        ai_layout.addWidget(self.ai_base_row_widget)

        # 模型
        self.ai_model_row_widget = QWidget()
        model_row = QHBoxLayout(self.ai_model_row_widget)
        model_row.setContentsMargins(0, 0, 0, 0)
        model_row.addWidget(QLabel(tr("model")))
        self.ai_model_combo = QComboBox()
        self.ai_model_combo.setToolTip("选择AI翻译使用的模型，不同模型速度和质量不同")
        self.ai_model_combo.setEditable(True)
        model_row.addWidget(self.ai_model_combo)
        ai_layout.addWidget(self.ai_model_row_widget)

        form.addRow(self.ai_config_widget)

        # Azure 专用配置
        self.ai_azure_widget = QWidget()
        azure_layout = QVBoxLayout(self.ai_azure_widget)
        azure_layout.setContentsMargins(0, 0, 0, 0)
        azure_layout.setSpacing(6)

        ep_row = QHBoxLayout()
        ep_row.addWidget(QLabel(tr("azure_endpoint")))
        self.ai_azure_endpoint_edit = QLineEdit()
        self.ai_azure_endpoint_edit.setPlaceholderText("https://xxx.openai.azure.com")
        ep_row.addWidget(self.ai_azure_endpoint_edit)
        azure_layout.addLayout(ep_row)

        dep_row = QHBoxLayout()
        dep_row.addWidget(QLabel(tr("azure_deployment")))
        self.ai_azure_deployment_edit = QLineEdit()
        self.ai_azure_deployment_edit.setPlaceholderText("你的部署名")
        dep_row.addWidget(self.ai_azure_deployment_edit)
        azure_layout.addLayout(dep_row)

        form.addRow(self.ai_azure_widget)

        # 百度翻译配置
        self.baidu_widget = QWidget()
        baidu_layout = QVBoxLayout(self.baidu_widget)
        baidu_layout.setContentsMargins(0, 0, 0, 0)
        baidu_layout.setSpacing(6)
        baidu_appid_row = QHBoxLayout()
        baidu_appid_row.addWidget(QLabel(tr("baidu_appid")))
        self.baidu_appid_edit = QLineEdit()
        baidu_appid_row.addWidget(self.baidu_appid_edit)
        baidu_layout.addLayout(baidu_appid_row)
        baidu_secret_row = QHBoxLayout()
        baidu_secret_row.addWidget(QLabel(tr("baidu_secret")))
        self.baidu_secret_edit = QLineEdit()
        self.baidu_secret_edit.setEchoMode(QLineEdit.Password)
        baidu_secret_row.addWidget(self.baidu_secret_edit)
        baidu_layout.addLayout(baidu_secret_row)
        baidu_hint = QLabel(tr("baidu_hint"))
        baidu_hint.setStyleSheet("color: gray; font-size: 10px;")
        baidu_hint.setWordWrap(True)
        baidu_layout.addWidget(baidu_hint)
        form.addRow(self.baidu_widget)

        # 目标语言
        self.target_combo = QComboBox()
        self.target_combo.setToolTip("选择翻译后的目标语言，例如英语、日语等")
        self.target_combo.addItems([
            "中文", "日语", "韩语", "英语", "法语", "德语",
            "俄语", "西班牙语", "阿拉伯语", "蒙古语", "葡萄牙语", "意大利语"
        ])
        form.addRow(tr("target_lang"), self.target_combo)

        # 自定义提示词
        self.prompt_edit = QLineEdit()
        form.addRow(tr("custom_prompt"), self.prompt_edit)

        # 启用翻译
        self.enable_translate_cb = QCheckBox(tr("enable_translate"))
        form.addRow(self.enable_translate_cb)

        return w

    # ========== OSC Tab ==========
    def _build_osc_tab(self):
        w = QWidget()
        form = QFormLayout(w)

        self.enable_osc_cb = QCheckBox(tr("enable_osc"))
        form.addRow(self.enable_osc_cb)

        self.osc_ip_edit = QLineEdit()
        form.addRow(tr("osc_ip"), self.osc_ip_edit)

        self.osc_port_spin = QSpinBox()
        self.osc_port_spin.setRange(1, 65535)
        form.addRow(tr("osc_port"), self.osc_port_spin)

        group = QGroupBox(tr("auto_send_group"))
        gform = QFormLayout(group)
        self.enable_auto_send_cb = QCheckBox(tr("enable_auto_send"))
        gform.addRow(self.enable_auto_send_cb)
        self.auto_send_delay_spin = QDoubleSpinBox()
        self.auto_send_delay_spin.setRange(0.0, 30)
        self.auto_send_delay_spin.setSingleStep(0.5)
        self.auto_send_delay_spin.setSuffix(" s")
        gform.addRow(tr("send_delay"), self.auto_send_delay_spin)
        self.enable_auto_activate_cb = QCheckBox(tr("enable_auto_activate"))
        gform.addRow(self.enable_auto_activate_cb)
        self.auto_activate_spin = QSpinBox()
        self.auto_activate_spin.setRange(1, 60)
        self.auto_activate_spin.setSuffix(" s")
        gform.addRow(tr("activate_interval"), self.auto_activate_spin)
        form.addRow(group)

        bi_group = QGroupBox(tr("osc_bilingual_group"))
        bi_form = QFormLayout(bi_group)
        self.enable_osc_bilingual_cb = QCheckBox(tr("enable_osc_bilingual"))
        bi_form.addRow(self.enable_osc_bilingual_cb)
        self.osc_bilingual_format_combo = QComboBox()
        self.osc_bilingual_format_combo.setToolTip("选择发送到VRChat的双语字幕格式：原文+译文/仅译文/仅原文")
        self.osc_bilingual_format_combo.addItems([
            tr("osc_format_multiline"),
            tr("osc_format_parenthesis"),
            tr("osc_format_slash"),
            tr("osc_format_translate_only"),
        ])
        bi_form.addRow(tr("osc_bilingual_format"), self.osc_bilingual_format_combo)
        self.osc_bilingual_order_combo = QComboBox()
        self.osc_bilingual_order_combo.setToolTip("选择双语字幕的显示顺序：原文在前或译文在前")
        self.osc_bilingual_order_combo.addItems([
            tr("osc_order_original_first"),
            tr("osc_order_translate_first"),
        ])
        bi_form.addRow(tr("osc_bilingual_order"), self.osc_bilingual_order_combo)
        self.enable_osc_typing_cb = QCheckBox(tr("enable_osc_typing"))
        bi_form.addRow(self.enable_osc_typing_cb)
        form.addRow(bi_group)

        return w

    # ========== 语音识别 Tab ==========
    def _build_speech_tab(self):
        w = QWidget()
        form = QFormLayout(w)

        self.enable_speech_cb = QCheckBox(tr("enable_speech"))
        form.addRow(self.enable_speech_cb)

        # 双向模式
        dual_group = QGroupBox(tr("dual_mode_group"))
        dual_form = QFormLayout(dual_group)
        self.dual_mode_cb = QCheckBox(tr("dual_mode_desc"))
        dual_form.addRow(self.dual_mode_cb)
        self.enable_mic_to_osc_cb = QCheckBox(tr("enable_mic_to_osc"))
        dual_form.addRow(self.enable_mic_to_osc_cb)
        self.mic_target_combo = QComboBox()
        self.mic_target_combo.setToolTip("麦克风识别的内容翻译成什么语言")
        self.mic_target_combo.addItems([
            "中文", "日语", "韩语", "英语", "法语", "德语",
            "俄语", "西班牙语", "阿拉伯语", "蒙古语", "葡萄牙语", "意大利语"
        ])
        dual_form.addRow(tr("mic_target_lang"), self.mic_target_combo)
        self.enable_computer_to_subtitle_cb = QCheckBox(tr("enable_computer_to_subtitle"))
        dual_form.addRow(self.enable_computer_to_subtitle_cb)
        self.computer_target_combo = QComboBox()
        self.computer_target_combo.setToolTip("电脑声音识别的内容翻译成什么语言")
        self.computer_target_combo.addItems([
            "中文", "日语", "韩语", "英语", "法语", "德语",
            "俄语", "西班牙语", "阿拉伯语", "蒙古语", "葡萄牙语", "意大利语"
        ])
        dual_form.addRow(tr("computer_target_lang"), self.computer_target_combo)
        # ===== 麦克风单独识别设置 =====
        mic_eng_group = QGroupBox("麦克风识别设置（留空则用下方全局设置）")
        mic_eng_form = QFormLayout(mic_eng_group)
        self.mic_engine_combo = QComboBox()
        self.mic_engine_combo.setMinimumHeight(28)
        self.mic_engine_combo.addItem("（使用全局设置）", "")
        self.mic_engine_combo.addItem("faster-whisper", "faster")
        self.mic_engine_combo.addItem("Sherpa-onnx", "sherpa")
        mic_eng_form.addRow("识别引擎：", self.mic_engine_combo)

        self.mic_model_combo = QComboBox()
        self.mic_model_combo.setMinimumHeight(28)
        self.mic_model_combo.setMinimumWidth(200)
        self.mic_model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.mic_sherpa_model_combo = QComboBox()
        self.mic_sherpa_model_combo.setMinimumHeight(28)
        self.mic_sherpa_model_combo.setMinimumWidth(200)
        try:
            from sherpa_recognizer import list_models
            for m in list_models():
                self.mic_sherpa_model_combo.addItem(m["name"], m["id"])
        except Exception:
            self.mic_sherpa_model_combo.addItem("流式 Paraformer 中英双语", "streaming-paraformer-bilingual-zh-en")
        from PyQt5.QtWidgets import QStackedWidget
        self.mic_model_stack = QStackedWidget()
        self.mic_model_stack.setMinimumHeight(28)
        self.mic_model_stack.addWidget(self.mic_model_combo)
        self.mic_model_stack.addWidget(self.mic_sherpa_model_combo)
        mic_eng_form.addRow("识别模型：", self.mic_model_stack)
        def _on_mic_engine_changed(idx):
            eng = self.mic_engine_combo.currentData()
            self.mic_model_stack.setCurrentIndex(1 if eng == "sherpa" else 0)
        self.mic_engine_combo.currentIndexChanged.connect(_on_mic_engine_changed)
        dual_form.addRow(mic_eng_group)

        # ===== 电脑声音单独识别设置 =====
        comp_eng_group = QGroupBox("电脑声音识别设置（留空则用下方全局设置）")
        comp_eng_form = QFormLayout(comp_eng_group)
        self.computer_engine_combo = QComboBox()
        self.computer_engine_combo.setMinimumHeight(28)
        self.computer_engine_combo.addItem("（使用全局设置）", "")
        self.computer_engine_combo.addItem("faster-whisper", "faster")
        self.computer_engine_combo.addItem("Sherpa-onnx", "sherpa")
        comp_eng_form.addRow("识别引擎：", self.computer_engine_combo)

        self.computer_model_combo = QComboBox()
        self.computer_model_combo.setMinimumHeight(28)
        self.computer_model_combo.setMinimumWidth(200)
        self.computer_model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.computer_sherpa_model_combo = QComboBox()
        self.computer_sherpa_model_combo.setMinimumHeight(28)
        self.computer_sherpa_model_combo.setMinimumWidth(200)
        try:
            from sherpa_recognizer import list_models
            for m in list_models():
                self.computer_sherpa_model_combo.addItem(m["name"], m["id"])
        except Exception:
            self.computer_sherpa_model_combo.addItem("流式 Paraformer 中英双语", "streaming-paraformer-bilingual-zh-en")
        self.computer_model_stack = QStackedWidget()
        self.computer_model_stack.setMinimumHeight(28)
        self.computer_model_stack.addWidget(self.computer_model_combo)
        self.computer_model_stack.addWidget(self.computer_sherpa_model_combo)
        comp_eng_form.addRow("识别模型：", self.computer_model_stack)
        def _on_computer_engine_changed(idx):
            eng = self.computer_engine_combo.currentData()
            self.computer_model_stack.setCurrentIndex(1 if eng == "sherpa" else 0)
        self.computer_engine_combo.currentIndexChanged.connect(_on_computer_engine_changed)
        dual_form.addRow(comp_eng_group)

        dual_hint = QLabel(tr("dual_mode_hint"))
        dual_hint.setStyleSheet("color: gray; font-size: 11px;")
        dual_hint.setWordWrap(True)
        dual_form.addRow(dual_hint)
        form.addRow(dual_group)

        # 双向模式启用时才显示单独引擎/模型设置
        def _toggle_dual_eng_settings(checked):
            mic_eng_group.setVisible(checked)
            comp_eng_group.setVisible(checked)
        self.dual_mode_cb.toggled.connect(_toggle_dual_eng_settings)
        _toggle_dual_eng_settings(self.dual_mode_cb.isChecked())

        # 单路模式音源
        self.source_combo = QComboBox()
        self.source_combo.setToolTip("麦克风：只识别你说的话\n电脑声音：只识别电脑里的声音（如VRChat其他人说话）\n双路：同时识别麦克风和电脑声音")
        self.source_combo.addItem(tr("source_computer"), "computer")
        self.source_combo.addItem(tr("source_mic"), "mic")
        form.addRow(tr("record_source") + " (" + tr("single_mode_only") + ")", self.source_combo)

        # 单路模式输出
        single_out_group = QGroupBox(tr("single_output_group"))
        single_out_form = QFormLayout(single_out_group)
        self.single_show_subtitle_cb = QCheckBox(tr("single_show_subtitle"))
        single_out_form.addRow(self.single_show_subtitle_cb)
        self.single_send_osc_cb = QCheckBox(tr("single_send_osc"))
        single_out_form.addRow(self.single_send_osc_cb)
        form.addRow(single_out_group)

        # 音频设备
        device_hint = QLabel(tr("device_hint"))
        device_hint.setStyleSheet("color: gray; font-size: 11px;")
        device_hint.setWordWrap(True)

        refresh_btn = QPushButton(tr("refresh_devices"))
        refresh_btn.clicked.connect(self._refresh_devices)

        self.device_computer_combo = QComboBox()
        self.device_computer_combo.setToolTip("选择录制电脑声音的音频设备，通常选「立体声混音」或虚拟音频设备")
        self.device_mic_combo = QComboBox()
        self.device_mic_combo.setToolTip("选择你的麦克风设备")

        device_row = QHBoxLayout()
        device_row.addWidget(QLabel(tr("device_computer")))
        device_row.addWidget(self.device_computer_combo, 1)
        form.addRow(device_row)

        device_row2 = QHBoxLayout()
        device_row2.addWidget(QLabel(tr("device_mic")))
        device_row2.addWidget(self.device_mic_combo, 1)
        form.addRow(device_row2)

        form.addRow(refresh_btn)
        form.addRow(device_hint)

        # 识别引擎
        self.engine_combo = QComboBox()
        self.engine_combo.setMinimumHeight(28)
        self.engine_combo.setToolTip("Sherpa-onnx：中文准，流式低延迟（推荐）\nfaster-whisper：通用多语言，EXE模式可能不稳定")
        self.engine_combo.addItem("faster-whisper", "faster")
        self.engine_combo.addItem("Sherpa-onnx", "sherpa")
        form.addRow(tr("engine"), self.engine_combo)

        # faster-whisper 模型大小
        # 模型选择：用 QStackedWidget 切换 faster-whisper 模型大小 和 sherpa 模型列表
        self.model_combo_speech = QComboBox()
        self.model_combo_speech.setMinimumHeight(28)
        self.model_combo_speech.setMinimumWidth(200)
        self.model_combo_speech.setToolTip("faster-whisper模型大小：tiny最快但准确率低，large最慢但准确率最高")
        self.model_combo_speech.addItems(["tiny", "base", "small", "medium", "large"])

        self.sherpa_model_combo = QComboBox()
        self.sherpa_model_combo.setMinimumHeight(28)
        self.sherpa_model_combo.setMinimumWidth(200)
        self.sherpa_model_combo.setToolTip("Sherpa-onnx模型：流式模型边说边识别延迟低，离线模型准确率高但需等说完")
        try:
            from sherpa_recognizer import list_models
            for m in list_models():
                label = f"{m['name']} ({m['size']}MB)"
                self.sherpa_model_combo.addItem(label, m["id"])
        except Exception as e:
            print(f"[Settings] 加载 sherpa 模型列表失败: {e}")
            self.sherpa_model_combo.addItem("流式 Paraformer 中英双语", "streaming-paraformer-bilingual-zh-en")

        from PyQt5.QtWidgets import QStackedWidget
        self.model_stack = QStackedWidget()
        self.model_stack.setMinimumHeight(28)
        self.model_stack.addWidget(self.model_combo_speech)  # index 0: faster-whisper
        self.model_stack.addWidget(self.sherpa_model_combo)  # index 1: sherpa
        model_hint = QLabel("流式模型边说边出结果，延迟低；离线模型准确率高但需等说完。")
        model_hint.setStyleSheet("color: gray; font-size: 11px;")
        model_hint.setWordWrap(True)
        form.addRow("识别模型：", self.model_stack)

        # SenseVoice 语言选择（仅对 SenseVoice 五语言模型有效）
        self.sense_voice_lang_combo = QComboBox()
        self.sense_voice_lang_combo.setMinimumHeight(28)
        self.sense_voice_lang_combo.setMinimumWidth(200)
        self.sense_voice_lang_combo.addItem("自动检测", "auto")
        self.sense_voice_lang_combo.addItem("中文", "zh")
        self.sense_voice_lang_combo.addItem("英语", "en")
        self.sense_voice_lang_combo.addItem("日语", "ja")
        self.sense_voice_lang_combo.addItem("韩语", "ko")
        self.sense_voice_lang_combo.addItem("粤语", "yue")
        self.sense_voice_lang_combo.setToolTip("仅对 SenseVoice 五语言模型有效。看日语番时选日语可大幅提升识别准确率。")
        form.addRow("SenseVoice 语言：", self.sense_voice_lang_combo)
        lang_hint = QLabel("看日语/韩语番时手动选择对应语言，避免自动检测误判成中文。")
        lang_hint.setStyleSheet("color: gray; font-size: 11px;")
        lang_hint.setWordWrap(True)
        form.addRow(lang_hint)

        form.addRow(model_hint)

        # 根据引擎切换显示对应模型选择
        def _on_engine_changed(idx):
            engine = self.engine_combo.currentData()
            if engine == "sherpa":
                self.model_stack.setCurrentIndex(1)
            else:
                self.model_stack.setCurrentIndex(0)
        self.engine_combo.currentIndexChanged.connect(_on_engine_changed)
        _on_engine_changed(0)  # 初始化显示状态

        # 已下载模型列表
        downloaded_label = QLabel("已下载模型：")
        self.downloaded_models_edit = QTextEdit()
        self.downloaded_models_edit.setReadOnly(True)
        self.downloaded_models_edit.setMaximumHeight(80)
        self.downloaded_models_edit.setStyleSheet(
            "QTextEdit { background: #2d2d2d; color: #e0e0e0; border: 1px solid #555; }"
        )
        self._refresh_downloaded_models()
        form.addRow(downloaded_label)
        form.addRow(self.downloaded_models_edit)

        self.device_combo = QComboBox()
        self.device_combo.setToolTip("CPU：大多数电脑够用（默认）\nCUDA：有NVIDIA显卡可选，需额外配置CUDA环境")
        self.device_combo.addItems(["cpu", "cuda"])
        self.device_combo.setToolTip("CPU：大多数电脑够用（默认）\nCUDA：有NVIDIA显卡可选，需额外配置CUDA环境")
        form.addRow(tr("run_device"), self.device_combo)

        self.compute_combo = QComboBox()
        self.compute_combo.setToolTip("计算精度：int8省内存速度快（CPU推荐），float16质量好（GPU推荐）")
        self.compute_combo.addItems([tr("compute_int8"), tr("compute_fp16"), tr("compute_fp32")])
        form.addRow(tr("compute_type"), self.compute_combo)

        # VAD
        vad_group = QGroupBox(tr("vad_group"))
        vad_form = QFormLayout(vad_group)
        self.vad_aggressive_spin = QSpinBox()
        self.vad_aggressive_spin.setRange(0, 3)
        self.vad_aggressive_spin.setSuffix("  (0~3)")
        vad_form.addRow(tr("vad_aggressive"), self.vad_aggressive_spin)
        self.silence_threshold_spin = QSpinBox()
        self.silence_threshold_spin.setRange(100, 5000)
        self.silence_threshold_spin.setSuffix(" ms")
        vad_form.addRow(tr("silence_threshold"), self.silence_threshold_spin)
        self.min_speech_spin = QSpinBox()
        self.min_speech_spin.setRange(100, 5000)
        self.min_speech_spin.setSuffix(" ms")
        vad_form.addRow(tr("min_speech"), self.min_speech_spin)
        self.max_speech_spin = QSpinBox()
        self.max_speech_spin.setRange(2000, 60000)
        self.max_speech_spin.setSuffix(" ms")
        vad_form.addRow(tr("max_speech"), self.max_speech_spin)
        form.addRow(vad_group)

        # 过滤词
        self.filter_filler_cb = QCheckBox("启用语气词过滤（嗯/啊/哎等）")
        self.filter_filler_cb.setChecked(self.config.get("filter_filler_words", False))
        form.addRow(self.filter_filler_cb)
        # ===== VRC 风格降噪区域 =====
        noise_group = QGroupBox("降噪与麦克风")
        noise_layout = QVBoxLayout(noise_group)

        # 降噪开关
        self.noise_reduction_cb = QCheckBox("启用 AI 降噪")
        self.noise_reduction_cb.setToolTip("启用后对麦克风和电脑声音采集的音频进行降噪，过滤环境噪音、键盘声等")
        self.noise_reduction_cb.setChecked(self.config.get("enable_noise_reduction", False))
        noise_layout.addWidget(self.noise_reduction_cb)

        # 降噪强度：低/中/高/自定义四档
        strength_layout = QHBoxLayout()
        strength_label = QLabel("降噪强度：")
        self.noise_strength_combo = QComboBox()
        self.noise_strength_combo.addItem("低（轻微降噪，保留更多细节）", 0.3)
        self.noise_strength_combo.addItem("中（平衡降噪，推荐）", 0.5)
        self.noise_strength_combo.addItem("高（强力降噪，可能损失部分人声）", 0.8)
        self.noise_strength_combo.addItem("自定义", -1)
        self.noise_strength_combo.setMinimumHeight(28)
        # 设置当前值
        current_strength = self.config.get("noise_reduction_strength", 0.5)
        strength_idx = 1  # 默认中
        for i in range(self.noise_strength_combo.count()):
            if abs(self.noise_strength_combo.itemData(i) - current_strength) < 0.01:
                strength_idx = i
                break
        else:
            strength_idx = 3  # 自定义
        self.noise_strength_combo.setCurrentIndex(strength_idx)
        strength_layout.addWidget(strength_label)
        strength_layout.addWidget(self.noise_strength_combo, 1)
        noise_layout.addLayout(strength_layout)

        # 自定义强度滑块（选"自定义"时显示）
        self.custom_strength_layout = QHBoxLayout()
        custom_label = QLabel("自定义强度：")
        self.noise_strength_slider = QSlider(Qt.Horizontal)
        self.noise_strength_slider.setRange(0, 100)
        self.noise_strength_slider.setValue(int(current_strength * 100))
        self.noise_strength_value = QLabel(f"{int(current_strength * 100)}%")
        self.noise_strength_slider.valueChanged.connect(
            lambda v: self.noise_strength_value.setText(f"{v}%")
        )
        self.custom_strength_layout.addWidget(custom_label)
        self.custom_strength_layout.addWidget(self.noise_strength_slider, 1)
        self.custom_strength_layout.addWidget(self.noise_strength_value)
        # 包装成 widget 方便显示/隐藏
        self.custom_strength_widget = QWidget()
        self.custom_strength_widget.setLayout(self.custom_strength_layout)
        self.custom_strength_widget.setVisible(strength_idx == 3)
        noise_layout.addWidget(self.custom_strength_widget)

        # 档位切换时显示/隐藏自定义滑块
        def _on_strength_changed(idx):
            self.custom_strength_widget.setVisible(idx == 3)
        self.noise_strength_combo.currentIndexChanged.connect(_on_strength_changed)

        # 降噪对象说明
        noise_hint = QLabel("降噪同时作用于麦克风和电脑声音两路采集，双向模式下两路都会降噪。")
        noise_hint.setStyleSheet("color: gray; font-size: 11px;")
        noise_hint.setWordWrap(True)
        noise_layout.addWidget(noise_hint)

        # 麦克风启动阈值 + 实时音量（组合在一起，滑块位置对应音量条阈值线）
        # 阈值滑块（在音量条上方，拖动时位置对应音量条上的阈值位置）
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("启动阈值：")
        threshold_label.setMinimumWidth(80)
        threshold_label.setToolTip("拖动滑块设置麦克风触发阈值，滑块位置对应下方音量条的阈值线")
        self.mic_threshold_slider = QSlider(Qt.Horizontal)
        self.mic_threshold_slider.setRange(1, 100)
        self.mic_threshold_slider.setValue(int(self.config.get("mic_activation_threshold", 0.02) * 1000))
        self.mic_threshold_value = QLabel(f"{int(self.config.get('mic_activation_threshold', 0.02) * 1000)}%")
        self.mic_threshold_value.setMinimumWidth(50)
        self.mic_threshold_slider.valueChanged.connect(
            lambda v: self.mic_threshold_value.setText(f"{v}%")
        )
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.mic_threshold_slider, 1)
        threshold_layout.addWidget(self.mic_threshold_value)
        noise_layout.addLayout(threshold_layout)

        # 实时音量指示器（VRC 风格，说话时有反应）
        volume_layout = QHBoxLayout()
        volume_label = QLabel("当前音量：")
        volume_label.setMinimumWidth(80)
        self.volume_meter = QProgressBar()
        self.volume_meter.setRange(0, 100)
        self.volume_meter.setValue(0)
        self.volume_meter.setTextVisible(True)
        self.volume_meter.setFormat("%v%")
        self.volume_meter.setMinimumHeight(24)
        self.volume_meter.setMinimumWidth(200)
        # 用内联样式确保不被主题覆盖，颜色明显
        self.volume_meter.setStyleSheet(
            "QProgressBar { border: 1px solid #555; border-radius: 4px; "
            "background-color: #1a1a1a; text-align: center; color: #fff; font-size: 11px; }"
            "QProgressBar::chunk { border-radius: 3px; "
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, "
            "stop:0 #4CAF50, stop:0.6 #FFC107, stop:1 #F44336); }"
        )
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_meter, 1)
        noise_layout.addLayout(volume_layout)

        # 音量提示
        volume_hint = QLabel("上方滑块设置触发阈值，下方音量条显示当前音量。音量超过阈值位置时触发识别。")
        volume_hint.setStyleSheet("color: gray; font-size: 11px;")
        volume_hint.setWordWrap(True)
        noise_layout.addWidget(volume_hint)

        form.addRow(noise_group)

        # 启动音量指示器定时器
        if self.recognizer is not None:
            self._volume_timer = QTimer(self)
            self._volume_timer.timeout.connect(self._update_volume_meter)
            self._volume_timer.start(50)  # 20fps 更新
        self.filter_words_edit = QTextEdit()
        self.filter_words_edit.setPlaceholderText(tr("filter_hint"))
        self.filter_words_edit.setMaximumHeight(80)
        form.addRow(tr("filter_words"), self.filter_words_edit)

        return w

    # ========== 同声传译 Tab ==========
    def _build_simul_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        # 总开关
        self.simul_enabled_cb = QCheckBox("启用同声传译")
        self.simul_enabled_cb.setToolTip("开启后：别人说的话翻译后朗读到你的耳机，你说的话翻译后输出到虚拟音频线（VRChat里用翻译语音说话）")
        layout.addWidget(self.simul_enabled_cb)

        # 入站设置（别人说话 → 翻译 → 朗读到耳机）
        inbound_group = QGroupBox("入站（听别人说话的翻译）")
        inbound_form = QFormLayout(inbound_group)
        self.simul_inbound_tts_cb = QCheckBox("启用入站 TTS 朗读")
        self.simul_inbound_tts_cb.setToolTip("别人说的话翻译后，用 TTS 朗读到你的耳机/扬声器")
        inbound_form.addRow(self.simul_inbound_tts_cb)
        # 入站输出设备
        inbound_device_row = QHBoxLayout()
        self.simul_inbound_device_combo = QComboBox()
        self.simul_inbound_device_combo.setMinimumHeight(28)
        self.simul_inbound_device_combo.setToolTip("入站翻译朗读的输出设备，留空=系统默认扬声器/耳机")
        inbound_device_row.addWidget(self.simul_inbound_device_combo, 1)
        inbound_refresh_btn = QPushButton("刷新")
        inbound_refresh_btn.setFixedWidth(60)
        inbound_refresh_btn.clicked.connect(self._refresh_simul_devices)
        inbound_device_row.addWidget(inbound_refresh_btn)
        inbound_test_btn = QPushButton("测试")
        inbound_test_btn.setFixedWidth(60)
        inbound_test_btn.clicked.connect(lambda: self._test_simul_tts("inbound"))
        inbound_device_row.addWidget(inbound_test_btn)
        inbound_form.addRow("输出设备：", inbound_device_row)
        layout.addWidget(inbound_group)

        # 出站设置（你说话 → 翻译 → 输出到虚拟音频线）
        outbound_group = QGroupBox("出站（你说的话翻译后在 VRChat 里说话）")
        outbound_form = QFormLayout(outbound_group)
        self.simul_outbound_tts_cb = QCheckBox("启用出站 TTS 输出")
        self.simul_outbound_tts_cb.setToolTip("你说的话翻译后，用 TTS 输出到虚拟音频线，VRChat 麦克风选择虚拟音频线就能用翻译后的语音说话")
        outbound_form.addRow(self.simul_outbound_tts_cb)
        # 出站输出设备
        outbound_device_row = QHBoxLayout()
        self.simul_outbound_device_combo = QComboBox()
        self.simul_outbound_device_combo.setMinimumHeight(28)
        self.simul_outbound_device_combo.setToolTip("出站翻译的输出设备，应选择虚拟音频线（如 CABLE Input）")
        outbound_device_row.addWidget(self.simul_outbound_device_combo, 1)
        outbound_refresh_btn = QPushButton("刷新")
        outbound_refresh_btn.setFixedWidth(60)
        outbound_refresh_btn.clicked.connect(self._refresh_simul_devices)
        outbound_device_row.addWidget(outbound_refresh_btn)
        outbound_test_btn = QPushButton("测试")
        outbound_test_btn.setFixedWidth(60)
        outbound_test_btn.clicked.connect(lambda: self._test_simul_tts("outbound"))
        outbound_device_row.addWidget(outbound_test_btn)
        outbound_form.addRow("输出设备：", outbound_device_row)
        # 麦克风直通
        self.simul_mic_passthrough_cb = QCheckBox("麦克风原始声音直通（Text Only 模式）")
        self.simul_mic_passthrough_cb.setToolTip("开启后，你的原始麦克风声音也同时输出到虚拟音频线，翻译文字通过 OSC 发送到聊天框。适合不想用 TTS 语音、只想发文字的场景")
        outbound_form.addRow(self.simul_mic_passthrough_cb)
        layout.addWidget(outbound_group)

        # 虚拟音频线引导
        vcab_group = QGroupBox("虚拟音频线设置")
        vcab_layout = QVBoxLayout(vcab_group)
        vcab_hint = QLabel("出站同声传译需要虚拟音频线把 TTS 音频喂给 VRChat。\n推荐安装 VB-CABLE（免费，几 MB），安装后在 VRChat 麦克风选择「CABLE Output」。")
        vcab_hint.setStyleSheet("color: gray; font-size: 11px;")
        vcab_hint.setWordWrap(True)
        vcab_layout.addWidget(vcab_hint)
        vcab_btn_row = QHBoxLayout()
        detect_btn = QPushButton("检测虚拟音频线")
        detect_btn.clicked.connect(self._detect_virtual_cable)
        vcab_btn_row.addWidget(detect_btn)
        install_btn = QPushButton("下载 VB-CABLE（免费）")
        install_btn.setToolTip("打开 VB-Audio 官网下载页面，下载后右键以管理员身份运行安装")
        install_btn.clicked.connect(self._open_vbcable_download)
        vcab_btn_row.addWidget(install_btn)
        vcab_layout.addLayout(vcab_btn_row)
        self.vcab_status_label = QLabel("点击「检测虚拟音频线」查看状态")
        self.vcab_status_label.setStyleSheet("color: gray; font-size: 11px;")
        self.vcab_status_label.setWordWrap(True)
        vcab_layout.addWidget(self.vcab_status_label)
        layout.addWidget(vcab_group)

        # TTS 朗读扩展
        tts_ext_group = QGroupBox("TTS 朗读扩展")
        tts_ext_form = QFormLayout(tts_ext_group)
        self.tts_read_mic_result_cb = QCheckBox("麦克风识别结果朗读（跟读/确认）")
        self.tts_read_mic_result_cb.setToolTip("麦克风识别到你说的话后，用 TTS 朗读出来，方便确认识别是否正确")
        tts_ext_form.addRow(self.tts_read_mic_result_cb)
        self.tts_read_manual_input_cb = QCheckBox("手动输入后自动朗读")
        self.tts_read_manual_input_cb.setToolTip("在手动输入框发送文字后，自动用 TTS 朗读")
        tts_ext_form.addRow(self.tts_read_manual_input_cb)
        layout.addWidget(tts_ext_group)

        layout.addStretch()
        # 初始化设备列表
        self._refresh_simul_devices()
        return w

    def _refresh_simul_devices(self):
        """刷新同声传译入站/出站输出设备列表"""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            # 入站设备
            self.simul_inbound_device_combo.clear()
            self.simul_inbound_device_combo.addItem("（系统默认扬声器/耳机）", "")
            # 出站设备
            self.simul_outbound_device_combo.clear()
            self.simul_outbound_device_combo.addItem("（请选择虚拟音频线）", "")
            for i, d in enumerate(devices):
                if d.get("max_output_channels", 0) > 0:
                    name = d.get("name", f"Device {i}")
                    label = f"[{i}] {name}"
                    self.simul_inbound_device_combo.addItem(label, i)
                    self.simul_outbound_device_combo.addItem(label, i)
            # 恢复已保存的设备
            inbound_saved = self.config.get("simul_inbound_tts_device", "")
            if inbound_saved != "":
                idx = self.simul_inbound_device_combo.findData(int(inbound_saved))
                if idx >= 0:
                    self.simul_inbound_device_combo.setCurrentIndex(idx)
            outbound_saved = self.config.get("simul_outbound_tts_device", "")
            if outbound_saved != "":
                idx = self.simul_outbound_device_combo.findData(int(outbound_saved))
                if idx >= 0:
                    self.simul_outbound_device_combo.setCurrentIndex(idx)
        except Exception as e:
            print(f"[Settings] 刷新同声传译设备失败: {e}")

    def _test_simul_tts(self, direction):
        """测试同声传译 TTS 输出"""
        try:
            import tts
            if direction == "inbound":
                device_data = self.simul_inbound_device_combo.currentData()
                text = "这是入站同声传译测试，别人说的话会翻译后朗读到这里。"
            else:
                device_data = self.simul_outbound_device_combo.currentData()
                text = "这是出站同声传译测试，你说的话会翻译后输出到虚拟音频线。"
            output_devices = [device_data] if device_data != "" else None
            engine = self.config.get("tts_engine", "pyttsx3")
            if engine == "edge":
                voice = self.config.get("tts_edge_voice", "zh-CN-XiaoxiaoNeural")
            elif engine == "volcengine":
                voice = self.config.get("tts_volc_voice", "BV001_streaming")
            else:
                voice = self.config.get("tts_voice", "") or None
            tts.speak(
                text, engine=engine, rate=self.config.get("tts_rate", 200),
                volume=self.config.get("tts_volume", 1.0), voice_id=voice,
                output_devices=output_devices,
                volc_appid=self.config.get("tts_volc_appid", ""),
                volc_token=self.config.get("tts_volc_token", ""),
                volc_pitch=self.config.get("tts_volc_pitch", 1.0),
            )
            QMessageBox.information(self, "测试", f"测试语音已发送，请在对应设备上听是否有声音。")
        except Exception as e:
            QMessageBox.warning(self, "测试失败", f"TTS 测试失败: {e}")

    def _detect_virtual_cable(self):
        """检测系统中是否有虚拟音频线"""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            found = []
            for i, d in enumerate(devices):
                name = d.get("name", "").lower()
                if "cable" in name or "virtual" in name or "vb-audio" in name:
                    found.append((i, d.get("name", "")))
            if found:
                msg = "检测到以下虚拟音频设备：\n\n"
                for idx, name in found:
                    msg += f"  [{idx}] {name}\n"
                msg += "\n建议在出站输出设备中选择 CABLE Input，然后在 VRChat 麦克风选择 CABLE Output。"
                self.vcab_status_label.setText(msg)
                self.vcab_status_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
            else:
                self.vcab_status_label.setText("未检测到虚拟音频线。请点击「下载 VB-CABLE」安装，安装后重启程序。")
                self.vcab_status_label.setStyleSheet("color: #FF9800; font-size: 11px;")
        except Exception as e:
            self.vcab_status_label.setText(f"检测失败: {e}")

    def _open_vbcable_download(self):
        """打开 VB-CABLE 下载页面"""
        try:
            from PyQt5.QtGui import QDesktopServices
            from PyQt5.QtCore import QUrl
            QDesktopServices.openUrl(QUrl("https://vb-audio.com/Cable/"))
        except Exception as e:
            QMessageBox.information(self, "VB-CABLE", "请手动访问 https://vb-audio.com/Cable/ 下载安装。")

    # ========== 外观 Tab ==========
    def _build_appearance_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        # 字体
        font_group = QGroupBox(tr("font_group"))
        font_layout = QVBoxLayout(font_group)
        self.font_btn = QPushButton(tr("choose_font"))
        self.font_btn.clicked.connect(self._choose_font)
        self.font_label = QLabel()
        font_row = QHBoxLayout()
        font_row.addWidget(self.font_btn)
        font_row.addWidget(self.font_label, 1)
        font_layout.addLayout(font_row)
        layout.addWidget(font_group)

        # 颜色
        color_group = QGroupBox(tr("color_group"))
        color_form = QFormLayout(color_group)
        self.original_color_btn = QPushButton()
        self.original_color_btn.clicked.connect(lambda: self._choose_color(self.original_color_btn))
        color_form.addRow(tr("original_color"), self.original_color_btn)
        self.translate_color_btn = QPushButton()
        self.translate_color_btn.clicked.connect(lambda: self._choose_color(self.translate_color_btn))
        color_form.addRow(tr("translate_color"), self.translate_color_btn)
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.clicked.connect(lambda: self._choose_color(self.bg_color_btn))
        color_form.addRow(tr("bg_color"), self.bg_color_btn)
        layout.addWidget(color_group)

        # 形状
        shape_group = QGroupBox(tr("shape_group"))
        shape_form = QFormLayout(shape_group)
        op_row = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_label = QLabel()
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(f"{v}%")
        )
        op_row.addWidget(self.opacity_slider)
        op_row.addWidget(self.opacity_label)
        op_widget = QWidget()
        op_widget.setLayout(op_row)
        shape_form.addRow(tr("bg_opacity_label"), op_widget)
        self.corner_spin = QSpinBox()
        self.corner_spin.setRange(0, 50)
        self.corner_spin.setSuffix(" px")
        shape_form.addRow(tr("corner_radius"), self.corner_spin)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(200, 2000)
        self.width_spin.setSuffix(" px")
        shape_form.addRow(tr("window_width"), self.width_spin)
        layout.addWidget(shape_group)

        # 显示
        display_group = QGroupBox(tr("display_group"))
        display_layout = QVBoxLayout(display_group)
        # 字幕显示模式下拉框
        mode_layout = QHBoxLayout()
        mode_label = QLabel("字幕显示模式：")
        self.subtitle_mode_combo = QComboBox()
        self.subtitle_mode_combo.addItem("同时显示原文和译文", "both")
        self.subtitle_mode_combo.addItem("仅显示原文（跳过AI翻译，省token）", "original_only")
        self.subtitle_mode_combo.addItem("仅显示译文", "translate_only")
        self.subtitle_mode_combo.setMinimumHeight(28)
        self.subtitle_mode_combo.setToolTip("选择仅显示原文时，不会调用AI翻译，节省API token")
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.subtitle_mode_combo, 1)
        display_layout.addLayout(mode_layout)
        # 显示/隐藏复选框（保留兼容，根据模式自动设置）
        self.show_original_cb = QCheckBox(tr("show_original"))
        self.show_translate_cb = QCheckBox(tr("show_translate"))
        display_layout.addWidget(self.show_original_cb)
        display_layout.addWidget(self.show_translate_cb)
        # 模式切换时自动设置复选框
        def _on_subtitle_mode_changed(idx):
            mode = self.subtitle_mode_combo.currentData()
            if mode == "both":
                self.show_original_cb.setChecked(True)
                self.show_translate_cb.setChecked(True)
            elif mode == "original_only":
                self.show_original_cb.setChecked(True)
                self.show_translate_cb.setChecked(False)
            elif mode == "translate_only":
                self.show_original_cb.setChecked(False)
                self.show_translate_cb.setChecked(True)
        self.subtitle_mode_combo.currentIndexChanged.connect(_on_subtitle_mode_changed)
        align_row = QHBoxLayout()
        align_row.addWidget(QLabel(tr("text_align")))
        self.align_combo = QComboBox()
        self.align_combo.setToolTip("字幕在窗口中的对齐方式：左对齐/居中/右对齐")
        self.align_combo.addItems([tr("align_center"), tr("align_left"), tr("align_right")])
        align_row.addWidget(self.align_combo)
        align_row.addStretch()
        display_layout.addLayout(align_row)
        layout.addWidget(display_group)

        # 文字描边/阴影
        effect_group = QGroupBox(tr("text_effect_group"))
        effect_form = QFormLayout(effect_group)
        self.text_stroke_cb = QCheckBox(tr("text_stroke_enabled"))
        effect_form.addRow(self.text_stroke_cb)
        self.text_stroke_color_btn = QPushButton()
        self.text_stroke_color_btn.clicked.connect(lambda: self._choose_color(self.text_stroke_color_btn))
        effect_form.addRow(tr("text_stroke_color"), self.text_stroke_color_btn)
        self.text_stroke_width_spin = QSpinBox()
        self.text_stroke_width_spin.setRange(1, 10)
        self.text_stroke_width_spin.setSuffix(" px")
        effect_form.addRow(tr("text_stroke_width"), self.text_stroke_width_spin)
        self.text_shadow_cb = QCheckBox(tr("text_shadow_enabled"))
        effect_form.addRow(self.text_shadow_cb)
        layout.addWidget(effect_group)

        # 其他窗口字体
        other_font_group = QGroupBox(tr("other_font_group"))
        other_font_layout = QFormLayout(other_font_group)
        self.history_font_spin = QSpinBox()
        self.history_font_spin.setRange(10, 32)
        self.history_font_spin.setSuffix(" px")
        other_font_layout.addRow(tr("history_font_size"), self.history_font_spin)
        self.ui_font_spin = QSpinBox()
        self.ui_font_spin.setRange(0, 20)
        self.ui_font_spin.setSuffix(" pt")
        self.ui_font_spin.setSpecialValueText(tr("system_default"))
        other_font_layout.addRow(tr("ui_font_size"), self.ui_font_spin)
        ui_hint = QLabel(tr("ui_font_hint"))
        ui_hint.setStyleSheet("color: gray; font-size: 10px;")
        other_font_layout.addRow(ui_hint)
        layout.addWidget(other_font_group)

        layout.addStretch()
        return w

    # ========== 其他 Tab ==========
    def _build_other_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        # TTS 朗读
        tts_group = QGroupBox(tr("tts_group"))
        tts_form = QFormLayout(tts_group)
        self.tts_enabled_cb = QCheckBox(tr("tts_enabled"))
        tts_form.addRow(self.tts_enabled_cb)
        self.tts_read_original_cb = QCheckBox(tr("tts_read_original"))
        tts_form.addRow(self.tts_read_original_cb)
        # TTS 引擎选择
        self.tts_engine_combo = QComboBox()
        self.tts_engine_combo.setMinimumHeight(28)
        self.tts_engine_combo.setToolTip("pyttsx3：离线系统语音\nedge-tts：联网微软语音，音色多\n火山引擎：联网豆包语音，自然可调")
        self.tts_engine_combo.addItem("pyttsx3", "pyttsx3")
        self.tts_engine_combo.addItem("edge-tts", "edge")
        self.tts_engine_combo.addItem("火山引擎（豆包）", "volcengine")
        self.tts_engine_combo.currentIndexChanged.connect(self._toggle_tts_engine)
        tts_form.addRow("TTS 引擎：", self.tts_engine_combo)

        # 火山引擎配置（默认隐藏，选择火山引擎时显示）
        self.tts_volc_widget = QWidget()
        volc_layout = QFormLayout(self.tts_volc_widget)
        volc_layout.setContentsMargins(0, 0, 0, 0)
        self.tts_volc_appid_edit = QLineEdit()
        self.tts_volc_appid_edit.setPlaceholderText("火山引擎 AppID")
        self.tts_volc_appid_edit.setEchoMode(QLineEdit.Password)
        volc_layout.addRow("AppID：", self.tts_volc_appid_edit)
        self.tts_volc_token_edit = QLineEdit()
        self.tts_volc_token_edit.setPlaceholderText("火山引擎 Access Token")
        self.tts_volc_token_edit.setEchoMode(QLineEdit.Password)
        volc_layout.addRow("Access Token：", self.tts_volc_token_edit)
        tts_form.addRow(self.tts_volc_widget)

        # 音色选择
        self.tts_voice_combo = QComboBox()
        self.tts_voice_combo.setMinimumHeight(28)
        self.tts_voice_combo.setToolTip("选择TTS朗读使用的音色")
        tts_form.addRow("语音音色：", self.tts_voice_combo)

        # 音调调节（火山引擎专用，默认隐藏）
        self.tts_pitch_widget = QWidget()
        pitch_layout = QHBoxLayout(self.tts_pitch_widget)
        pitch_layout.setContentsMargins(0, 0, 0, 0)
        pitch_layout.addWidget(QLabel("音调："))
        self.tts_pitch_slider = QSlider(Qt.Horizontal)
        self.tts_pitch_slider.setRange(50, 200)  # 0.5-2.0
        self.tts_pitch_label = QLabel("1.0")
        self.tts_pitch_slider.valueChanged.connect(
            lambda v: self.tts_pitch_label.setText(f"{v/100:.1f}")
        )
        pitch_layout.addWidget(self.tts_pitch_slider)
        pitch_layout.addWidget(self.tts_pitch_label)
        tts_form.addRow(self.tts_pitch_widget)
        # 输出设备选择
        self.tts_device_list = QListWidget()
        self.tts_device_list.setSelectionMode(QListWidget.MultiSelection)
        self.tts_device_list.setMaximumHeight(180)
        tts_form.addRow("输出设备（可多选，含虚拟音频线）：", self.tts_device_list)
        # 刷新设备按钮
        refresh_dev_btn = QPushButton("刷新设备列表")
        refresh_dev_btn.clicked.connect(self._refresh_tts_devices)
        tts_form.addRow(refresh_dev_btn)
        self.tts_rate_spin = QSpinBox()
        self.tts_rate_spin.setRange(50, 400)
        self.tts_rate_spin.setSuffix(" wpm")
        tts_form.addRow(tr("tts_rate"), self.tts_rate_spin)
        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel(tr("tts_volume")))
        self.tts_volume_slider = QSlider(Qt.Horizontal)
        self.tts_volume_slider.setRange(0, 100)
        self.tts_volume_label = QLabel()
        self.tts_volume_slider.valueChanged.connect(
            lambda v: self.tts_volume_label.setText(f"{v}%")
        )
        vol_row.addWidget(self.tts_volume_slider)
        vol_row.addWidget(self.tts_volume_label)
        vol_widget = QWidget()
        vol_widget.setLayout(vol_row)
        tts_form.addRow(vol_widget)
        layout.addWidget(tts_group)

        # 自动更新
        update_group = QGroupBox(tr("update_group"))
        update_layout = QVBoxLayout(update_group)
        self.check_update_cb = QCheckBox(tr("check_update_on_start"))
        update_layout.addWidget(self.check_update_cb)
        layout.addWidget(update_group)

        # 日志
        log_group = QGroupBox(tr("log_group"))
        log_layout = QVBoxLayout(log_group)
        log_hint = QLabel(tr("log_hint"))
        log_hint.setStyleSheet("color: gray; font-size: 11px;")
        log_hint.setWordWrap(True)
        log_layout.addWidget(log_hint)
        layout.addWidget(log_group)

        # 快捷键配置
        from PyQt5.QtWidgets import QKeySequenceEdit
        hotkey_group = QGroupBox("快捷键")
        hotkey_form = QFormLayout(hotkey_group)
        self.hotkey_subtitle = QKeySequenceEdit(self.config.get("hotkey_toggle_subtitle", "Ctrl+Alt+S"))
        hotkey_form.addRow("显示/隐藏字幕：", self.hotkey_subtitle)
        self.hotkey_history = QKeySequenceEdit(self.config.get("hotkey_toggle_history", "Ctrl+Alt+H"))
        hotkey_form.addRow("显示/隐藏历史记录：", self.hotkey_history)
        self.hotkey_ai_chat = QKeySequenceEdit(self.config.get("hotkey_toggle_ai_chat", "Ctrl+Alt+A"))
        hotkey_form.addRow("显示/隐藏AI代聊：", self.hotkey_ai_chat)
        hotkey_hint = QLabel("提示：快捷键在程序窗口获得焦点时生效，全局快捷键需要管理员权限。")
        hotkey_hint.setStyleSheet("color: gray; font-size: 10px;")
        hotkey_hint.setWordWrap(True)
        hotkey_form.addRow(hotkey_hint)
        layout.addWidget(hotkey_group)

        # 还原工具
        fix_group = QGroupBox("还原工具")
        fix_layout = QVBoxLayout(fix_group)
        fix_hint = QLabel("程序出问题时可以尝试以下操作：")
        fix_hint.setStyleSheet("color: gray; font-size: 11px;")
        fix_hint.setWordWrap(True)
        fix_layout.addWidget(fix_hint)

        # 一键修复
        oneclick_btn = QPushButton("一键修复")
        oneclick_btn.setToolTip("删除所有模型和配置，重新下载安装（相当于全新安装）")
        oneclick_btn.setStyleSheet("QPushButton { background-color: #c42b1c; color: white; font-weight: bold; }")
        oneclick_btn.clicked.connect(self._oneclick_repair)
        fix_layout.addWidget(oneclick_btn)
        oneclick_hint = QLabel("删除所有文件，重新下载")
        oneclick_hint.setStyleSheet("color: gray; font-size: 10px;")
        oneclick_hint.setAlignment(Qt.AlignCenter)
        fix_layout.addWidget(oneclick_hint)

        fix_btn_row = QHBoxLayout()
        repair_btn = QPushButton("重装依赖")
        repair_btn.setToolTip("重新安装所有依赖库（解决库损坏/缺失问题）")
        repair_btn.clicked.connect(self._repair_dependencies)
        fix_btn_row.addWidget(repair_btn)

        redownload_btn = QPushButton("重新下载模型")
        redownload_btn.setToolTip("删除当前模型并重新下载（解决模型损坏问题）")
        redownload_btn.clicked.connect(self._redownload_model)
        fix_btn_row.addWidget(redownload_btn)

        open_log_btn = QPushButton("打开日志文件夹")
        open_log_btn.setToolTip("打开日志文件所在目录")
        open_log_btn.clicked.connect(self._open_log_folder)
        fix_btn_row.addWidget(open_log_btn)

        fix_layout.addLayout(fix_btn_row)
        layout.addWidget(fix_group)

        layout.addStretch()
        return w

    # ========== 已下载模型列表 ==========
    def _refresh_downloaded_models(self):
        """刷新已下载模型列表"""
        import os
        from pathlib import Path

        if os.name == "nt":
            base = os.environ.get("APPDATA", str(Path.home()))
        else:
            base = str(Path.home() / ".config")
        models_dir = Path(base) / "vrc_trans" / "models"

        if not models_dir.exists():
            self.downloaded_models_edit.setText("（暂无已下载模型）")
            return

        lines = []
        for model_dir in sorted(models_dir.iterdir()):
            if model_dir.is_dir():
                # 计算目录总大小
                total_size = 0
                file_count = 0
                for f in model_dir.rglob("*"):
                    if f.is_file():
                        total_size += f.stat().st_size
                        file_count += 1
                size_mb = total_size / (1024 * 1024)
                lines.append(f"• {model_dir.name}  ({size_mb:.1f} MB, {file_count} 个文件)")

        if lines:
            self.downloaded_models_edit.setText("\n".join(lines))
        else:
            self.downloaded_models_edit.setText("（暂无已下载模型）")

    # ========== 音频设备刷新（自动检测默认麦克风） ==========
    def _refresh_devices(self):
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            self.device_computer_combo.clear()
            self.device_mic_combo.clear()
            input_device_indices = []
            for i, d in enumerate(devices):
                if d.get("max_input_channels", 0) > 0:
                    name = d.get("name", f"Device {i}")
                    label = f"{i}: {name}"
                    self.device_computer_combo.addItem(label, i)
                    self.device_mic_combo.addItem(label, i)
                    input_device_indices.append(i)

            # 获取系统默认输入设备
            default_input_idx = None
            try:
                default_input_idx = sd.default.device[0]
            except Exception:
                pass

            # 设置电脑声音设备：优先用配置，不存在则用默认输入设备
            comp_id = self.config.get("device_computer", None)
            comp_found = False
            if comp_id is not None:
                for i in range(self.device_computer_combo.count()):
                    if self.device_computer_combo.itemData(i) == comp_id:
                        self.device_computer_combo.setCurrentIndex(i)
                        comp_found = True
                        break
            if not comp_found and default_input_idx is not None and default_input_idx in input_device_indices:
                for i in range(self.device_computer_combo.count()):
                    if self.device_computer_combo.itemData(i) == default_input_idx:
                        self.device_computer_combo.setCurrentIndex(i)
                        break

            # 设置麦克风设备：优先用配置，不存在则自动选默认输入设备
            mic_id = self.config.get("device_mic", None)
            mic_found = False
            if mic_id is not None:
                for i in range(self.device_mic_combo.count()):
                    if self.device_mic_combo.itemData(i) == mic_id:
                        self.device_mic_combo.setCurrentIndex(i)
                        mic_found = True
                        break
            if not mic_found and default_input_idx is not None and default_input_idx in input_device_indices:
                for i in range(self.device_mic_combo.count()):
                    if self.device_mic_combo.itemData(i) == default_input_idx:
                        self.device_mic_combo.setCurrentIndex(i)
                        break
            elif not mic_found and self.device_mic_combo.count() > 0:
                self.device_mic_combo.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to list devices: {e}")

    def _choose_font(self):
        font, ok = QFontDialog.getFont(
            QFont(self.config.get("font_family"), self.config.get("font_size")),
            self, tr("choose_font")
        )
        if ok:
            self._selected_font = font
            self.font_label.setText(f"{font.family()} {font.pointSize()}pt")

    def _choose_color(self, btn):
        current = btn.property("color") or "#FFFFFF"
        color = QColorDialog.getColor(QColor(current), self, tr("bg_color"))
        if color.isValid():
            btn.setProperty("color", color.name())
            btn.setStyleSheet(f"background-color: {color.name()}; min-height: 24px;")
            btn.setText(color.name())

    # ========== 加载/保存 ==========
    def _load_values(self):
        c = self.config

        # 语言
        lang = c.get("language", "auto")
        lang_map = {"auto": 0, "zh": 1, "zh-tw": 2, "en": 3, "ja": 4, "ko": 5,
                    "fr": 6, "de": 7, "es": 8, "ru": 9, "pt": 10}
        self.lang_combo.setCurrentIndex(lang_map.get(lang, 0))

        # 翻译引擎
        engine = c.get("translate_engine", "deepseek")
        engine_map = {"deepseek": 0, "google": 1, "baidu": 2}
        self.translate_engine_combo.setCurrentIndex(engine_map.get(engine, 0))

        # AI 提供商
        provider = c.get("ai_provider", "deepseek")
        provider_map = {}
        for i in range(self.ai_provider_combo.count()):
            provider_map[self.ai_provider_combo.itemData(i)] = i
        self._current_ai_provider = provider
        self.ai_provider_combo.setCurrentIndex(provider_map.get(provider, 0))

        # AI 配置：优先从按提供商分开的字典里加载
        saved = self._load_provider_config(provider)
        self.ai_api_key_edit.setText(saved.get("api_key", c.get("ai_api_key", "")))
        self.ai_base_edit.setText(saved.get("api_base", c.get("ai_api_base", "")))
        self.ai_model_combo.setEditText(saved.get("model", c.get("ai_model", "")))
        self.ai_azure_endpoint_edit.setText(saved.get("azure_endpoint", c.get("ai_azure_endpoint", "")))
        self.ai_azure_deployment_edit.setText(saved.get("azure_deployment", c.get("ai_azure_deployment", "")))

        # 百度
        self.baidu_appid_edit.setText(c.get("baidu_appid", ""))
        self.baidu_secret_edit.setText(c.get("baidu_secret", ""))

        # 翻译通用
        self.target_combo.setCurrentText(c.get("target_lang", "中文"))
        self.prompt_edit.setText(c.get("custom_prompt", ""))
        self.enable_translate_cb.setChecked(c.get("enable_translate", True))

        # 触发一次显示切换
        self._on_translate_engine_changed(self.translate_engine_combo.currentIndex())
        self._on_ai_provider_changed(self.ai_provider_combo.currentIndex())

        # OSC
        self.enable_osc_cb.setChecked(c.get("enable_osc", True))
        self.osc_ip_edit.setText(c.get("osc_ip", "127.0.0.1"))
        self.osc_port_spin.setValue(c.get("osc_port", 9000))
        self.enable_auto_send_cb.setChecked(c.get("enable_auto_send", True))
        self.auto_send_delay_spin.setValue(c.get("auto_send_delay", 3.5))
        self.enable_auto_activate_cb.setChecked(c.get("enable_auto_activate", True))
        self.auto_activate_spin.setValue(c.get("auto_activate_interval", 4))
        self.enable_osc_bilingual_cb.setChecked(c.get("osc_bilingual", False))
        bi_fmt = c.get("osc_bilingual_format", "multiline")
        bi_fmt_map = {"multiline": 0, "parenthesis": 1, "slash": 2, "translate_only": 3}
        self.osc_bilingual_format_combo.setCurrentIndex(bi_fmt_map.get(bi_fmt, 0))
        bi_order = c.get("osc_bilingual_order", "original_first")
        bi_order_map = {"original_first": 0, "translate_first": 1}
        self.osc_bilingual_order_combo.setCurrentIndex(bi_order_map.get(bi_order, 0))
        self.enable_osc_typing_cb.setChecked(c.get("enable_osc_typing", True))

        # 语音
        self.enable_speech_cb.setChecked(c.get("enable_speech", True))
        self.dual_mode_cb.setChecked(c.get("dual_mode", False))
        self.enable_mic_to_osc_cb.setChecked(c.get("enable_mic_to_osc", True))
        self.mic_target_combo.setCurrentText(c.get("mic_target_lang", "日语"))
        self.enable_computer_to_subtitle_cb.setChecked(c.get("enable_computer_to_subtitle", True))
        self.computer_target_combo.setCurrentText(c.get("computer_target_lang", "中文"))

        # 双向模式：麦克风单独引擎/模型
        mic_eng = c.get("mic_whisper_engine", "")
        mic_eng_idx = self.mic_engine_combo.findData(mic_eng)
        self.mic_engine_combo.setCurrentIndex(mic_eng_idx if mic_eng_idx >= 0 else 0)
        mic_model = c.get("mic_whisper_model", "small")
        mic_model_idx = self.mic_model_combo.findText(mic_model)
        self.mic_model_combo.setCurrentIndex(mic_model_idx if mic_model_idx >= 0 else 2)
        mic_sherpa = c.get("mic_sherpa_model_id", "")
        mic_sherpa_idx = self.mic_sherpa_model_combo.findData(mic_sherpa)
        self.mic_sherpa_model_combo.setCurrentIndex(mic_sherpa_idx if mic_sherpa_idx >= 0 else 0)
        self.mic_model_stack.setCurrentIndex(1 if mic_eng == "sherpa" else 0)

        # 双向模式：电脑声音单独引擎/模型
        comp_eng = c.get("computer_whisper_engine", "")
        comp_eng_idx = self.computer_engine_combo.findData(comp_eng)
        self.computer_engine_combo.setCurrentIndex(comp_eng_idx if comp_eng_idx >= 0 else 0)
        comp_model = c.get("computer_whisper_model", "small")
        comp_model_idx = self.computer_model_combo.findText(comp_model)
        self.computer_model_combo.setCurrentIndex(comp_model_idx if comp_model_idx >= 0 else 2)
        comp_sherpa = c.get("computer_sherpa_model_id", "")
        comp_sherpa_idx = self.computer_sherpa_model_combo.findData(comp_sherpa)
        self.computer_sherpa_model_combo.setCurrentIndex(comp_sherpa_idx if comp_sherpa_idx >= 0 else 0)
        self.computer_model_stack.setCurrentIndex(1 if comp_eng == "sherpa" else 0)

        self.single_show_subtitle_cb.setChecked(c.get("single_show_subtitle", True))
        self.single_send_osc_cb.setChecked(c.get("single_send_osc", True))
        self.source_combo.setCurrentIndex(
            0 if c.get("record_source", "computer") == "computer" else 1
        )

        # 音频设备
        self._refresh_devices()

        engine_sp = c.get("whisper_engine", "sherpa")
        engine_idx = self.engine_combo.findData(engine_sp)
        self.engine_combo.setCurrentIndex(engine_idx if engine_idx >= 0 else 1)
        self.model_combo_speech.setCurrentText(c.get("whisper_model", "small"))
        # Sherpa 模型选择
        sherpa_model_id = c.get("sherpa_model_id", "streaming-paraformer-bilingual-zh-en")
        sherpa_idx = self.sherpa_model_combo.findData(sherpa_model_id)
        if sherpa_idx >= 0:
            self.sherpa_model_combo.setCurrentIndex(sherpa_idx)
        # SenseVoice 语言
        sv_lang = c.get("sense_voice_language", "auto")
        sv_idx = self.sense_voice_lang_combo.findData(sv_lang)
        if sv_idx >= 0:
            self.sense_voice_lang_combo.setCurrentIndex(sv_idx)
        # 触发引擎切换显示
        self.engine_combo.currentIndexChanged.emit(self.engine_combo.currentIndex())
        self.device_combo.setCurrentText(c.get("whisper_device", "cpu"))
        compute = c.get("compute_type", "int8")
        compute_map = {"int8": 0, "float16": 1, "float32": 2}
        self.compute_combo.setCurrentIndex(compute_map.get(compute, 0))
        self.vad_aggressive_spin.setValue(c.get("vad_aggressiveness", 2))
        self.silence_threshold_spin.setValue(c.get("silence_threshold", 250))
        self.min_speech_spin.setValue(c.get("min_speech_duration", 300))
        self.max_speech_spin.setValue(c.get("max_speech_duration", 15000))
        words = c.get("filter_words", ["嗯", "啊", "呃", "哦", "唉", "唔"])
        self.filter_words_edit.setPlainText("\n".join(words))

        # 外观
        self._selected_font = QFont(c.get("font_family", "微软雅黑"), c.get("font_size", 18))
        self.font_label.setText(f"{self._selected_font.family()} {self._selected_font.pointSize()}pt")
        self._set_color_btn(self.original_color_btn, c.get("original_color", "#87CEEB"))
        self._set_color_btn(self.translate_color_btn, c.get("translate_color", "#FFB6C1"))
        self._set_color_btn(self.bg_color_btn, c.get("bg_color", "#000000"))
        opacity = int(c.get("bg_opacity", 0.4) * 100)
        self.opacity_slider.setValue(opacity)
        self.opacity_label.setText(f"{opacity}%")
        self.corner_spin.setValue(c.get("corner_radius", 10))
        self.width_spin.setValue(c.get("window_width", 500))
        align = c.get("text_alignment", "center")
        align_map = {"center": 0, "left": 1, "right": 2}
        self.align_combo.setCurrentIndex(align_map.get(align, 0))
        self.show_original_cb.setChecked(c.get("show_original", True))
        self.show_translate_cb.setChecked(c.get("show_translate", True))
        # 字幕显示模式
        display_mode = c.get("subtitle_display_mode", "both")
        mode_idx = self.subtitle_mode_combo.findData(display_mode)
        self.subtitle_mode_combo.setCurrentIndex(mode_idx if mode_idx >= 0 else 0)

        # 文字效果
        self.text_stroke_cb.setChecked(c.get("text_stroke_enabled", False))
        self._set_color_btn(self.text_stroke_color_btn, c.get("text_stroke_color", "#000000"))
        self.text_stroke_width_spin.setValue(c.get("text_stroke_width", 2))
        self.text_shadow_cb.setChecked(c.get("text_shadow_enabled", False))

        # 其他字体
        self.history_font_spin.setValue(c.get("history_font_size", 14))
        self.ui_font_spin.setValue(c.get("ui_font_size", 0))

        # TTS
        self.tts_enabled_cb.setChecked(c.get("tts_enabled", False))
        self.tts_read_original_cb.setChecked(c.get("tts_read_original", False))
        self.tts_rate_spin.setValue(c.get("tts_rate", 200))
        self.tts_volume_slider.setValue(int(c.get("tts_volume", 1.0) * 100))
        self.tts_volume_label.setText(f"{int(c.get('tts_volume', 1.0) * 100)}%")
        # TTS 引擎
        engine = c.get("tts_engine", "pyttsx3")
        idx = self.tts_engine_combo.findData(engine)
        if idx >= 0:
            self.tts_engine_combo.setCurrentIndex(idx)
        self._toggle_tts_engine()
        # 音色
        if engine == "edge":
            edge_voice = c.get("tts_edge_voice", "zh-CN-XiaoxiaoNeural")
            idx = self.tts_voice_combo.findData(edge_voice)
            if idx >= 0:
                self.tts_voice_combo.setCurrentIndex(idx)
        elif engine == "volcengine":
            volc_voice = c.get("tts_volc_voice", "BV001_streaming")
            idx = self.tts_voice_combo.findData(volc_voice)
            if idx >= 0:
                self.tts_voice_combo.setCurrentIndex(idx)
        # 火山引擎配置
        self.tts_volc_appid_edit.setText(c.get("tts_volc_appid", ""))
        self.tts_volc_token_edit.setText(c.get("tts_volc_token", ""))
        # 音调
        pitch = c.get("tts_volc_pitch", 1.0)
        self.tts_pitch_slider.setValue(int(pitch * 100))
        self.tts_pitch_label.setText(f"{pitch:.1f}")
        # 输出设备
        self._refresh_tts_devices()
        import json
        devices_str = c.get("tts_output_devices", "")
        if devices_str:
            try:
                saved_devices = json.loads(devices_str)
                for i in range(self.tts_device_list.count()):
                    dev_id = self.tts_device_list.item(i).data(Qt.UserRole)
                    if dev_id in saved_devices:
                        self.tts_device_list.item(i).setSelected(True)
            except Exception:
                pass
        else:
            # 首次运行：自动选中系统默认输出设备（扬声器）
            try:
                import sounddevice as sd
                default_output_idx = sd.default.device[1]
                for i in range(self.tts_device_list.count()):
                    dev_id = self.tts_device_list.item(i).data(Qt.UserRole)
                    if dev_id == default_output_idx:
                        self.tts_device_list.item(i).setSelected(True)
                        break
            except Exception:
                # 失败则选第一个输出设备
                if self.tts_device_list.count() > 0:
                    self.tts_device_list.item(0).setSelected(True)

        # 同声传译
        self.simul_enabled_cb.setChecked(c.get("simultaneous_interpretation_enabled", False))
        self.simul_inbound_tts_cb.setChecked(c.get("simul_inbound_tts_enabled", True))
        self.simul_outbound_tts_cb.setChecked(c.get("simul_outbound_tts_enabled", True))
        self.simul_mic_passthrough_cb.setChecked(c.get("simul_mic_passthrough", False))
        # TTS 朗读扩展
        self.tts_read_mic_result_cb.setChecked(c.get("tts_read_mic_result", False))
        self.tts_read_manual_input_cb.setChecked(c.get("tts_read_manual_input", False))

        # 更新
        self.check_update_cb.setChecked(c.get("check_update_on_start", True))

    def _set_color_btn(self, btn, color_hex):
        btn.setProperty("color", color_hex)
        btn.setStyleSheet(f"background-color: {color_hex}; min-height: 24px;")
        btn.setText(color_hex)

    def _toggle_tts_engine(self):
        """切换 TTS 引擎时显示/隐藏对应配置项和音色列表"""
        engine = self.tts_engine_combo.currentData()
        is_edge = (engine == "edge")
        is_volc = (engine == "volcengine")

        # 显示/隐藏火山引擎配置
        self.tts_volc_widget.setVisible(is_volc)
        # 显示/隐藏音调调节（仅火山引擎支持）
        self.tts_pitch_widget.setVisible(is_volc)

        # 音色列表
        self.tts_voice_combo.clear()
        if is_edge:
            try:
                from tts import get_edge_voices
                for voice_id, label in get_edge_voices():
                    self.tts_voice_combo.addItem(label, voice_id)
            except Exception:
                self.tts_voice_combo.addItem("晓晓（默认）", "zh-CN-XiaoxiaoNeural")
            self.tts_voice_combo.setEnabled(True)
        elif is_volc:
            try:
                from tts import get_voices
                for voice_id, label in get_voices("volcengine"):
                    self.tts_voice_combo.addItem(label, voice_id)
            except Exception:
                self.tts_voice_combo.addItem("通用女声（默认）", "BV001_streaming")
            self.tts_voice_combo.setEnabled(True)
        else:
            self.tts_voice_combo.addItem("系统默认语音", "")
            self.tts_voice_combo.setEnabled(False)

    def _refresh_tts_devices(self):
        """刷新音频输出设备列表"""
        self.tts_device_list.clear()
        try:
            from tts import get_output_devices
            from PyQt5.QtWidgets import QListWidgetItem
            for dev_id, dev_name in get_output_devices():
                item = QListWidgetItem(f"[{dev_id}] {dev_name}")
                item.setData(Qt.UserRole, dev_id)
                self.tts_device_list.addItem(item)
        except Exception as e:
            from PyQt5.QtWidgets import QListWidgetItem
            self.tts_device_list.addItem(QListWidgetItem(f"获取设备失败: {e}"))

    def _export_config(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, tr("config_export"),
            "vrc_trans_config.json",
            "JSON Files (*.json);;All Files (*)"
        )
        if filepath:
            if self.config.export_to_file(filepath):
                QMessageBox.information(self, tr("config_export"),
                                        tr("config_export_done") + "\n" + filepath)
            else:
                QMessageBox.warning(self, tr("config_export"), "Export failed!")

    def _import_config(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, tr("config_import"),
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if filepath:
            if self.config.import_from_file(filepath):
                QMessageBox.information(self, tr("config_import"),
                                        tr("config_import_done"))
                self._load_values()
            else:
                QMessageBox.warning(self, tr("config_import"), "Import failed! Invalid file.")

    def _reset_config(self):
        reply = QMessageBox.question(
            self, tr("config_reset"), tr("config_reset_confirm"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config.reset_to_default()
            self._load_values()
            QMessageBox.information(self, tr("config_reset"), "Done!")

    def _on_ok(self):
        c = self.config
        # 语言
        c.set("language", self.lang_combo.currentData())
        # 翻译引擎
        c.set("translate_engine", self.translate_engine_combo.currentData())
        # AI 配置
        current_provider = self.ai_provider_combo.currentData()
        c.set("ai_provider", current_provider)
        c.set("ai_api_key", self.ai_api_key_edit.text().strip())
        c.set("ai_api_base", self.ai_base_edit.text().strip())
        c.set("ai_model", self.ai_model_combo.currentText().strip())
        c.set("ai_azure_endpoint", self.ai_azure_endpoint_edit.text().strip())
        c.set("ai_azure_deployment", self.ai_azure_deployment_edit.text().strip())
        # 按提供商分开保存，切换时自动加载
        self._save_provider_config(current_provider)
        # 百度
        c.set("baidu_appid", self.baidu_appid_edit.text().strip())
        c.set("baidu_secret", self.baidu_secret_edit.text().strip())
        # 翻译通用
        c.set("target_lang", self.target_combo.currentText())
        c.set("custom_prompt", self.prompt_edit.text().strip())
        c.set("enable_translate", self.enable_translate_cb.isChecked())
        # 兼容旧键
        c.set("api_key", self.ai_api_key_edit.text().strip())
        c.set("api_base", self.ai_base_edit.text().strip() or "https://api.deepseek.com")
        c.set("model", self.ai_model_combo.currentText().strip() or "deepseek-v4-flash")

        # OSC
        c.set("enable_osc", self.enable_osc_cb.isChecked())
        c.set("osc_ip", self.osc_ip_edit.text().strip())
        c.set("osc_port", self.osc_port_spin.value())
        c.set("enable_auto_send", self.enable_auto_send_cb.isChecked())
        c.set("auto_send_delay", self.auto_send_delay_spin.value())
        c.set("enable_auto_activate", self.enable_auto_activate_cb.isChecked())
        c.set("auto_activate_interval", self.auto_activate_spin.value())
        c.set("osc_bilingual", self.enable_osc_bilingual_cb.isChecked())
        bi_fmt_rev = {0: "multiline", 1: "parenthesis", 2: "slash", 3: "translate_only"}
        c.set("osc_bilingual_format", bi_fmt_rev.get(self.osc_bilingual_format_combo.currentIndex(), "multiline"))
        bi_order_rev = {0: "original_first", 1: "translate_first"}
        c.set("osc_bilingual_order", bi_order_rev.get(self.osc_bilingual_order_combo.currentIndex(), "original_first"))
        c.set("enable_osc_typing", self.enable_osc_typing_cb.isChecked())

        # 语音
        c.set("enable_speech", self.enable_speech_cb.isChecked())
        c.set("dual_mode", self.dual_mode_cb.isChecked())
        c.set("enable_mic_to_osc", self.enable_mic_to_osc_cb.isChecked())
        c.set("mic_target_lang", self.mic_target_combo.currentText())
        c.set("enable_computer_to_subtitle", self.enable_computer_to_subtitle_cb.isChecked())
        c.set("computer_target_lang", self.computer_target_combo.currentText())
        # 双向模式：保存麦克风/电脑声音单独引擎/模型
        c.set("mic_whisper_engine", self.mic_engine_combo.currentData() or "")
        c.set("mic_whisper_model", self.mic_model_combo.currentText())
        c.set("mic_sherpa_model_id", self.mic_sherpa_model_combo.currentData() or "")
        c.set("computer_whisper_engine", self.computer_engine_combo.currentData() or "")
        c.set("computer_whisper_model", self.computer_model_combo.currentText())
        c.set("computer_sherpa_model_id", self.computer_sherpa_model_combo.currentData() or "")
        c.set("single_show_subtitle", self.single_show_subtitle_cb.isChecked())
        c.set("single_send_osc", self.single_send_osc_cb.isChecked())
        c.set("record_source", self.source_combo.currentData())
        c.set("device_computer", self.device_computer_combo.currentData() or 2)
        c.set("device_mic", self.device_mic_combo.currentData() or 1)
        c.set("whisper_engine", self.engine_combo.currentData() or "sherpa")
        c.set("whisper_model", self.model_combo_speech.currentText())
        c.set("sherpa_model_id", self.sherpa_model_combo.currentData() or "streaming-paraformer-bilingual-zh-en")
        c.set("sense_voice_language", self.sense_voice_lang_combo.currentData() or "auto")
        c.set("whisper_device", self.device_combo.currentText())
        compute_map = {0: "int8", 1: "float16", 2: "float32"}
        c.set("compute_type", compute_map.get(self.compute_combo.currentIndex(), "int8"))
        c.set("vad_aggressiveness", self.vad_aggressive_spin.value())
        c.set("silence_threshold", self.silence_threshold_spin.value())
        c.set("min_speech_duration", self.min_speech_spin.value())
        c.set("max_speech_duration", self.max_speech_spin.value())
        words_text = self.filter_words_edit.toPlainText().strip()
        words = [w.strip() for w in words_text.split("\n") if w.strip()]
        c.set("filter_filler_words", self.filter_filler_cb.isChecked())
        c.set("enable_noise_reduction", self.noise_reduction_cb.isChecked())
        # 降噪强度：下拉框选低/中/高用预设值，自定义用滑块
        strength_data = self.noise_strength_combo.currentData()
        if strength_data == -1:
            c.set("noise_reduction_strength", self.noise_strength_slider.value() / 100.0)
        else:
            c.set("noise_reduction_strength", strength_data)
        c.set("mic_activation_threshold", self.mic_threshold_slider.value() / 1000.0)
        c.set("filter_words", words if words else ["嗯", "啊", "呃", "哦"])

        # 外观
        if hasattr(self, "_selected_font"):
            c.set("font_family", self._selected_font.family())
            c.set("font_size", self._selected_font.pointSize())
        c.set("original_color", self.original_color_btn.property("color") or "#87CEEB")
        c.set("translate_color", self.translate_color_btn.property("color") or "#FFB6C1")
        c.set("bg_color", self.bg_color_btn.property("color") or "#000000")
        c.set("bg_opacity", self.opacity_slider.value() / 100.0)
        c.set("corner_radius", self.corner_spin.value())
        c.set("window_width", self.width_spin.value())
        align_map = {0: "center", 1: "left", 2: "right"}
        c.set("text_alignment", align_map.get(self.align_combo.currentIndex(), "center"))
        c.set("show_original", self.show_original_cb.isChecked())
        c.set("show_translate", self.show_translate_cb.isChecked())
        c.set("subtitle_display_mode", self.subtitle_mode_combo.currentData())

        # 文字效果
        c.set("text_stroke_enabled", self.text_stroke_cb.isChecked())
        c.set("text_stroke_color", self.text_stroke_color_btn.property("color") or "#000000")
        c.set("text_stroke_width", self.text_stroke_width_spin.value())
        c.set("text_shadow_enabled", self.text_shadow_cb.isChecked())

        # 其他字体
        c.set("history_font_size", self.history_font_spin.value())
        c.set("ui_font_size", self.ui_font_spin.value())

        # TTS
        c.set("tts_enabled", self.tts_enabled_cb.isChecked())
        c.set("tts_read_original", self.tts_read_original_cb.isChecked())
        c.set("tts_rate", self.tts_rate_spin.value())
        c.set("tts_volume", self.tts_volume_slider.value() / 100.0)
        c.set("tts_engine", self.tts_engine_combo.currentData())
        # 保存音色（根据引擎）
        engine = self.tts_engine_combo.currentData()
        if engine == "edge":
            c.set("tts_edge_voice", self.tts_voice_combo.currentData() or "zh-CN-XiaoxiaoNeural")
        elif engine == "volcengine":
            c.set("tts_volc_voice", self.tts_voice_combo.currentData() or "BV001_streaming")
        # 火山引擎配置
        c.set("tts_volc_appid", self.tts_volc_appid_edit.text().strip())
        c.set("tts_volc_token", self.tts_volc_token_edit.text().strip())
        c.set("tts_volc_pitch", self.tts_pitch_slider.value() / 100.0)
        # 保存选中的输出设备
        import json
        selected_devices = []
        for item in self.tts_device_list.selectedItems():
            selected_devices.append(item.data(Qt.UserRole))
        c.set("tts_output_devices", json.dumps(selected_devices) if selected_devices else "")

        # 同声传译
        c.set("simultaneous_interpretation_enabled", self.simul_enabled_cb.isChecked())
        c.set("simul_inbound_tts_enabled", self.simul_inbound_tts_cb.isChecked())
        c.set("simul_outbound_tts_enabled", self.simul_outbound_tts_cb.isChecked())
        c.set("simul_mic_passthrough", self.simul_mic_passthrough_cb.isChecked())
        # 入站/出站输出设备
        inbound_dev = self.simul_inbound_device_combo.currentData()
        c.set("simul_inbound_tts_device", str(inbound_dev) if inbound_dev != "" else "")
        outbound_dev = self.simul_outbound_device_combo.currentData()
        c.set("simul_outbound_tts_device", str(outbound_dev) if outbound_dev != "" else "")
        # TTS 朗读扩展
        c.set("tts_read_mic_result", self.tts_read_mic_result_cb.isChecked())
        c.set("tts_read_manual_input", self.tts_read_manual_input_cb.isChecked())

        # 更新
        c.set("check_update_on_start", self.check_update_cb.isChecked())

        # 快捷键
        c.set("hotkey_toggle_subtitle", self.hotkey_subtitle.keySequence().toString())
        c.set("hotkey_toggle_history", self.hotkey_history.keySequence().toString())
        c.set("hotkey_toggle_ai_chat", self.hotkey_ai_chat.keySequence().toString())

        self.accept()

    # ========== 还原工具 ==========
    def _oneclick_repair(self):
        """一键修复：删除所有模型和配置，恢复全新状态"""
        from PyQt5.QtWidgets import QMessageBox
        import shutil
        import os
        from pathlib import Path

        reply = QMessageBox.warning(
            self, "一键修复",
            "⚠️ 确定要执行一键修复吗？\n\n"
            "这将删除：\n"
            "  • 所有已下载的语音模型\n"
            "  • 所有配置（API Key、设置等）\n\n"
            "删除后需要重新下载模型和配置，相当于全新安装。\n\n"
            "此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            # 删除模型目录
            if os.name == "nt":
                base = os.environ.get("APPDATA", str(Path.home()))
            else:
                base = str(Path.home() / ".config")
            app_dir = Path(base) / "vrc_trans"
            models_dir = app_dir / "models"

            if models_dir.exists():
                shutil.rmtree(models_dir, ignore_errors=True)

            # 重置配置
            from config import DEFAULT_CONFIG
            for key, value in DEFAULT_CONFIG.items():
                self.config.set(key, value)

            QMessageBox.information(
                self, "修复完成",
                "已删除所有模型和配置。\n\n"
                "点击确定后将自动重新下载模型（会显示下载进度窗口）。"
            )
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "修复失败", f"一键修复失败：{e}")

    def _repair_dependencies(self):
        """重新安装所有依赖库"""
        from PyQt5.QtWidgets import QMessageBox, QProgressDialog
        from PyQt5.QtCore import QThread, pyqtSignal
        import subprocess
        import sys
        import os

        # 检查是否是 EXE 模式（frozen）
        if getattr(sys, "frozen", False):
            QMessageBox.information(
                self, "修复依赖",
                "当前是 EXE 版本，所有依赖已打包在程序内，无需安装。\n\n"
                "如果程序异常，请尝试「重新下载模型」。"
            )
            return

        # 源码模式：重新安装依赖
        reply = QMessageBox.question(
            self, "修复依赖",
            "确定要重新安装所有依赖库吗？\n\n"
            "这将执行 pip install -r requirements.txt，可能需要几分钟。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 在后台线程执行 pip install
        class InstallThread(QThread):
            output = pyqtSignal(str)
            finished = pyqtSignal(bool, str)

            def run(self):
                try:
                    req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
                    proc = subprocess.Popen(
                        [sys.executable, "-m", "pip", "install", "-r", req_path],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, encoding="utf-8", errors="replace"
                    )
                    for line in proc.stdout:
                        self.output.emit(line.strip())
                    proc.wait()
                    self.finished.emit(proc.returncode == 0, f"退出码：{proc.returncode}")
                except Exception as e:
                    self.finished.emit(False, str(e))

        self._install_thread = InstallThread()
        self._install_thread.output.connect(lambda s: print(f"[pip] {s}"))
        self._install_thread.finished.connect(self._on_repair_done)
        self._install_thread.start()

        QMessageBox.information(
            self, "正在安装",
            "正在后台重新安装依赖库，请稍候...\n\n"
            "安装完成后会弹出提示，期间可以继续使用程序。"
        )

    def _on_repair_done(self, success, msg):
        """依赖安装完成回调"""
        from PyQt5.QtWidgets import QMessageBox
        if success:
            QMessageBox.information(self, "修复完成", "依赖库已重新安装。\n\n建议重启程序使变更生效。")
        else:
            QMessageBox.warning(self, "修复失败", f"依赖安装失败：{msg}\n\n请手动运行 pip install -r requirements.txt")

    def _redownload_model(self):
        """重新下载模型"""
        from PyQt5.QtWidgets import QMessageBox
        import shutil
        from pathlib import Path
        import os

        model_name = self.config.get("whisper_model", "small")
        if os.name == "nt":
            base = os.environ.get("APPDATA", str(Path.home()))
        else:
            base = str(Path.home() / ".config")
        model_dir = Path(base) / "vrc_trans" / "models" / model_name

        reply = QMessageBox.question(
            self, "重新下载模型",
            f"确定要删除当前模型（{model_name}）并重新下载吗？\n\n"
            f"模型目录：{model_dir}\n\n"
            "删除后需要重新下载（约460MB），请确保网络畅通。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if model_dir.exists():
                shutil.rmtree(model_dir, ignore_errors=True)
            QMessageBox.information(
                self, "已删除",
                f"模型已删除。\n\n请重启程序，程序会自动重新下载模型。"
            )
            self.accept()

    def _open_log_folder(self):
        """打开日志文件夹"""
        import os
        from pathlib import Path
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl

        if os.name == "nt":
            base = os.environ.get("APPDATA", str(Path.home()))
        else:
            base = str(Path.home() / ".config")
        log_dir = Path(base) / "vrc_trans"
        log_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(log_dir)))
