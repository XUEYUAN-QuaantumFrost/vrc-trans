"""
Sherpa-onnx 语音识别引擎（多模型支持）- V5 修复版
- 支持流式识别（OnlineRecognizer）和离线识别（OfflineRecognizer）
- 支持 Paraformer / Zipformer / SenseVoice 多种架构
- 模型运行时下载，不打进 EXE
- 统一接口，上层无需关心模型差异
- 增强：健壮的文件查找、SenseVoice 兼容、详细错误日志、模型完整性验证
"""
import os
import glob
import numpy as np
from typing import Optional, List, Dict, Tuple

# ============================================================
# 模型注册表
# ============================================================
# 每个模型的 file_patterns 是按优先级排序的候选文件名列表
# 查找时会依次尝试，找到第一个存在的即使用
MODEL_REGISTRY: List[Dict] = [
    # ---------- 流式模型（推荐，低延迟） ----------
    {
        "id": "streaming-paraformer-bilingual-zh-en",
        "name": "流式 Paraformer 中英双语（≈whisper small，推荐）",
        "type": "streaming",
        "architecture": "paraformer",
        "languages": ["zh", "en"],
        "size": 220,
        "tar_filename": "sherpa-onnx-streaming-paraformer-bilingual-zh-en.tar.bz2",
        "required_files": ["encoder.int8.onnx", "decoder.int8.onnx", "tokens.txt"],
        "file_patterns": {
            "encoder": ["encoder.int8.onnx", "encoder.onnx"],
            "decoder": ["decoder.int8.onnx", "decoder.onnx"],
            "tokens": ["tokens.txt"],
        },
        "description": "流式识别，边说边出结果，延迟极低。中英双语混合识别，VRChat 首选。",
        "recommended": True,
    },
    {
        "id": "streaming-paraformer-trilingual-zh-cantonese-en",
        "name": "流式 Paraformer 中粤英三语（≈whisper small）",
        "type": "streaming",
        "architecture": "paraformer",
        "languages": ["zh", "yue", "en"],
        "size": 230,
        "tar_filename": "sherpa-onnx-streaming-paraformer-trilingual-zh-cantonese-en.tar.bz2",
        "required_files": ["encoder.int8.onnx", "decoder.int8.onnx", "tokens.txt"],
        "file_patterns": {
            "encoder": ["encoder.int8.onnx", "encoder.onnx"],
            "decoder": ["decoder.int8.onnx", "decoder.onnx"],
            "tokens": ["tokens.txt"],
        },
        "description": "流式识别，支持中文、粤语、英语三语混合。适合有粤语朋友的场景。",
        "recommended": False,
    },
    {
        "id": "streaming-zipformer-bilingual-zh-en-2023-02-20",
        "name": "流式 Zipformer 中英双语（≈whisper medium）",
        "type": "streaming",
        "architecture": "zipformer",
        "languages": ["zh", "en"],
        "size": 380,
        "tar_filename": "sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20.tar.bz2",
        "required_files": ["encoder-epoch-99-avg-1.onnx", "decoder-epoch-99-avg-1.onnx",
                           "joiner-epoch-99-avg-1.onnx", "tokens.txt"],
        "file_patterns": {
            "encoder": ["encoder-epoch-99-avg-1.int8.onnx", "encoder-epoch-99-avg-1.onnx",
                        "encoder.int8.onnx", "encoder.onnx"],
            "decoder": ["decoder-epoch-99-avg-1.int8.onnx", "decoder-epoch-99-avg-1.onnx",
                        "decoder.int8.onnx", "decoder.onnx"],
            "joiner": ["joiner-epoch-99-avg-1.int8.onnx", "joiner-epoch-99-avg-1.onnx",
                       "joiner.int8.onnx", "joiner.onnx"],
            "tokens": ["tokens.txt"],
        },
        "description": "流式 Zipformer 架构，中英双语，准确率高但体积较大。",
        "recommended": False,
    },
    {
        "id": "streaming-zipformer-small-bilingual-zh-en-2023-02-16",
        "name": "流式 Zipformer 轻量中英双语（≈whisper small）",
        "type": "streaming",
        "architecture": "zipformer",
        "languages": ["zh", "en"],
        "size": 180,
        "tar_filename": "sherpa-onnx-streaming-zipformer-small-bilingual-zh-en-2023-02-16.tar.bz2",
        "required_files": ["encoder-epoch-99-avg-1.onnx", "decoder-epoch-99-avg-1.onnx",
                           "joiner-epoch-99-avg-1.onnx", "tokens.txt"],
        "file_patterns": {
            "encoder": ["encoder-epoch-99-avg-1.int8.onnx", "encoder-epoch-99-avg-1.onnx",
                        "encoder.int8.onnx", "encoder.onnx"],
            "decoder": ["decoder-epoch-99-avg-1.int8.onnx", "decoder-epoch-99-avg-1.onnx",
                        "decoder.int8.onnx", "decoder.onnx"],
            "joiner": ["joiner-epoch-99-avg-1.int8.onnx", "joiner-epoch-99-avg-1.onnx",
                       "joiner.int8.onnx", "joiner.onnx"],
            "tokens": ["tokens.txt"],
        },
        "description": "轻量版流式 Zipformer，中英双语，体积小速度快，适合低性能电脑。",
        "recommended": False,
    },
    {
        "id": "streaming-zipformer-zh-int8-2025-06-30",
        "name": "流式 Zipformer 中文 int8（≈whisper base）",
        "type": "streaming",
        "architecture": "zipformer",
        "languages": ["zh"],
        "size": 80,
        "tar_filename": "sherpa-onnx-streaming-zipformer-zh-int8-2025-06-30.tar.bz2",
        "required_files": ["encoder-epoch-99-avg-1.int8.onnx", "decoder-epoch-99-avg-1.int8.onnx",
                           "joiner-epoch-99-avg-1.int8.onnx", "tokens.txt"],
        "file_patterns": {
            "encoder": ["encoder-epoch-99-avg-1.int8.onnx", "encoder-epoch-99-avg-1.onnx",
                        "encoder.int8.onnx", "encoder.onnx"],
            "decoder": ["decoder-epoch-99-avg-1.int8.onnx", "decoder-epoch-99-avg-1.onnx",
                        "decoder.int8.onnx", "decoder.onnx"],
            "joiner": ["joiner-epoch-99-avg-1.int8.onnx", "joiner-epoch-99-avg-1.onnx",
                       "joiner.int8.onnx", "joiner.onnx"],
            "tokens": ["tokens.txt"],
        },
        "description": "2025年新版中文流式模型，int8 量化，体积小速度快。仅中文。",
        "recommended": False,
    },
    {
        "id": "streaming-zipformer-zh-14M-2023-02-23",
        "name": "流式 Zipformer 超轻量中文（≈whisper tiny）",
        "type": "streaming",
        "architecture": "zipformer",
        "languages": ["zh"],
        "size": 30,
        "tar_filename": "sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23.tar.bz2",
        "required_files": ["encoder-epoch-99-avg-1.onnx", "decoder-epoch-99-avg-1.onnx",
                           "joiner-epoch-99-avg-1.onnx", "tokens.txt"],
        "file_patterns": {
            "encoder": ["encoder-epoch-99-avg-1.int8.onnx", "encoder-epoch-99-avg-1.onnx",
                        "encoder.int8.onnx", "encoder.onnx"],
            "decoder": ["decoder-epoch-99-avg-1.int8.onnx", "decoder-epoch-99-avg-1.onnx",
                        "decoder.int8.onnx", "decoder.onnx"],
            "joiner": ["joiner-epoch-99-avg-1.int8.onnx", "joiner-epoch-99-avg-1.onnx",
                       "joiner.int8.onnx", "joiner.onnx"],
            "tokens": ["tokens.txt"],
        },
        "description": "超轻量中文流式模型，仅 14M 参数，适合非常弱的设备（如低配笔记本）。",
        "recommended": False,
    },
    # ---------- 离线模型（准确率高，但延迟高） ----------
    {
        "id": "paraformer-zh-2024-03-09",
        "name": "离线 Paraformer 中文（≈whisper small）",
        "type": "offline",
        "architecture": "paraformer",
        "languages": ["zh", "en"],
        "size": 220,
        "tar_filename": "sherpa-onnx-paraformer-zh-2024-03-09.tar.bz2",
        "required_files": ["model.int8.onnx", "tokens.txt"],
        "file_patterns": {
            "model": ["model.int8.onnx", "model.onnx"],
            "tokens": ["tokens.txt"],
        },
        "description": "2024年新版离线 Paraformer，中英双语，准确率高。需要等说完才识别。",
        "recommended": False,
    },
    {
        "id": "paraformer-zh-small-2024-03-09",
        "name": "离线 Paraformer 轻量中文（≈whisper base）",
        "type": "offline",
        "architecture": "paraformer",
        "languages": ["zh", "en"],
        "size": 30,
        "tar_filename": "sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2",
        "required_files": ["model.int8.onnx", "tokens.txt"],
        "file_patterns": {
            "model": ["model.int8.onnx", "model.onnx"],
            "tokens": ["tokens.txt"],
        },
        "description": "轻量版离线 Paraformer，仅约 30MB，速度快，适合低配电脑。",
        "recommended": False,
    },
    {
        "id": "paraformer-zh-2023-09-14",
        "name": "离线 Paraformer 中文旧版（≈whisper small）",
        "type": "offline",
        "architecture": "paraformer",
        "languages": ["zh", "en"],
        "size": 200,
        "tar_filename": "sherpa-onnx-paraformer-zh-2023-09-14.tar.bz2",
        "required_files": ["model.int8.onnx", "tokens.txt"],
        "file_patterns": {
            "model": ["model.int8.onnx", "model.onnx"],
            "tokens": ["tokens.txt"],
        },
        "description": "旧版离线 Paraformer，当前默认模型。保留兼容，建议升级到新版或流式模型。",
        "recommended": False,
    },
    {
        "id": "paraformer-en-2024-03-09",
        "name": "离线 Paraformer 英文（≈whisper small）",
        "type": "offline",
        "architecture": "paraformer",
        "languages": ["en"],
        "size": 200,
        "tar_filename": "sherpa-onnx-paraformer-en-2024-03-09.tar.bz2",
        "required_files": ["model.int8.onnx", "tokens.txt"],
        "file_patterns": {
            "model": ["model.int8.onnx", "model.onnx"],
            "tokens": ["tokens.txt"],
        },
        "description": "纯英文离线识别模型，准确率高。适合主要听英语的场景。",
        "recommended": False,
    },
    {
        "id": "sense-voice-5lang-int8-2025-09-09",
        "name": "离线 SenseVoice 五语言（≈whisper small，含日韩语）",
        "type": "offline",
        "architecture": "sense_voice",
        "languages": ["zh", "en", "ja", "ko", "yue"],
        "size": 250,
        "tar_filename": "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09.tar.bz2",
        "required_files": ["model.int8.onnx", "tokens.txt"],
        "file_patterns": {
            "model": ["model.int8.onnx", "model.onnx", "sense-voice-ctc-int8.onnx",
                      "sense-voice-ctc.onnx", "model_quant.onnx"],
            "tokens": ["tokens.txt", "tokens.zh-en.txt", "lang_tokens.txt"],
        },
        # SenseVoice 可能需要的额外文件（如果存在则一并复制）
        "optional_files": ["am.mvn", "config.json", "preprocess_config.json"],
        "description": "SenseVoice 多语言模型，支持中、英、日、韩、粤语五种语言自动检测。离线模式。",
        "recommended": False,
    },
    # ---------- 专门日语模型（推荐看番用） ----------
    {
        "id": "zipformer-ja-reazonspeech-2024-08-01",
        "name": "离线 Zipformer 日语专用（推荐看番）",
        "type": "offline",
        "architecture": "zipformer",
        "languages": ["ja"],
        "size": 90,
        "tar_filename": "sherpa-onnx-zipformer-ja-reazonspeech-2024-08-01.tar.bz2",
        "required_files": ["model.int8.onnx", "tokens.txt"],
        "file_patterns": {
            "model": ["model.int8.onnx", "model.onnx"],
            "tokens": ["tokens.txt"],
        },
        "optional_files": ["int8.onnx", "decoder.onnx", "encoder.onnx", "joiner.onnx"],
        "description": "专门针对日语优化的 Zipformer 模型，识别准确率高，推荐看日语番时使用。离线模式。",
        "recommended": False,
    },
]


