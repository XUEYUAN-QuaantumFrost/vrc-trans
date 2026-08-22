"""
配置管理模块
所有设置持久化到 %APPDATA%/vrc_trans/config.json
"""
import json
import os
from pathlib import Path


def get_config_dir() -> Path:
    """获取配置目录（Windows: %APPDATA%/vrc_trans）"""
    if os.name == "nt":
        base = os.environ.get("APPDATA", str(Path.home()))
    else:
        base = str(Path.home() / ".config")
    d = Path(base) / "vrc_trans"
    d.mkdir(parents=True, exist_ok=True)
    return d


CONFIG_PATH = get_config_dir() / "config.json"

# 默认配置
DEFAULT_CONFIG = {
    # ===== 翻译 API =====
    "language": "auto",         # auto / zh / en
    "translate_engine": "deepseek",  # deepseek(AI) / google / baidu
    "target_lang": "中文",
    "custom_prompt": "",
    "enable_translate": True,
    # 百度翻译
    "baidu_appid": "",
    "baidu_secret": "",
    # ===== 统一 AI 提供商配置（翻译 + AI代聊共用）=====
    # provider: deepseek / openai / azure / custom
    "ai_provider": "deepseek",
    "ai_api_key": "",
    "ai_api_base": "",          # 空=使用提供商默认地址
    "ai_model": "",             # 空=使用提供商默认模型
    # Azure OpenAI 专用
    "ai_azure_endpoint": "",
    "ai_azure_deployment": "",
    "ai_azure_api_version": "2024-02-15-preview",
    "ai_provider_configs": {},  # 按提供商分开存配置：{"deepseek": {"api_key":"", "api_base":"", "model":""}, ...}
    # ===== AI 代聊独立配置（全部留空=继承上面的全局配置）=====
    "aichat_provider": "",      # 空=继承全局
    "aichat_api_key": "",
    "aichat_api_base": "",
    "aichat_model": "",
    "aichat_azure_endpoint": "",
    "aichat_azure_deployment": "",
    # 旧版兼容键（已迁移到 ai_*，保留仅用于旧配置读取）
    "api_key": "",
    "api_base": "https://api.deepseek.com",
    "model": "deepseek-v4-flash",

    # ===== OSC =====
    "osc_ip": "127.0.0.1",
    "osc_port": 9000,
    "enable_osc": True,
    # OSC 双语发送
    "osc_bilingual": False,            # True=原文+翻译一起发送
    "osc_bilingual_format": "multiline",  # multiline / parenthesis / slash / translate_only
    "osc_bilingual_order": "original_first",  # original_first / translate_first
    "enable_osc_typing": True,         # 翻译时显示打字指示器

    # ===== 语音识别 =====
    "enable_speech": True,
    "record_source": "computer",   # "computer"=立体声混音 / "mic"=麦克风（单路模式用）
    "device_computer": 2,          # 立体声混音设备编号
    "device_mic": 1,               # 麦克风设备编号
    "whisper_model": "small",
    "whisper_engine": "sherpa",    # sherpa(中文更准) / faster(通用)
    "sherpa_model_id": "streaming-paraformer-bilingual-zh-en",  # sherpa-onnx 模型 ID
    "sense_voice_language": "auto",  # SenseVoice 语言: auto/zh/en/ja/ko/yue
    # 双向模式：麦克风单独配置（留空则用全局配置）
    "mic_whisper_engine": "",              # 麦克风识别引擎（sherpa/faster，留空用全局）
    "mic_whisper_model": "",               # 麦克风 faster-whisper 模型（留空用全局）
    "mic_sherpa_model_id": "",             # 麦克风 sherpa 模型 ID（留空用全局）
    # 双向模式：电脑声音单独配置（留空则用全局配置）
    "computer_whisper_engine": "",         # 电脑声音识别引擎（留空用全局）
    "computer_whisper_model": "",          # 电脑声音 faster-whisper 模型（留空用全局）
    "computer_sherpa_model_id": "",        # 电脑声音 sherpa 模型 ID（留空用全局）
    "custom_download_mirrors": [],  # 自定义 GitHub 下载镜像前缀列表，如 ["https://ghproxy.net/"]
    "whisper_device": "cpu",       # cpu / cuda
    "compute_type": "int8",        # int8 / float16 / float32
    "silence_threshold": 250,      # 静音多久算一句话结束（ms）
    "min_speech_duration": 300,    # 最短说话时长（ms）
    "max_speech_duration": 15000,  # 最长说话时长，超过强制切断（ms）
    "vad_aggressiveness": 2,       # VAD灵敏度 0-3，推荐2
    "filter_words": ["嗯", "啊", "呃", "哦", "唉", "唔"],
    # ===== 双向翻译模式 =====
    "dual_mode": False,             # True=双路同时运行，False=单路模式
    "enable_mic_to_osc": True,      # 麦克风→翻译→OSC聊天框
    "mic_target_lang": "英语",       # 麦克风翻译目标语言
    "enable_computer_to_subtitle": True,  # 电脑声音→翻译→悬浮字幕
    "computer_target_lang": "中文",   # 电脑声音翻译目标语言
    # ===== 单路模式输出设置 =====
    "single_show_subtitle": True,    # 单路模式：显示悬浮字幕
    "single_send_osc": True,         # 单路模式：发送OSC到聊天框

    # ===== 自动发送 =====
    "auto_send_delay": 0,        # 秒
    "enable_auto_send": True,
    "enable_auto_activate": True,
    "auto_activate_interval": 1,   # 秒

    # ===== 悬浮窗外观 =====
    "font_family": "微软雅黑",
    "font_size": 18,
    "original_color": "#87CEEB",   # 原文颜色（天蓝）
    "translate_color": "#FFB6C1",  # 翻译颜色（粉红）
    "bg_color": "#000000",
    "bg_opacity": 0.4,             # 0~1
    "corner_radius": 10,           # 圆角半径
    "text_alignment": "center",    # left / center / right
    "window_width": 500,
    "window_x": 100,
    "window_y": 100,
    "locked": False,
    "visible": True,
    "show_original": True,
    "show_translate": True,
    "subtitle_display_mode": "both",       # 字幕显示模式：both=同时显示, original_only=仅原文(跳过AI翻译省token), translate_only=仅译文
    # 文字描边/阴影
    "text_stroke_enabled": False,
    "text_stroke_color": "#000000",
    "text_stroke_width": 2,
    "text_shadow_enabled": False,
    "text_shadow_color": "#000000",
    "text_shadow_blur": 4,
    # ===== TTS 朗读 =====
    "tts_enabled": False,
    "tts_rate": 200,
    "tts_volume": 1.0,
    "tts_voice": "",
    "tts_read_original": False,   # True=朗读原文, False=朗读翻译
    "tts_engine": "pyttsx3",      # pyttsx3(离线) / edge(联网微软) / volcengine(火山引擎/豆包)
    "tts_edge_voice": "zh-CN-XiaoxiaoNeural",  # edge-tts 音色
    "tts_output_devices": "",     # 输出设备索引，JSON 数组字符串，如 "[0,2]"，空=系统默认
    # 火山引擎（豆包）TTS 配置
    "tts_volc_appid": "",         # 火山引擎 AppID
    "tts_volc_token": "",         # 火山引擎 Access Token
    "tts_volc_voice": "BV001_streaming",  # 火山引擎音色
    "tts_volc_pitch": 1.0,        # 音调 0.5-2.0
    # ===== 自动更新 =====
    "check_update_on_start": True,
    "tutorial_seen": False,        # 是否已看过新手引导
    # 快捷键配置
    "hotkey_toggle_subtitle": "Ctrl+Alt+S",   # 显示/隐藏字幕
    "hotkey_toggle_history": "Ctrl+Alt+H",    # 显示/隐藏历史记录
    "hotkey_toggle_ai_chat": "Ctrl+Alt+A",    # 显示/隐藏AI代聊
    "hotkey_toggle_history_lock": "Ctrl+Alt+L", # 锁定/解锁历史记录窗口
    "filter_filler_words": False,             # 是否过滤语气词（嗯/啊/哎等）
    "enable_noise_reduction": False,            # 是否启用实时降噪（noisereduce）
    "noise_reduction_strength": 0.5,             # 降噪强度 0.0-1.0（0.5=中等）
    "mic_activation_threshold": 0.02,            # 麦克风启动阈值（音量振幅 0.0-1.0）
    # ===== 历史记录窗口 =====
    "history_visible": False,          # 历史窗口是否显示
    "history_locked": False,           # 历史窗口是否锁定
    "history_save_to_file": False,     # 是否持久化到文件
    "history_max_items": 200,          # 内存中最大保留条数
    "history_window_x": 100,
    "history_window_y": 200,
    "history_window_width": 450,
    "history_window_height": 300,
    "history_font_size": 18,
    "ui_font_size": 0,               # 全局界面字体大小，0=系统默认
    # ===== 手动输入 =====
    "manual_input_mode": "both",     # both / osc_only / subtitle_only
    # ===== AI 代聊 =====
    "aichat_default_tone": "friendly",  # friendly / formal / humorous / shy / cool
    "aichat_default_target_lang": "",   # 空=继承麦克风目标语言
    "aichat_window_x": 300,
    "aichat_window_y": 300,
    "aichat_api_mode": "deepseek",      # deepseek / free
    "aichat_free_base": "https://api.siliconflow.cn/v1",
    "aichat_free_model": "deepseek-ai/DeepSeek-V2.5",
    "aichat_free_key": "",
    # AI 代聊增强
    "aichat_persona": "我是中国人，现居中国，使用中文和日语交流。性格友好开朗。",  # 人设/地区设定
    "aichat_auto_mode": False,       # 自动代聊模式（拾取语音自动回复）
    "aichat_bilingual": True,        # AI 回复双语输出
    "aichat_max_chars": 60,          # AI 回复最大字符数
    "aichat_silence_timeout": 1500,  # 语音停顿多久后自动发送（毫秒）
    "aichat_window_opacity": 0.92,   # 窗口透明度 0.5-1.0
    # ===== TTS 朗读扩展 =====
    "tts_read_mic_result": False,      # 麦克风识别结果 TTS 朗读（跟读/确认）
    "tts_read_manual_input": False,    # 手动输入文字后自动 TTS 朗读
    # ===== 同声传译模式 =====
    "simultaneous_interpretation_enabled": False,  # 同声传译总开关
    "simul_inbound_tts_enabled": True,    # 入站（别人说话）翻译后 TTS 朗读到耳机
    "simul_inbound_tts_device": "",       # 入站 TTS 输出设备索引，空=系统默认扬声器/耳机
    "simul_outbound_tts_enabled": True,   # 出站（你说话）翻译后 TTS 输出到虚拟音频线
    "simul_outbound_tts_device": "",      # 出站 TTS 输出设备索引（虚拟音频线，如 VB-Cable Input）
    "simul_mic_passthrough": False,       # 同声传译时麦克风原始声音是否也直通到虚拟线（Text Only 模式）

}


