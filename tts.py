"""
TTS 语音朗读模块
支持三种引擎：
  - pyttsx3：离线，Windows 自带语音，只能用系统默认输出设备
  - edge-tts：联网，微软语音，音色丰富，可指定输出设备（含虚拟音频线）
  - volcengine（火山引擎/豆包）：联网，字节跳动语音，音色自然，可调语速/音量/音调
输出设备通过 sounddevice 选择，支持同时输出到多个设备。
"""
import os
import json
import time
import tempfile
import threading
import logger
log = logger.get_logger("tts")

# 全局状态
_pyttsx3_engine = None
_pyttsx3_available = None
_edge_available = None
_volcengine_available = None

# edge-tts 常用音色（中文）
EDGE_VOICES = [
    ("zh-CN-XiaoxiaoNeural", "晓晓（女声，活泼）"),
    ("zh-CN-XiaoyiNeural", "晓伊（女声，温柔）"),
    ("zh-CN-YunjianNeural", "云健（男声，沉稳）"),
    ("zh-CN-YunxiNeural", "云希（男声，阳光）"),
    ("zh-CN-YunxiaNeural", "云夏（男声，少年）"),
    ("zh-CN-YunyangNeural", "云扬（男声，新闻）"),
    ("zh-TW-HsiaoChenNeural", "晓辰（繁体女声）"),
    ("zh-TW-YunJheNeural", "云哲（繁体男声）"),
    ("en-US-AriaNeural", "Aria（英语女声）"),
    ("en-US-GuyNeural", "Guy（英语男声）"),
    ("ja-JP-NanamiNeural", "七海（日语女声）"),
    ("ja-JP-KeitaNeural", "庆太（日语男声）"),
]

# 火山引擎（豆包）常用音色
# 完整列表请参考火山引擎控制台：https://console.volcengine.com/speech/service/8
VOLCENGINE_VOICES = [
    ("BV001_streaming", "通用女声（清晰自然）"),
    ("BV002_streaming", "通用男声（沉稳大气）"),
    ("BV406_streaming", "亲切女声（温柔体贴）"),
    ("BV407_streaming", "活泼女声（青春活力）"),
    ("BV408_streaming", "沉稳男声（成熟稳重）"),
    ("BV409_streaming", "阳光男声（朝气阳光）"),
    ("BV103_streaming", "知性女声（专业干练）"),
    ("BV105_streaming", "甜美女声（甜美可爱）"),
    ("BV106_streaming", "磁性男声（磁性低沉）"),
    ("BV108_streaming", "萝莉女声（稚嫩可爱）"),
    ("BV123_streaming", "少年男声（青春少年）"),
    ("BV124_streaming", "御姐女声（成熟优雅）"),
]


def _check_pyttsx3():
    global _pyttsx3_engine, _pyttsx3_available
    if _pyttsx3_available is False:
        return None
    if _pyttsx3_engine is not None:
        return _pyttsx3_engine
    try:
        import pyttsx3
        _pyttsx3_engine = pyttsx3.init()
        _pyttsx3_available = True
        log.info("TTS pyttsx3 引擎初始化成功")
        return _pyttsx3_engine
    except ImportError:
        _pyttsx3_available = False
        log.warning("未安装 pyttsx3")
        return None
    except Exception as e:
        _pyttsx3_available = False
        log.error(f"pyttsx3 初始化失败: {e}")
        return None


def _check_edge_tts():
    global _edge_available
    if _edge_available is not None:
        return _edge_available
    try:
        import edge_tts  # noqa: F401
        _edge_available = True
        log.info("edge-tts 可用")
    except ImportError:
        _edge_available = False
        log.warning("未安装 edge-tts，联网语音不可用。安装: pip install edge-tts")
    return _edge_available