def get_model_info(model_id: str) -> Optional[Dict]:
    """根据 model_id 获取模型信息"""
    for m in MODEL_REGISTRY:
        if m["id"] == model_id:
            return m
    return None


def list_models(model_type: Optional[str] = None) -> List[Dict]:
    """列出所有可用模型，可按类型筛选"""
    if model_type:
        return [m for m in MODEL_REGISTRY if m["type"] == model_type]
    return list(MODEL_REGISTRY)


def get_default_model_id() -> str:
    """获取默认推荐模型 ID"""
    for m in MODEL_REGISTRY:
        if m.get("recommended"):
            return m["id"]
    return MODEL_REGISTRY[0]["id"]


def verify_model_files(model_dir: str, model_info: Dict) -> Tuple[bool, str]:
    """
    验证模型目录中的文件是否完整
    返回 (是否完整, 缺失文件描述)
    """
    if not os.path.isdir(model_dir):
        return False, f"模型目录不存在: {model_dir}"

    file_patterns = model_info.get("file_patterns", {})
    missing = []

    for key, patterns in file_patterns.items():
        found = False
        for pattern in patterns:
            # 先尝试直接路径
            direct = os.path.join(model_dir, pattern)
            if os.path.exists(direct):
                found = True
                break
            # 递归搜索
            for root, dirs, files in os.walk(model_dir):
                if pattern in files:
                    found = True
                    break
                # 也支持 glob 模式匹配
                matches = glob.glob(os.path.join(root, pattern))
                if matches:
                    found = True
                    break
            if found:
                break
        if not found:
            missing.append(f"{key} (尝试: {', '.join(patterns)})")

    if missing:
        # 列出目录内容方便调试
        dir_contents = []
        for root, dirs, files in os.walk(model_dir):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), model_dir)
                dir_contents.append(rel)
        content_str = ", ".join(sorted(dir_contents)) if dir_contents else "(空目录)"
        return False, f"缺失文件: {'; '.join(missing)}\n目录实际内容: {content_str}"

    return True, "所有必需文件齐全"