class Config:
    """配置单例"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = {}
            cls._instance.load()
        return cls._instance

    def load(self):
        """从文件加载配置"""
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}
        # 合并默认值（新增字段自动补全）
        for k, v in DEFAULT_CONFIG.items():
            if k not in self._data:
                self._data[k] = v

        # 旧配置迁移：api_key/api_base/model -> ai_api_key/ai_api_base/ai_model
        if not self._data.get("ai_api_key") and self._data.get("api_key"):
            self._data["ai_api_key"] = self._data["api_key"]
            self._data["ai_provider"] = "deepseek"
        if not self._data.get("ai_api_base") and self._data.get("api_base"):
            self._data["ai_api_base"] = self._data["api_base"]
        if not self._data.get("ai_model") and self._data.get("model"):
            self._data["ai_model"] = self._data["model"]

        # 旧版 aichat free 配置迁移
        if (not self._data.get("aichat_provider")
                and self._data.get("aichat_api_mode") == "free"
                and self._data.get("aichat_free_key")):
            self._data["aichat_provider"] = "custom"
            self._data["aichat_api_key"] = self._data.get("aichat_free_key", "")
            self._data["aichat_api_base"] = self._data.get("aichat_free_base", "")
            self._data["aichat_model"] = self._data.get("aichat_free_model", "")

        # 旧版 whisper 引擎迁移：openai -> faster（openai-whisper 依赖 torch，已弃用）
        if self._data.get("whisper_engine") == "openai":
            self._data["whisper_engine"] = "sherpa"

        # CPU 模式下 float16 不支持，自动改成 int8
        if (self._data.get("whisper_device") == "cpu"
                and self._data.get("compute_type") == "float16"):
            self._data["compute_type"] = "int8"

    def save(self):
        """保存到文件"""
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"[Config] 保存失败: {e}")

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    def get_all(self):
        return dict(self._data)

    def update(self, data: dict):
        self._data.update(data)
        self.save()

    def export_to_file(self, filepath: str) -> bool:
        """导出配置到指定文件"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            return True
        except OSError as e:
            print(f"[Config] 导出失败: {e}")
            return False

    def import_from_file(self, filepath: str) -> bool:
        """从文件导入配置（合并，不删除已有键）"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return False
            self._data.update(data)
            # 补全缺失的默认键
            for k, v in DEFAULT_CONFIG.items():
                if k not in self._data:
                    self._data[k] = v
            self.save()
            return True
        except (json.JSONDecodeError, OSError) as e:
            print(f"[Config] 导入失败: {e}")
            return False

    def reset_to_default(self):
        """恢复所有设置为默认值"""
        self._data = dict(DEFAULT_CONFIG)
        self.save()