def _check_volcengine():
    global _volcengine_available
    if _volcengine_available is not None:
        return _volcengine_available
    try:
        import websockets  # noqa: F401
        _volcengine_available = True
        log.info("火山引擎 TTS 依赖（websockets）可用")
    except ImportError:
        _volcengine_available = False
        log.warning("未安装 websockets，火山引擎 TTS 不可用。安装: pip install websockets")
    return _volcengine_available


def is_available(engine="pyttsx3") -> bool:
    """检查指定 TTS 引擎是否可用"""
    if engine == "edge":
        return _check_edge_tts()
    if engine == "volcengine":
        return _check_volcengine()
    return _check_pyttsx3() is not None


def get_output_devices():
    """获取所有音频输出设备列表 [(index, name), ...]"""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        result = []
        for i, d in enumerate(devices):
            if d.get('max_output_channels', 0) > 0:
                name = d.get('name', f'设备 {i}')
                result.append((i, name))
        return result
    except Exception as e:
        log.error(f"获取音频输出设备失败: {e}")
        return []


def get_voices(engine="edge"):
    """获取指定引擎的可用音色列表 [(voice_id, label), ...]"""
    if engine == "volcengine":
        return VOLCENGINE_VOICES
    return EDGE_VOICES


def get_edge_voices():
    """获取 edge-tts 可用音色列表（兼容旧接口）"""
    return EDGE_VOICES