# ============================================================
# 识别器基类
# ============================================================
class SherpaRecognizerBase:
    """识别器基类，定义统一接口"""

    def __init__(self, model_dir: str, model_info: Dict, device: str = "cpu", num_threads: int = 4, language: str = "auto"):
        self.model_dir = model_dir
        self.model_info = model_info
        self.device = device
        self.num_threads = num_threads
        self.language = language
        self._recognizer = None
        self._stream = None

    @property
    def model_id(self) -> str:
        return self.model_info["id"]

    @property
    def model_name(self) -> str:
        return self.model_info["name"]

    @property
    def is_streaming(self) -> bool:
        return self.model_info["type"] == "streaming"

    def _load_model(self):
        """加载模型（子类实现）"""
        raise NotImplementedError

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """离线识别整段音频（流式模型也可用此方法做一次性识别）"""
        raise NotImplementedError

    # ---------- 流式识别专用接口 ----------
    def create_stream(self):
        """创建新的识别流（流式模式用）"""
        if self._recognizer is None:
            raise RuntimeError("模型未加载")
        self._stream = self._recognizer.create_stream()
        return self._stream

    def accept_waveform(self, audio: np.ndarray, sample_rate: int = 16000):
        """向当前流喂入音频数据（流式模式用）"""
        if self._stream is None:
            self.create_stream()
        if sample_rate != 16000:
            audio = self._resample(audio, sample_rate, 16000)
        self._stream.accept_waveform(16000, audio.tolist())

    def decode(self) -> str:
        """解码当前流并返回部分识别结果（流式模式用）"""
        if self._stream is None or self._recognizer is None:
            return ""
        while self._recognizer.is_ready(self._stream):
            self._recognizer.decode_stream(self._stream)
        return self._recognizer.get_result(self._stream).strip()

    def is_endpoint(self) -> bool:
        """检测是否到达一句话的结尾（流式模式用）"""
        if self._stream is None or self._recognizer is None:
            return False
        return self._recognizer.is_endpoint(self._stream)

    def reset_stream(self):
        """重置当前流（一句话结束后调用，开始下一句）"""
        if self._stream is not None and self._recognizer is not None:
            self._recognizer.reset(self._stream)

    def get_final_text(self) -> str:
        """获取当前流的最终文本（在 endpoint 后调用）"""
        if self._stream is None or self._recognizer is None:
            return ""
        while self._recognizer.is_ready(self._stream):
            self._recognizer.decode_stream(self._stream)
        return self._recognizer.get_result(self._stream).strip()

    # ---------- 工具方法 ----------
    def _resample(self, audio: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
        """简单重采样"""
        if src_rate == dst_rate:
            return audio
        ratio = dst_rate / src_rate
        new_len = int(len(audio) * ratio)
        indices = np.linspace(0, len(audio) - 1, new_len)
        return np.interp(indices, np.arange(len(audio)), audio)

    def _find_file(self, *filenames: str) -> Optional[str]:
        """
        在模型目录中查找文件，支持多个候选文件名（按优先级）
        找到第一个存在的即返回完整路径
        """
        for filename in filenames:
            # 直接路径
            direct = os.path.join(self.model_dir, filename)
            if os.path.exists(direct):
                return direct
            # 递归搜索精确文件名
            for root, dirs, files in os.walk(self.model_dir):
                if filename in files:
                    return os.path.join(root, filename)
            # glob 模式匹配（支持通配符）
            matches = glob.glob(os.path.join(self.model_dir, "**", filename), recursive=True)
            if matches:
                return matches[0]
        return None

    def _find_file_by_patterns(self, patterns: List[str]) -> Optional[str]:
        """按模式列表查找文件，找到第一个存在的即返回"""
        return self._find_file(*patterns)

    def _list_dir_contents(self) -> str:
        """列出模型目录内容，用于调试"""
        contents = []
        for root, dirs, files in os.walk(self.model_dir):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), self.model_dir)
                size = os.path.getsize(os.path.join(root, f))
                contents.append(f"{rel} ({size}B)")
        return ", ".join(sorted(contents)) if contents else "(空目录)"


