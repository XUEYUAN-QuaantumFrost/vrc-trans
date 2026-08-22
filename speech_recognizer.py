"""
实时语音识别模块
- 支持流式识别（sherpa-onnx OnlineRecognizer）和离线识别
- 流式模式：边说边出结果，延迟极低，内置 endpoint 检测
- 离线模式：webrtcvad 断句 + 整段识别
- 支持电脑声音（立体声混音）和麦克风两种来源
"""
import os
import time
import tempfile
import queue
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf

# 无意义语气词（不翻译）
DEFAULT_FILTER_WORDS = [
    "嗯", "啊", "呃", "哦", "唉", "唔",
    "嗯。", "啊。", "呃。", "哦。",
    "嗯.", "啊.", "呃.", "哦.",
]


class SpeechRecognizer:
    def __init__(self,
                 record_source="computer",
                 device_computer=2,
                 device_mic=1,
                 whisper_model="small",
                 whisper_engine="sherpa",
                 sherpa_model_id="streaming-paraformer-bilingual-zh-en",
                 whisper_device="cpu",
                 compute_type="int8",
                 silence_threshold=500,
                 min_speech_duration=300,
                 max_speech_duration=15000,
                 vad_aggressiveness=2,
                 filter_words=None,
                 on_result=None,
                 on_partial_result=None,
                 config=None):
        """
        Args:
            on_result: 回调(text, detected_lang)，识别到一句完整语音时调用
            on_partial_result: 回调(text)，流式识别的部分结果（实时更新字幕用）
            sherpa_model_id: sherpa-onnx 模型 ID（对应 MODEL_REGISTRY）
        """
        self.config = config
        self.record_source = record_source
        self.device_computer = device_computer
        self.device_mic = device_mic
        self.whisper_model = whisper_model
        self.whisper_engine = whisper_engine
        self.sherpa_model_id = sherpa_model_id
        self.whisper_device = whisper_device
        self.compute_type = compute_type
        self.silence_threshold = silence_threshold
        self.min_speech_duration = min_speech_duration
        self.max_speech_duration = max_speech_duration
        self.vad_aggressiveness = vad_aggressiveness
        self.filter_words = filter_words or DEFAULT_FILTER_WORDS
        self.on_result = on_result
        self.on_partial_result = on_partial_result
        # 降噪设置
        self.enable_noise_reduction = config.get("enable_noise_reduction", False) if config else False
        self.noise_reduction_strength = config.get("noise_reduction_strength", 0.5) if config else 0.5
        self.mic_activation_threshold = config.get("mic_activation_threshold", 0.02) if config else 0.02
        self._noise_reduction_disabled = False  # 降噪失败后禁用，避免反复报错刷屏
        self._noise_profile = None  # 降噪的噪声频谱估计
        self._prev_gain = None  # 上一帧增益（用于时间平滑）
        self._use_builtin_denoise = False  # noisereduce 不可用时自动切换到内置降噪

        self._model = None
        self._vad = None
        self._audio_queue = queue.Queue(maxsize=100)
        self._running = False
        self._stream = None
        self._sample_rate = 16000
        self._frame_duration = 30  # webrtcvad 只支持 10/20/30ms

        # 流式模式状态
        self._streaming = False  # 由模型类型自动决定

    @property
    def _device_id(self):
        return self.device_computer if self.record_source == "computer" else self.device_mic

    @property
    def _source_name(self):
        return "电脑声音（立体声混音）" if self.record_source == "computer" else "麦克风"

    @property
    def is_streaming_mode(self) -> bool:
        """是否为流式识别模式（由模型类型决定）"""
        if self._model is not None and hasattr(self._model, 'is_streaming'):
            return self._model.is_streaming
        return False

    def _load_model(self):
        """加载语音识别模型，faster-whisper 失败时自动回退到 sherpa-onnx"""
        if self._model is not None:
            return

        if self.whisper_engine == "sherpa":
            self._load_sherpa_model()
            return

        if self.whisper_engine == "faster":
            # faster-whisper 依赖 ctranslate2，在某些环境下会随机触发 access violation 致命崩溃
            # 子进程测试也不可靠（测试通过后主进程仍可能崩溃），为了程序稳定直接回退到 sherpa-onnx
            print("[Speech] 注意：faster-whisper 在当前环境不稳定（ctranslate2 access violation），已自动切换到 sherpa-onnx")
            print("[Speech] 如需使用 faster-whisper，可在设置中手动切换，但请注意可能随机崩溃")
            self.whisper_engine = "sherpa"
            self._load_sherpa_model()
            return

        # 旧配置兼容
        print(f"[Speech] 引擎 {self.whisper_engine} 不可用，自动回退到 sherpa")
        self.whisper_engine = "sherpa"
        self._load_sherpa_model()

    def _load_sherpa_model(self):
        """加载 sherpa-onnx 模型（使用新的多模型框架）"""
        try:
            from sherpa_recognizer import create_sherpa_recognizer, get_model_info
            from bootstrap import check_sherpa_model_exists, download_sherpa_model, get_sherpa_model_dir

            model_info = get_model_info(self.sherpa_model_id)
            if model_info is None:
                print(f"[Speech] 未知模型 ID: {self.sherpa_model_id}，使用默认模型")
                from sherpa_recognizer import get_default_model_id
                self.sherpa_model_id = get_default_model_id()
                model_info = get_model_info(self.sherpa_model_id)

            # 检查模型是否存在，不存在则下载（带进度对话框，后台线程，不卡 UI）
            if not check_sherpa_model_exists(self.sherpa_model_id):
                print(f"[Speech] 模型 {self.sherpa_model_id} 不存在，开始下载...")
                success = self._download_model_with_progress(self.sherpa_model_id, model_info)
                if not success:
                    print("[Speech] 模型下载失败")
                    self._model = None
                    return

            model_dir = str(get_sherpa_model_dir(self.sherpa_model_id))
            sv_language = self.config.get("sense_voice_language", "auto") if self.config else "auto"
            self._model = create_sherpa_recognizer(
                model_id=self.sherpa_model_id,
                model_dir=model_dir,
                device=self.whisper_device,
                num_threads=4,
                language=sv_language,
            )
            self._streaming = self._model.is_streaming
            mode_str = "流式" if self._streaming else "离线"
            print(f"[Speech] Sherpa-onnx 模型加载成功 ({mode_str}): {self._model.model_name}")
        except Exception as e:
            print(f"[Speech] Sherpa-onnx 加载失败: {e}")
            import traceback
            traceback.print_exc()
            self._model = None

    def _download_model_with_progress(self, model_id, model_info):
        """带进度对话框的模型下载（后台线程，不阻塞 UI）；无 Qt 环境时回退到控制台下载。"""
        from bootstrap import download_sherpa_model

        # 尝试使用 Qt 进度对话框
        try:
            from PyQt5.QtWidgets import QApplication, QProgressDialog, QMessageBox
            from PyQt5.QtCore import QTimer, Qt
            app = QApplication.instance()
            if app is None:
                raise RuntimeError("no QApplication")
        except Exception:
            return download_sherpa_model(model_id)

        model_name = model_info.get("name", model_id)
        tar_filename = model_info.get("tar_filename", model_id)
        official_url = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{tar_filename}"
        progress = {"d": 0, "t": 0, "mirror": "连接中...", "done": False, "success": False}
        cancel_event = threading.Event()

        def _progress_cb(d, t):
            progress["d"] = d
            progress["t"] = t

        def _status_cb(idx, total, url):
            progress["mirror"] = f"线路 {idx}/{total}"

        def _worker():
            try:
                progress["success"] = download_sherpa_model(
                    model_id,
                    progress_callback=_progress_cb,
                    cancel_event=cancel_event,
                    status_callback=_status_cb,
                )
            except Exception as e:
                print(f"[Speech] 下载线程异常: {e}")
                progress["success"] = False
            finally:
                progress["done"] = True

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

        dlg = QProgressDialog(
            f"正在下载语音模型：{model_name}\n首次运行需要下载模型，请耐心等待...",
            "取消", 0, 100)
        dlg.setWindowTitle("下载语音模型")
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setMinimumDuration(0)
        dlg.setAutoClose(False)
        dlg.setAutoReset(False)
        dlg.setMinimumWidth(460)
        dlg.setValue(0)

        def _on_cancel():
            cancel_event.set()
            dlg.setLabelText("正在取消下载...")
        dlg.canceled.connect(_on_cancel)

        def _tick():
            if progress["done"]:
                dlg.setValue(100)
                dlg.close()
                timer.stop()
                return
            if dlg.wasCanceled():
                return
            d, tot, mirror = progress["d"], progress["t"], progress["mirror"]
            if tot > 0:
                pct = min(100, int(d * 100 / tot))
                dlg.setValue(pct)
                mb = d // 1024 // 1024
                tot_mb = tot // 1024 // 1024
                dlg.setLabelText(
                    f"正在下载语音模型：{model_name}\n"
                    f"{mirror}  {pct}%  ({mb}/{tot_mb} MB)"
                )
            else:
                dlg.setLabelText(
                    f"正在下载语音模型：{model_name}\n"
                    f"{mirror}  连接中..."
                )

        timer = QTimer()
        timer.timeout.connect(_tick)
        timer.start(200)
        dlg.exec_()
        timer.stop()
        t.join(timeout=5)

        if not progress["success"]:
            try:
                QMessageBox.warning(
                    None, "模型下载失败",
                    "语音模型下载失败（可能是网络/镜像问题）。\n\n"
                    "你可以：\n"
                    "1. 检查网络后重启程序重试\n"
                    "2. 用浏览器/下载工具手动下载：\n"
                    f"   {official_url}\n"
                    f"   （国内可加前缀 https://ghfast.top/ ）\n"
                    "3. 下载后解压，把里面的文件放到模型目录（见控制台输出路径）"
                )
            except Exception:
                pass
        return progress["success"]

    def _load_faster_whisper_model(self):
        """加载 faster-whisper 模型（保留兼容，EXE 模式下可能崩溃）"""
        # NumPy 2.x 与 ctranslate2 不兼容，直接跳过加载，避免崩溃
        try:
            import numpy as np
            ver = tuple(int(x) for x in np.__version__.split('.')[:2])
            if ver >= (2, 0):
                print(f"[Speech] NumPy {np.__version__} 与 ctranslate2/faster-whisper 不兼容，跳过加载")
                print("[Speech] 已自动回退到 sherpa-onnx。如需使用 faster-whisper，请执行: pip install numpy<2，然后重启程序")
                self._model = None
                return
        except Exception:
            pass
        try:
            from faster_whisper import WhisperModel
            from bootstrap import get_models_dir

            model_path = None
            bootstrap_dir = get_models_dir() / self.whisper_model
            if bootstrap_dir.is_dir() and (bootstrap_dir / "model.bin").exists():
                model_path = str(bootstrap_dir)
                print(f"[Speech] 使用 bootstrap 模型: {model_path}")

            if model_path is None:
                local_dir = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "models", self.whisper_model
                )
                if os.path.isdir(local_dir) and os.path.exists(os.path.join(local_dir, "model.bin")):
                    model_path = local_dir

            if model_path is None:
                model_path = self.whisper_model
                print(f"[Speech] 未找到本地模型 {self.whisper_model}，faster-whisper 将自动从 HuggingFace 下载，请稍候...")
                print(f"[Speech] 提示：下载较慢可改用 sherpa-onnx 引擎（已内置模型自动下载，速度更快）")

            # 先用子进程测试 faster-whisper 能不能正常加载，避免主程序崩溃（access violation）
            print("[Speech] 正在测试 faster-whisper 兼容性...")
            import subprocess
            import sys
            _test_code = (
                "import sys\n"
                "try:\n"
                "    from faster_whisper import WhisperModel\n"
                "    model = WhisperModel(" + repr(model_path) + ", device='cpu', compute_type='int8', num_workers=1, cpu_threads=1)\n"
                "    print('OK')\n"
                "    sys.exit(0)\n"
                "except Exception as e:\n"
                "    print('ERROR:', e)\n"
                "    sys.exit(1)"
            )
            try:
                result = subprocess.run([sys.executable, "-c", _test_code], capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    err_output = (result.stderr or result.stdout or "").strip()
                    print(f"[Speech] faster-whisper 子进程测试失败: {err_output[:200]}")
                    print("[Speech] 自动回退到 sherpa-onnx（faster-whisper 在当前环境不稳定）")
                    self.whisper_engine = "sherpa"
                    self._load_sherpa_model()
                    return
                print("[Speech] faster-whisper 兼容性测试通过")
            except subprocess.TimeoutExpired:
                print("[Speech] faster-whisper 子进程测试超时，自动回退到 sherpa-onnx")
                self.whisper_engine = "sherpa"
                self._load_sherpa_model()
                return
            except Exception as test_err:
                print(f"[Speech] faster-whisper 子进程测试异常: {test_err}，自动回退到 sherpa-onnx")
                self.whisper_engine = "sherpa"
                self._load_sherpa_model()
                return

            try:
                self._model = WhisperModel(
                    model_path,
                    device=self.whisper_device,
                    compute_type=self.compute_type,
                    num_workers=1,
                    cpu_threads=1,
                )
            except Exception as e:
                if "float16" in str(e).lower() or "compute type" in str(e).lower():
                    print(f"[Speech] {self.compute_type} 不支持，自动回退到 int8")
                    self.compute_type = "int8"
                    self._model = WhisperModel(
                        model_path,
                        device=self.whisper_device,
                        compute_type="int8",
                        num_workers=1,
                        cpu_threads=1,
                    )
                else:
                    raise
            self._streaming = False
            print(f"[Speech] faster-whisper 模型加载成功: {model_path}")
        except Exception as e:
            print(f"[Speech] faster-whisper 加载失败: {e}")
            import traceback
            traceback.print_exc()
            self._model = None
            # 如果是没安装，自动 pip install
            if isinstance(e, ModuleNotFoundError) and "faster_whisper" in str(e):
                print("[Speech] faster-whisper 未安装，正在自动安装...")
                try:
                    import subprocess
                    import sys
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "faster-whisper", "--quiet"],
                        capture_output=True, text=True, timeout=300
                    )
                    if result.returncode == 0:
                        print("[Speech] faster-whisper 安装成功！请重启程序以使用该引擎")
                    else:
                        print(f"[Speech] faster-whisper 安装失败: {result.stderr}")
                except Exception as install_err:
                    print(f"[Speech] faster-whisper 安装异常: {install_err}")

    def _init_vad(self):
        """初始化 webrtcvad（离线模式用）"""
        import webrtcvad
        self._vad = webrtcvad.Vad(self.vad_aggressiveness)

    def _audio_callback(self, indata, frames, time_info, status):
        """sounddevice 采集回调"""
        if status and not status.input_overflow:
            print(f"[Speech] 音频状态: {status}")
        try:
            # 记录当前音量（用于设置界面的音量指示器）
            self._current_volume = float(np.abs(indata).mean()) / 32768.0
            self._audio_queue.put_nowait(indata.copy())
        except queue.Full:
            try:
                self._audio_queue.get_nowait()
                self._audio_queue.put_nowait(indata.copy())
            except Exception:
                pass

    def get_current_volume(self) -> float:
        """获取当前麦克风音量（0.0-1.0），用于设置界面的音量指示器"""
        return getattr(self, '_current_volume', 0.0)

    def _is_meaningless(self, text):
        """判断是否是无意义语气词"""
        clean = text.strip().rstrip("。.，,！!？?~～")
        if clean in self.filter_words:
            return True
        if len(clean) <= 1:
            return True
        return False

    def _emit_result(self, text, detected_lang="unknown"):
        """触发识别结果回调（含语气词过滤）"""
        if not text:
            return
        cfg = getattr(self, 'config', None)
        if cfg and cfg.get("filter_filler_words", False) and self._is_meaningless(text):
            return
        if self.on_result:
            self.on_result(text, detected_lang)

    # ============================================================
    # 处理循环：根据模式分流
    # ============================================================

    def _process_loop(self):
        """音频处理主循环（子线程），根据模型类型自动选择流式/离线"""
        if self.is_streaming_mode:
            self._streaming_process_loop()
        else:
            self._offline_process_loop()

    # ---------- 流式识别处理循环 ----------

    def _streaming_process_loop(self):
        """
        流式识别处理循环
        - 直接把音频喂给 OnlineRecognizer
        - 定期 decode 获取部分结果
        - endpoint 检测到一句话结束 → 触发最终结果 → reset
        """
        print("[Speech] 流式识别模式启动")
        self._model.create_stream()
        partial_text = ""
        frames_since_decode = 0
        decode_interval = 3  # 每 3 帧（约 90ms）decode 一次

        while self._running:
            try:
                frame = self._audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # frame: int16, shape (blocksize, channels)
            if frame.ndim > 1:
                mono = frame.mean(axis=1)
            else:
                mono = frame

            # 转 float32, 范围 [-1, 1]
            audio_float = mono.astype(np.float32) / 32768.0

            # 喂给识别器
            self._model.accept_waveform(audio_float, self._sample_rate)

            frames_since_decode += 1
            if frames_since_decode >= decode_interval:
                frames_since_decode = 0
                # decode 获取部分结果
                current_text = self._model.decode()
                if current_text and current_text != partial_text:
                    partial_text = current_text
                    if self.on_partial_result:
                        self.on_partial_result(partial_text)

                # 检查是否到达一句话结尾
                if self._model.is_endpoint():
                    final_text = self._model.get_final_text()
                    if final_text and final_text.strip():
                        # 清除部分结果显示
                        if self.on_partial_result:
                            self.on_partial_result("")
                        # 触发最终结果
                        self._emit_result(final_text.strip(), "zh")
                    # 重置流，开始下一句
                    self._model.reset_stream()
                    partial_text = ""

    # ---------- 离线识别处理循环（原有逻辑） ----------

    def _offline_process_loop(self):
        """离线识别处理循环（webrtcvad 断句 + 整段识别）"""
        speech_buffer = []
        silence_frames = 0
        in_speech = False

        while self._running:
            try:
                frame = self._audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if frame.ndim > 1:
                mono = frame.mean(axis=1).astype(np.int16)
            else:
                mono = frame.astype(np.int16)

            try:
                is_speech = self._vad.is_speech(mono.tobytes(), self._sample_rate)
            except Exception as e:
                print(f"[Speech] VAD 错误: {e}")
                continue

            if is_speech:
                speech_buffer.append(mono)
                silence_frames = 0
                in_speech = True
                if len(speech_buffer) * self._frame_duration >= self.max_speech_duration:
                    self._transcribe_offline(speech_buffer)
                    speech_buffer = []
                    silence_frames = 0
                    in_speech = False
            else:
                if in_speech:
                    silence_frames += 1
                    speech_buffer.append(mono)
                    if silence_frames * self._frame_duration >= self.silence_threshold:
                        speech_duration = len(speech_buffer) * self._frame_duration
                        if speech_duration >= self.min_speech_duration:
                            self._transcribe_offline(speech_buffer)
                        speech_buffer = []
                        silence_frames = 0
                        in_speech = False

    def _builtin_denoise(self, audio_float: np.ndarray) -> np.ndarray:
        """内置降噪算法：改进的频谱减法，纯 NumPy 实现，不依赖 scipy/noisereduce
        
        改进点：
        1. 持续更新噪声谱（低能量帧自动更新）
        2. 过减法 + 频谱下限，减少音乐噪声
        3. 增益因子时间平滑
        4. 自适应降噪强度（根据帧能量）
        """
        sr = self._sample_rate
        strength = float(getattr(self, 'noise_reduction_strength', 0.5))
        strength = max(0.0, min(1.0, strength))
        
        # 参数
        frame_size = 1024
        hop_size = 256
        n_fft = frame_size
        
        # 太短的音频直接返回
        if len(audio_float) < frame_size:
            return audio_float
        
        # 汉宁窗
        window = np.hanning(frame_size).astype(np.float32)
        
        # 计算帧数
        n_frames = 1 + (len(audio_float) - frame_size) // hop_size
        
        # 初始化噪声谱（如果还没有）
        if self._noise_profile is None:
            # 用前几帧中能量最低的几帧估计噪声
            n_init_frames = min(20, n_frames)
            frame_energies = []
            frame_specs = []
            for i in range(n_init_frames):
                start = i * hop_size
                frame = audio_float[start:start + frame_size] * window
                spec = np.abs(np.fft.rfft(frame, n=n_fft))
                frame_specs.append(spec)
                frame_energies.append(np.mean(spec ** 2))
            # 取能量最低的 40% 帧作为噪声参考
            n_noise = max(1, int(n_init_frames * 0.4))
            noise_indices = np.argsort(frame_energies)[:n_noise]
            self._noise_profile = np.mean([frame_specs[i] for i in noise_indices], axis=0)
            # 上一帧增益（用于时间平滑）
            self._prev_gain = np.ones(n_fft // 2 + 1, dtype=np.float32)
        
        noise_spec = self._noise_profile
        prev_gain = self._prev_gain
        
        # 过减法因子（根据强度调整）
        over_sub = 1.0 + strength * 1.5  # 1.0 ~ 2.5
        # 频谱下限（避免完全静音，减少音乐噪声）
        spectral_floor = 0.08 + strength * 0.05  # 0.08 ~ 0.13
        # 时间平滑因子
        smooth_factor = 0.55
        
        # 逐帧处理（重叠相加）
        output = np.zeros_like(audio_float)
        window_sum = np.zeros_like(audio_float)
        
        for i in range(n_frames):
            start = i * hop_size
            frame = audio_float[start:start + frame_size] * window
            
            # FFT
            spec = np.fft.rfft(frame, n=n_fft)
            mag = np.abs(spec)
            phase = np.angle(spec)
            
            # 计算帧能量，判断是否为静音段
            frame_energy = np.mean(mag ** 2)
            noise_energy = np.mean(noise_spec ** 2)
            
            # 静音段（能量接近噪声）：更新噪声谱
            if frame_energy < noise_energy * 1.5:
                # 平滑更新噪声谱
                noise_spec = noise_spec * 0.9 + mag * 0.1
            
            # 计算后验 SNR
            eps = 1e-10
            post_snr = (mag ** 2) / (noise_spec ** 2 + eps)
            
            # 过减法：增益 = max((SNR - over_sub) / SNR, floor)
            gain = np.maximum((post_snr - over_sub) / (post_snr + eps), spectral_floor)
            gain = np.minimum(gain, 1.0)
            
            # 时间平滑（减少音乐噪声）
            gain = smooth_factor * prev_gain + (1 - smooth_factor) * gain
            prev_gain = gain
            
            # 应用增益
            mag_denoised = mag * gain
            
            # 重建
            spec_denoised = mag_denoised * np.exp(1j * phase)
            frame_denoised = np.fft.irfft(spec_denoised, n=n_fft)[:frame_size]
            
            # 重叠相加
            output[start:start + frame_size] += frame_denoised * window
            window_sum[start:start + frame_size] += window * window
        
        # 保存更新后的噪声谱和增益
        self._noise_profile = noise_spec
        self._prev_gain = prev_gain
        
        # 归一化
        mask = window_sum > 1e-8
        output[mask] /= window_sum[mask]
        
        return output.astype(np.float32)

    def _transcribe_offline(self, buffer_list):
        """离线转写一段音频"""
        if not buffer_list:
            return
        audio_data = np.concatenate(buffer_list)

        # 实时降噪：优先用 noisereduce（效果更好），不可用时回退内置降噪
        if getattr(self, 'enable_noise_reduction', False) and not getattr(self, '_noise_reduction_disabled', False):
            audio_float = audio_data.astype(np.float32) / 32768.0
            audio_denoised = None
            
            # 优先尝试 noisereduce（如果未标记为不可用）
            if not getattr(self, '_use_builtin_denoise', False):
                try:
                    import noisereduce as nr
                    try:
                        # noisereduce 3.x API
                        audio_denoised = nr.reduce_noise(
                            y=audio_float, 
                            sr=self._sample_rate,
                            prop_decrease=float(self.noise_reduction_strength)
                        )
                    except TypeError:
                        # 旧版 API 兼容
                        audio_denoised = nr.reduce_noise(
                            audio_clip=audio_float, 
                            rate=self._sample_rate
                        )
                except Exception as e:
                    # noisereduce 不可用，回退到内置降噪（只报一次）
                    if not getattr(self, '_use_builtin_denoise', False):
                        err_msg = str(e)
                        if "long" in err_msg or ("numpy" in err_msg.lower() and "attribute" in err_msg.lower()):
                            print(f"[Speech] noisereduce 依赖不兼容（scipy过旧），切换到内置降噪。可执行: pip install --upgrade scipy noisereduce")
                        else:
                            print(f"[Speech] noisereduce 不可用({type(e).__name__})，切换到内置降噪")
                        self._use_builtin_denoise = True
            
            # 内置降噪（频谱减法，纯 NumPy 实现）
            if audio_denoised is None:
                try:
                    audio_denoised = self._builtin_denoise(audio_float)
                except Exception as e:
                    if not getattr(self, '_noise_reduction_disabled', False):
                        print(f"[Speech] 内置降噪失败，已关闭降噪: {e}")
                        self._noise_reduction_disabled = True
                    audio_denoised = audio_float
            
            if audio_denoised is not None:
                audio_data = (np.clip(audio_denoised, -1.0, 1.0) * 32767.0).astype(np.int16)

        tmp_file = tempfile.mktemp(suffix=".wav")
        try:
            sf.write(tmp_file, audio_data, self._sample_rate)
            self._load_model()
            if self._model is None:
                return

            if self.whisper_engine == "sherpa":
                # sherpa 直接用 numpy 数组
                audio_float = audio_data.astype(np.float32) / 32768.0
                text = self._model.transcribe(audio_float, self._sample_rate)
                detected_lang = "zh"
            elif self.whisper_engine == "faster":
                segments, info = self._model.transcribe(tmp_file, beam_size=5)
                text = " ".join(seg.text for seg in segments).strip()
                detected_lang = info.language
            else:
                result = self._model.transcribe(tmp_file)
                text = result["text"].strip()
                detected_lang = result.get("language", "unknown")

            if not text:
                return
            self._emit_result(text, detected_lang)
        except Exception as e:
            import traceback
            print(f"[Speech] 转写失败: {e}")
            traceback.print_exc()
        finally:
            try:
                os.remove(tmp_file)
            except OSError:
                pass

    # ============================================================
    # 公共接口
    # ============================================================

    def start(self):
        """启动实时识别"""
        if self._running:
            return

        # 离线模式需要 VAD，流式模式用 sherpa 内置 endpoint detection
        if not self.is_streaming_mode:
            try:
                self._init_vad()
            except ImportError:
                print("[Speech] 未安装 webrtcvad，请运行: pip install webrtcvad")
                return

        print("[Speech] 正在加载模型...")
        self._load_model()
        if self._model is None:
            print("[Speech] 模型加载失败，无法启动识别")
            return

        self._running = True
        self._audio_queue = queue.Queue(maxsize=100)
        self._process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._process_thread.start()

        try:
            blocksize = int(self._sample_rate * self._frame_duration / 1000)
            self._stream = sd.InputStream(
                samplerate=self._sample_rate,
                channels=1,
                dtype=np.int16,
                device=self._device_id,
                blocksize=blocksize,
                latency='high',
                callback=self._audio_callback,
            )
            self._stream.start()
            mode_str = "流式" if self.is_streaming_mode else "离线"
            print(f"[Speech] 实时识别已启动（{mode_str}模式, 来源: {self._source_name}, 设备: {self._device_id}）")
        except Exception as e:
            print(f"[Speech] 音频流启动失败: {e}")
            self._running = False

    def stop(self):
        """停止识别（安全释放资源，避免退出时堆损坏）"""
        if not self._running and self._stream is None and self._model is None:
            return
        self._running = False
        # 1. 先停止音频流（停止采集回调）
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        # 2. 清空音频队列，解除处理线程的阻塞
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except Exception:
                break
        # 3. 等待处理线程结束（最多等 2 秒，避免卡死）
        if hasattr(self, '_process_thread') and self._process_thread is not None:
            try:
                self._process_thread.join(timeout=2.0)
            except Exception:
                pass
            self._process_thread = None
        # 4. 显式释放 sherpa-onnx 模型（触发 onnxruntime session 释放）
        if self._model is not None:
            try:
                # 如果模型有显式的释放方法就调用
                if hasattr(self._model, 'release'):
                    self._model.release()
            except Exception:
                pass
            self._model = None
        # 5. 释放 VAD
        if self._vad is not None:
            self._vad = None
        # 6. 强制垃圾回收，确保 onnxruntime 内存释放
        import gc
        gc.collect()
        # 7. 小延迟，给底层库时间清理
        time.sleep(0.3)
        print("[Speech] 实时识别已停止")

    def is_running(self):
        return self._running

    @staticmethod
    def list_devices():
        """列出所有音频输入设备"""
        try:
            devices = sd.query_devices()
            result = []
            for i, d in enumerate(devices):
                if d.get("max_input_channels", 0) > 0:
                    result.append((i, d["name"], d["max_input_channels"]))
            return result
        except Exception as e:
            print(f"[Speech] 枚举设备失败: {e}")
            return []

    @staticmethod
    def get_default_input_device():
        """获取系统默认输入设备索引"""
        try:
            return sd.default.device[0]
        except Exception:
            return None