def _play_on_devices(filepath, device_ids):
    """在指定设备上播放音频文件"""
    try:
        import sounddevice as sd
        import soundfile as sf
        data, fs = sf.read(filepath)
        threads = []
        for dev_id in device_ids:
            def _play(did=dev_id):
                try:
                    sd.play(data, fs, device=did)
                    sd.wait()
                except Exception as e:
                    log.error(f"在设备 {did} 播放失败: {e}")
            t = threading.Thread(target=_play, daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join(timeout=30)
    except Exception as e:
        log.error(f"播放音频失败: {e}")


def speak(
    text: str,
    engine: str = "pyttsx3",
    rate: int = 200,
    volume: float = 1.0,
    voice_id: str = None,
    output_devices=None,
    # 火山引擎专用参数
    volc_appid: str = None,
    volc_token: str = None,
    volc_pitch: float = 1.0,
):
    """
    朗读文本（异步，不阻塞主线程）
    engine: "pyttsx3"（离线）/ "edge"（联网微软语音）/ "volcengine"（火山引擎/豆包）
    rate: 语速 50-400（pyttsx3 用）
    volume: 音量 0.0-1.0
    voice_id: 语音 ID
    output_devices: 输出设备索引列表 [0, 2]，None 则用系统默认
    volc_appid / volc_token: 火山引擎凭证
    volc_pitch: 音调 0.5-2.0（火山引擎用）
    """
    if not text or not text.strip():
        return

    def _worker():
        if engine == "edge" and _check_edge_tts():
            _speak_edge(text, voice_id, output_devices)
        elif engine == "volcengine" and _check_volcengine() and volc_appid and volc_token:
            _speak_volcengine(text, voice_id, volc_appid, volc_token,
                               rate, volume, volc_pitch, output_devices)
        else:
            _speak_pyttsx3(text, rate, volume, voice_id)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def _speak_pyttsx3(text, rate, volume, voice_id):
    """用 pyttsx3 朗读（离线，系统默认设备）"""
    engine = _check_pyttsx3()
    if engine is None:
        return
    try:
        if rate:
            engine.setProperty('rate', rate)
        if volume is not None:
            engine.setProperty('volume', volume)
        if voice_id:
            engine.setProperty('voice', voice_id)
        engine.say(text.strip())
        engine.runAndWait()
    except Exception as e:
        log.error(f"pyttsx3 朗读失败: {e}")


def _speak_edge(text, voice_id, output_devices):
    """用 edge-tts 朗读（联网，可指定输出设备）"""
    try:
        import edge_tts
        import asyncio
        voice = voice_id or "zh-CN-XiaoxiaoNeural"
        tmp_file = os.path.join(tempfile.gettempdir(), f"vrc_tts_{os.getpid()}.mp3")

        async def _generate():
            communicate = edge_tts.Communicate(text.strip(), voice)
            await communicate.save(tmp_file)

        # 在新线程里跑 asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate())
        loop.close()

        if os.path.exists(tmp_file):
            if output_devices:
                _play_on_devices(tmp_file, output_devices)
            else:
                _play_on_devices(tmp_file, [None])  # None = 默认设备
            # 清理临时文件
            try:
                os.remove(tmp_file)
            except OSError:
                pass
    except Exception as e:
        log.error(f"edge-tts 朗读失败: {e}")


def _speak_volcengine(text, voice_id, appid, token, rate, volume, pitch, output_devices):
    """
    用火山引擎（豆包）TTS 朗读（联网，WebSocket 接口）
    文档：https://www.volcengine.com/docs/6561/97465
    """
    try:
        import asyncio
        import websockets

        voice = voice_id or "BV001_streaming"
        tmp_file = os.path.join(tempfile.gettempdir(), f"vrc_tts_volc_{os.getpid()}.mp3")
        reqid = f"vrc_trans_{int(time.time() * 1000)}"

        # 语速映射：pyttsx3 的 rate（50-400）映射到 0.5-2.0
        # rate=200 为正常速度，对应 speed_ratio=1.0
        speed_ratio = max(0.5, min(2.0, rate / 200.0)) if rate else 1.0
        # 音量映射：0.0-1.0 映射到 0.1-3.0
        volume_ratio = max(0.1, min(3.0, volume * 3.0)) if volume else 1.0
        # 音调：0.5-2.0
        pitch_ratio = max(0.5, min(2.0, pitch)) if pitch else 1.0

        request_payload = {
            "app": {
                "appid": appid,
                "token": token,
                "user": "vrc_trans_user"
            },
            "user": {
                "uid": "vrc_trans_user"
            },
            "audio": {
                "voice_type": voice,
                "encoding": "mp3",
                "speed_ratio": speed_ratio,
                "volume_ratio": volume_ratio,
                "pitch_ratio": pitch_ratio,
            },
            "request": {
                "reqid": reqid,
                "text": text.strip(),
                "text_type": "plain",
                "operation": "query"
            }
        }

        async def _generate():
            url = "wss://openspeech.bytedance.com/api/v1/tts"
            audio_data = b""
            async with websockets.connect(url, ping_interval=None) as ws:
                await ws.send(json.dumps(request_payload))
                while True:
                    response = await ws.recv()
                    if isinstance(response, bytes):
                        # 二进制数据是音频
                        audio_data += response
                    else:
                        # JSON 数据是元数据
                        try:
                            result = json.loads(response)
                            code = result.get("code", -1)
                            if code == 3000:
                                # 合成完成
                                break
                            elif code != 3001:
                                # 3001 是继续，其他码是错误
                                log.error(f"火山引擎 TTS 错误: code={code}, msg={result.get('message', '')}")
                                break
                        except json.JSONDecodeError:
                            pass
            if audio_data:
                with open(tmp_file, "wb") as f:
                    f.write(audio_data)

        # 在新线程里跑 asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate())
        loop.close()

        if os.path.exists(tmp_file) and os.path.getsize(tmp_file) > 0:
            if output_devices:
                _play_on_devices(tmp_file, output_devices)
            else:
                _play_on_devices(tmp_file, [None])
            try:
                os.remove(tmp_file)
            except OSError:
                pass
        else:
            log.error("火山引擎 TTS 未生成音频数据，请检查 AppID/Token 是否正确")
    except Exception as e:
        log.error(f"火山引擎 TTS 朗读失败: {e}")


def stop():
    """停止当前朗读（pyttsx3 有效，edge/火山引擎模式无法中途停止）"""
    engine = _check_pyttsx3()
    if engine is not None:
        try:
            engine.stop()
        except Exception:
            pass