# ============================================================
# 离线识别器
# ============================================================
class OfflineSherpaRecognizer(SherpaRecognizerBase):
    """Sherpa-onnx 离线识别器（Paraformer / SenseVoice）"""

    def _load_model(self):
        """加载离线识别模型"""
        print(f"[Sherpa-offline] 开始加载模型: {self.model_name} (ID: {self.model_id})")
        print(f"[Sherpa-offline] 模型目录: {self.model_dir}")

        # 先验证文件完整性
        ok, msg = verify_model_files(self.model_dir, self.model_info)
        if not ok:
            print(f"[Sherpa-offline] 文件验证失败: {msg}")
            raise FileNotFoundError(f"模型文件不完整: {msg}")
        print(f"[Sherpa-offline] 文件验证通过")

        try:
            import sherpa_onnx
            print(f"[Sherpa-offline] sherpa-onnx 版本: {getattr(sherpa_onnx, '__version__', 'unknown')}")
        except ImportError:
            raise ImportError("sherpa-onnx 未安装，请运行: pip install sherpa-onnx")

        arch = self.model_info["architecture"]
        print(f"[Sherpa-offline] 架构: {arch}")

        # 查找 tokens 文件
        tokens_patterns = self.model_info.get("file_patterns", {}).get("tokens", ["tokens.txt"])
        tokens_path = self._find_file_by_patterns(tokens_patterns)
        if not tokens_path:
            raise FileNotFoundError(
                f"词表文件不存在。尝试了: {tokens_patterns}\n"
                f"目录内容: {self._list_dir_contents()}"
            )
        print(f"[Sherpa-offline] tokens: {tokens_path}")

        if arch == "paraformer":
            model_patterns = self.model_info.get("file_patterns", {}).get(
                "model", ["model.int8.onnx", "model.onnx"])
            model_path = self._find_file_by_patterns(model_patterns)
            if not model_path:
                raise FileNotFoundError(
                    f"Paraformer 模型文件不存在。尝试了: {model_patterns}\n"
                    f"目录内容: {self._list_dir_contents()}"
                )
            print(f"[Sherpa-offline] model: {model_path}")

            try:
                self._recognizer = sherpa_onnx.OfflineRecognizer.from_paraformer(
                    paraformer=model_path,
                    tokens=tokens_path,
                    num_threads=self.num_threads,
                    sample_rate=16000,
                    feature_dim=80,
                    decoding_method="greedy_search",
                )
            except TypeError as e:
                # 某些版本的 from_paraformer 参数名不同
                print(f"[Sherpa-offline] from_paraformer 参数不兼容，尝试备用方式: {e}")
                self._recognizer = sherpa_onnx.OfflineRecognizer.from_paraformer(
                    model_path,
                    tokens_path,
                    self.num_threads,
                )

        elif arch == "sense_voice":
            model_patterns = self.model_info.get("file_patterns", {}).get(
                "model", ["model.int8.onnx", "model.onnx"])
            model_path = self._find_file_by_patterns(model_patterns)
            if not model_path:
                raise FileNotFoundError(
                    f"SenseVoice 模型文件不存在。尝试了: {model_patterns}\n"
                    f"目录内容: {self._list_dir_contents()}"
                )
            print(f"[Sherpa-offline] SenseVoice model: {model_path}")
            print(f"[Sherpa-offline] SenseVoice language: {self.language}")

            # 检查 from_sense_voice API 是否存在
            if not hasattr(sherpa_onnx.OfflineRecognizer, 'from_sense_voice'):
                raise RuntimeError(
                    f"当前 sherpa-onnx 版本 ({getattr(sherpa_onnx, '__version__', 'unknown')}) "
                    f"不支持 from_sense_voice API。请升级 sherpa-onnx: pip install -U sherpa-onnx"
                )

            # 尝试多种参数组合，兼容不同版本
            sense_voice_loaded = False
            load_errors = []

            # 方式1: 标准参数
            try:
                self._recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                    model=model_path,
                    tokens=tokens_path,
                    num_threads=self.num_threads,
                    use_itn=True,
                    language=self.language,
                )
                sense_voice_loaded = True
                print("[Sherpa-offline] SenseVoice 加载成功（方式1: 标准参数）")
            except Exception as e:
                load_errors.append(f"方式1失败: {e}")
                print(f"[Sherpa-offline] SenseVoice 方式1失败: {e}")

            # 方式2: 不带 use_itn
            if not sense_voice_loaded:
                try:
                    self._recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                        model=model_path,
                        tokens=tokens_path,
                        num_threads=self.num_threads,
                        language=self.language,
                    )
                    sense_voice_loaded = True
                    print("[Sherpa-offline] SenseVoice 加载成功（方式2: 无 use_itn）")
                except Exception as e:
                    load_errors.append(f"方式2失败: {e}")
                    print(f"[Sherpa-offline] SenseVoice 方式2失败: {e}")

            # 方式3: 位置参数
            if not sense_voice_loaded:
                try:
                    self._recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                        model_path, tokens_path, self.num_threads,
                    )
                    sense_voice_loaded = True
                    print("[Sherpa-offline] SenseVoice 加载成功（方式3: 位置参数）")
                except Exception as e:
                    load_errors.append(f"方式3失败: {e}")
                    print(f"[Sherpa-offline] SenseVoice 方式3失败: {e}")

            if not sense_voice_loaded:
                raise RuntimeError(
                    f"SenseVoice 模型加载失败，所有方式均失败:\n"
                    + "\n".join(f"  - {e}" for e in load_errors)
                    + f"\n模型: {self.model_name}\n模型文件: {model_path}\ntokens: {tokens_path}"
                )

        else:
            raise ValueError(f"不支持的离线模型架构: {arch}")

        print(f"[Sherpa-offline] 模型加载成功: {self.model_name}")

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """离线识别整段音频"""
        if self._recognizer is None:
            self._load_model()
        if self._recognizer is None:
            return ""
        if sample_rate != 16000:
            audio = self._resample(audio, sample_rate, 16000)
        stream = self._recognizer.create_stream()
        stream.accept_waveform(16000, audio.tolist())
        self._recognizer.decode_stream(stream)
        return stream.result.text.strip()


# ============================================================
# 流式识别器
# ============================================================
class StreamingSherpaRecognizer(SherpaRecognizerBase):
    """Sherpa-onnx 流式识别器（Paraformer / Zipformer）"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rule1_min_trailing_silence = 2.4
        self.rule2_min_trailing_silence = 1.2
        self.rule3_min_utterance_length = 300

    def _load_model(self):
        """加载流式识别模型"""
        print(f"[Sherpa-streaming] 开始加载模型: {self.model_name} (ID: {self.model_id})")
        print(f"[Sherpa-streaming] 模型目录: {self.model_dir}")

        # 先验证文件完整性
        ok, msg = verify_model_files(self.model_dir, self.model_info)
        if not ok:
            print(f"[Sherpa-streaming] 文件验证失败: {msg}")
            raise FileNotFoundError(f"模型文件不完整: {msg}")
        print(f"[Sherpa-streaming] 文件验证通过")

        try:
            import sherpa_onnx
            print(f"[Sherpa-streaming] sherpa-onnx 版本: {getattr(sherpa_onnx, '__version__', 'unknown')}")
        except ImportError:
            raise ImportError("sherpa-onnx 未安装，请运行: pip install sherpa-onnx")

        arch = self.model_info["architecture"]
        print(f"[Sherpa-streaming] 架构: {arch}")

        # 查找 tokens 文件
        tokens_patterns = self.model_info.get("file_patterns", {}).get("tokens", ["tokens.txt"])
        tokens_path = self._find_file_by_patterns(tokens_patterns)
        if not tokens_path:
            raise FileNotFoundError(
                f"词表文件不存在。尝试了: {tokens_patterns}\n"
                f"目录内容: {self._list_dir_contents()}"
            )
        print(f"[Sherpa-streaming] tokens: {tokens_path}")

        common_kwargs = dict(
            tokens=tokens_path,
            num_threads=self.num_threads,
            sample_rate=16000,
            feature_dim=80,
            enable_endpoint_detection=True,
            rule1_min_trailing_silence=self.rule1_min_trailing_silence,
            rule2_min_trailing_silence=self.rule2_min_trailing_silence,
            rule3_min_utterance_length=self.rule3_min_utterance_length,
        )

        if arch == "paraformer":
            encoder_patterns = self.model_info.get("file_patterns", {}).get(
                "encoder", ["encoder.int8.onnx", "encoder.onnx"])
            decoder_patterns = self.model_info.get("file_patterns", {}).get(
                "decoder", ["decoder.int8.onnx", "decoder.onnx"])

            encoder_path = self._find_file_by_patterns(encoder_patterns)
            decoder_path = self._find_file_by_patterns(decoder_patterns)

            if not encoder_path or not decoder_path:
                raise FileNotFoundError(
                    f"流式 Paraformer 模型文件不完整:\n"
                    f"  encoder (尝试: {encoder_patterns}): {'找到' if encoder_path else '缺失'}\n"
                    f"  decoder (尝试: {decoder_patterns}): {'找到' if decoder_path else '缺失'}\n"
                    f"目录内容: {self._list_dir_contents()}"
                )
            print(f"[Sherpa-streaming] encoder: {encoder_path}")
            print(f"[Sherpa-streaming] decoder: {decoder_path}")

            try:
                self._recognizer = sherpa_onnx.OnlineRecognizer.from_paraformer(
                    encoder=encoder_path,
                    decoder=decoder_path,
                    **common_kwargs,
                )
            except TypeError as e:
                print(f"[Sherpa-streaming] from_paraformer 参数不兼容，尝试备用方式: {e}")
                self._recognizer = sherpa_onnx.OnlineRecognizer.from_paraformer(
                    encoder_path, decoder_path, tokens_path, self.num_threads,
                )

        elif arch == "zipformer":
            encoder_patterns = self.model_info.get("file_patterns", {}).get("encoder", [
                "encoder-epoch-99-avg-1.int8.onnx", "encoder-epoch-99-avg-1.onnx",
                "encoder.int8.onnx", "encoder.onnx"])
            decoder_patterns = self.model_info.get("file_patterns", {}).get("decoder", [
                "decoder-epoch-99-avg-1.int8.onnx", "decoder-epoch-99-avg-1.onnx",
                "decoder.int8.onnx", "decoder.onnx"])
            joiner_patterns = self.model_info.get("file_patterns", {}).get("joiner", [
                "joiner-epoch-99-avg-1.int8.onnx", "joiner-epoch-99-avg-1.onnx",
                "joiner.int8.onnx", "joiner.onnx"])

            encoder_path = self._find_file_by_patterns(encoder_patterns)
            decoder_path = self._find_file_by_patterns(decoder_patterns)
            joiner_path = self._find_file_by_patterns(joiner_patterns)

            if not encoder_path or not decoder_path or not joiner_path:
                raise FileNotFoundError(
                    f"流式 Zipformer 模型文件不完整:\n"
                    f"  encoder (尝试: {encoder_patterns}): {'找到' if encoder_path else '缺失'}\n"
                    f"  decoder (尝试: {decoder_patterns}): {'找到' if decoder_path else '缺失'}\n"
                    f"  joiner (尝试: {joiner_patterns}): {'找到' if joiner_path else '缺失'}\n"
                    f"目录内容: {self._list_dir_contents()}"
                )
            print(f"[Sherpa-streaming] encoder: {encoder_path}")
            print(f"[Sherpa-streaming] decoder: {decoder_path}")
            print(f"[Sherpa-streaming] joiner: {joiner_path}")

            try:
                self._recognizer = sherpa_onnx.OnlineRecognizer.from_zipformer(
                    encoder=encoder_path,
                    decoder=decoder_path,
                    joiner=joiner_path,
                    **common_kwargs,
                )
            except TypeError as e:
                print(f"[Sherpa-streaming] from_zipformer 参数不兼容，尝试备用方式: {e}")
                self._recognizer = sherpa_onnx.OnlineRecognizer.from_zipformer(
                    encoder_path, decoder_path, joiner_path, tokens_path, self.num_threads,
                )

        else:
            raise ValueError(f"不支持的流式模型架构: {arch}")

        print(f"[Sherpa-streaming] 模型加载成功: {self.model_name}")

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """用流式模型做一次性离线识别（兼容旧接口）"""
        if self._recognizer is None:
            self._load_model()
        if self._recognizer is None:
            return ""
        if sample_rate != 16000:
            audio = self._resample(audio, sample_rate, 16000)
        stream = self._recognizer.create_stream()
        stream.accept_waveform(16000, audio.tolist())
        tail_padding = np.zeros(int(16000 * 0.3), dtype=np.float32)
        stream.accept_waveform(16000, tail_padding.tolist())
        while self._recognizer.is_ready(stream):
            self._recognizer.decode_stream(stream)
        return self._recognizer.get_result(stream).strip()


# ============================================================
# 工厂函数
# ============================================================
def create_sherpa_recognizer(
    model_id: str,
    model_dir: Optional[str] = None,
    device: str = "cpu",
    num_threads: int = 4,
    language: str = "auto",
) -> SherpaRecognizerBase:
    """
    工厂函数：根据 model_id 创建对应的识别器
    加载失败时会抛出详细异常，由上层捕获处理
    """
    model_info = get_model_info(model_id)
    if model_info is None:
        print(f"[Sherpa] 未知模型 ID: {model_id}，回退到默认模型")
        model_id = get_default_model_id()
        model_info = get_model_info(model_id)

    if model_dir is None:
        from bootstrap import get_models_dir
        model_dir = str(get_models_dir() / model_info["id"])

    print(f"[Sherpa] 创建识别器: {model_info['name']} (类型: {model_info['type']}, 架构: {model_info['architecture']})")

    if model_info["type"] == "streaming":
        recognizer = StreamingSherpaRecognizer(model_dir, model_info, device, num_threads, language)
    else:
        recognizer = OfflineSherpaRecognizer(model_dir, model_info, device, num_threads, language)

    recognizer._load_model()
    return recognizer


# ============================================================
# 模型自检测试（用于调试）
# ============================================================
def diagnose_model(model_id: str, model_dir: Optional[str] = None) -> Dict:
    """
    诊断指定模型的状态，返回详细的诊断信息
    不实际加载模型，只检查文件和配置
    """
    model_info = get_model_info(model_id)
    result = {
        "model_id": model_id,
        "model_name": model_info["name"] if model_info else "未知模型",
        "exists_in_registry": model_info is not None,
        "model_dir": None,
        "dir_exists": False,
        "files_ok": False,
        "files_message": "",
        "file_details": {},
    }

    if model_info is None:
        result["files_message"] = "模型 ID 不在注册表中"
        return result

    if model_dir is None:
        from bootstrap import get_models_dir
        model_dir = str(get_models_dir() / model_info["id"])

    result["model_dir"] = model_dir
    result["dir_exists"] = os.path.isdir(model_dir)

    if not result["dir_exists"]:
        result["files_message"] = "模型目录不存在，需要下载"
        return result

    # 检查每个文件模式
    file_patterns = model_info.get("file_patterns", {})
    for key, patterns in file_patterns.items():
        found = None
        for pattern in patterns:
            direct = os.path.join(model_dir, pattern)
            if os.path.exists(direct):
                found = direct
                break
            for root, dirs, files in os.walk(model_dir):
                if pattern in files:
                    found = os.path.join(root, pattern)
                    break
                matches = glob.glob(os.path.join(root, pattern))
                if matches:
                    found = matches[0]
                    break
            if found:
                break
        result["file_details"][key] = {
            "found": found is not None,
            "path": found,
            "tried_patterns": patterns,
        }

    ok, msg = verify_model_files(model_dir, model_info)
    result["files_ok"] = ok
    result["files_message"] = msg

    return result


def diagnose_all_models() -> List[Dict]:
    """诊断所有已注册模型的状态"""
    results = []
    for m in MODEL_REGISTRY:
        results.append(diagnose_model(m["id"]))
    return results


# ============================================================
# 兼容旧接口
# ============================================================
class SherpaOnnxRecognizer:
    """旧版兼容类，内部委托给 OfflineSherpaRecognizer"""

    def __init__(self, model_dir: str, device: str = "cpu"):
        model_info = get_model_info("paraformer-zh-2023-09-14")
        if model_info is None:
            model_info = MODEL_REGISTRY[0]
        self._impl = OfflineSherpaRecognizer(model_dir, model_info, device)
        self._impl._load_model()

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        return self._impl.transcribe(audio, sample_rate)

    @staticmethod
    def get_model_info() -> dict:
        return {
            "name": "sherpa-onnx-paraformer-zh",
            "description": "Sherpa-onnx 中文优化模型（Paraformer）",
            "size": "约 200MB",
            "files": ["model.onnx", "tokens.txt"],
            "download_url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-paraformer-zh-2023-09-14.tar.bz2",
        }


if __name__ == "__main__":
    # 运行模型诊断
    print("=" * 60)
    print("Sherpa-onnx 模型诊断")
    print("=" * 60)
    results = diagnose_all_models()
    for r in results:
        status = "OK" if r["files_ok"] else "问题"
        print(f"\n[{status}] {r['model_name']} ({r['model_id']})")
        print(f"  目录: {r['model_dir']}")
        print(f"  目录存在: {r['dir_exists']}")
        print(f"  文件状态: {r['files_message']}")
        if r.get("file_details"):
            for key, detail in r["file_details"].items():
                file_status = "找到" if detail["found"] else "缺失"
                print(f"    {key}: {file_status} - {detail.get('path', 'N/A')}")
