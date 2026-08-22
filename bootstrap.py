"""
首次运行自检 + 自动下载模块
- 检查 whisper 模型是否存在，缺失则从国内镜像下载
- 检查 FFmpeg 是否可用
- 多镜像源自动切换 + 文件完整性校验 + 自动重试
- 用 PyQt5 显示下载进度
- 在 main.py 启动时调用
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

# 可用的 HuggingFace 镜像源（按优先级排序，会自动测速选最快）
HF_MIRRORS = [
    "https://hf-mirror.com",
    "https://huggingface.co",
]

# 各模型的 model.bin 期望大小（字节），用于完整性校验
EXPECTED_MODEL_SIZE = {
    "tiny": 75 * 1024 * 1024,
    "base": 150 * 1024 * 1024,
    "small": 460 * 1024 * 1024,
    "medium": 1500 * 1024 * 1024,
    "large": 3000 * 1024 * 1024,
}

# 缓存选中的最快镜像
_fastest_mirror = None


def get_models_dir() -> Path:
    """获取模型存储目录（%APPDATA%/vrc_trans/models/）"""
    if os.name == "nt":
        base = os.environ.get("APPDATA", str(Path.home()))
    else:
        base = str(Path.home() / ".config")
    d = Path(base) / "vrc_trans" / "models"
    d.mkdir(parents=True, exist_ok=True)
    return d


def check_model_exists(model_name: str = "small") -> bool:
    """检查模型文件是否存在且完整"""
    model_dir = get_models_dir() / model_name
    # faster-whisper 需要的关键文件
    required = ["model.bin", "config.json", "tokenizer.json"]
    for f in required:
        if not (model_dir / f).exists():
            return False
    # 校验 model.bin 大小（允许 20% 误差）
    model_bin = model_dir / "model.bin"
    expected = EXPECTED_MODEL_SIZE.get(model_name, 460 * 1024 * 1024)
    if model_bin.stat().st_size < expected * 0.8:
        print(f"[Bootstrap] model.bin 不完整: {model_bin.stat().st_size}B < 期望 {expected}B")
        return False
    # 如果有 vocabulary.txt 但没有 vocabulary.json，视为不完整（需要转换）
    vocab_txt = model_dir / "vocabulary.txt"
    vocab_json = model_dir / "vocabulary.json"
    if vocab_txt.exists() and (not vocab_json.exists() or vocab_json.stat().st_size == 0):
        return False
    return True


def find_fastest_mirror(timeout: float = 5.0) -> str:
    """测速选择最快的镜像源"""
    global _fastest_mirror
    if _fastest_mirror:
        return _fastest_mirror

    best_url = HF_MIRRORS[0]
    best_time = float('inf')
    for mirror in HF_MIRRORS:
        try:
            start = time.time()
            req = urllib.request.Request(
                f"{mirror}/api/models",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp.read(1024)
            elapsed = time.time() - start
            print(f"[Bootstrap] 镜像 {mirror} 延迟: {elapsed:.2f}s")
            if elapsed < best_time:
                best_time = elapsed
                best_url = mirror
        except Exception as e:
            print(f"[Bootstrap] 镜像 {mirror} 不可用: {e}")

    _fastest_mirror = best_url
    print(f"[Bootstrap] 选择最快镜像: {best_url}")
    return best_url


def _download_file(url: str, filepath: Path, max_retries: int = 2) -> bool:
    """下载单个文件，支持自动重试"""
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                print(f"[Bootstrap] 重试 ({attempt}/{max_retries})...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as response:
                total = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 65536
                with open(filepath, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
            # 校验下载完整性
            if total > 0 and downloaded < total:
                raise IOError(f"下载不完整: {downloaded}/{total}")
            return True
        except Exception as e:
            print(f"[Bootstrap] 下载失败: {e}")
            if filepath.exists():
                try:
                    filepath.unlink()
                except OSError:
                    pass
            if attempt < max_retries:
                time.sleep(1)
    return False


def _convert_vocabulary(model_dir: Path) -> bool:
    """将 vocabulary.txt 转换为 ctranslate2 需要的 vocabulary.json（数组格式）"""
    vocab_txt = model_dir / "vocabulary.txt"
    vocab_json = model_dir / "vocabulary.json"

    if not vocab_txt.exists():
        return False
    if vocab_json.exists() and vocab_json.stat().st_size > 0:
        # 已存在且非空，验证格式
        try:
            with open(vocab_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 1000:
                return True  # 格式正确，无需转换
        except Exception:
            pass  # 格式错误，重新转换

    try:
        print("[Bootstrap] 转换 vocabulary.txt -> vocabulary.json...")
        with open(vocab_txt, "r", encoding="utf-8") as f:
            tokens = [line.rstrip("\n") for line in f]
        # ctranslate2 期望数组格式：["token1", "token2", ...]，索引即 ID
        with open(vocab_json, "w", encoding="utf-8") as f:
            json.dump(tokens, f, ensure_ascii=False)
        # 验证转换结果
        with open(vocab_json, "r", encoding="utf-8") as f:
            verify = json.load(f)
        if not isinstance(verify, list) or len(verify) != len(tokens):
            raise ValueError(f"转换结果异常: {type(verify)}, len={len(verify) if isinstance(verify, list) else 'N/A'}")
        print(f"[Bootstrap] 转换完成，共 {len(tokens)} 个 token，已验证")
        return True
    except Exception as e:
        print(f"[Bootstrap] 转换 vocabulary 失败: {e}")
        if vocab_json.exists() and vocab_json.stat().st_size == 0:
            try:
                vocab_json.unlink()
            except OSError:
                pass
        return False


def _is_file_complete(filename: str, filepath: Path, model_name: str) -> bool:
    """检查文件是否完整，不完整的需要重新下载"""
    if not filepath.exists() or filepath.stat().st_size == 0:
        return False
    # model.bin：检查大小是否 >= 期望的 80%
    if filename == "model.bin":
        expected = EXPECTED_MODEL_SIZE.get(model_name, 460 * 1024 * 1024)
        if filepath.stat().st_size < expected * 0.8:
            print(f"[Bootstrap] {filename} 不完整 ({filepath.stat().st_size}B)，重新下载")
            return False
        return True
    # JSON 文件：检查能否正常解析
    if filename.endswith(".json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                json.load(f)
            return True
        except Exception:
            print(f"[Bootstrap] {filename} 损坏，重新下载")
            return False
    # 其他文件：存在且非空即可
    return True


def download_model(model_name: str = "small", progress_callback=None) -> bool:
    """
    从最快的 HuggingFace 镜像下载 faster-whisper 模型
    自动测速选源，失败自动切换，文件完整性校验
    """
    model_dir = get_models_dir() / model_name
    model_dir.mkdir(parents=True, exist_ok=True)

    # 需要下载的文件
    required_files = ["model.bin", "config.json", "tokenizer.json"]
    optional_files = ["vocabulary.txt", "preprocessor_config.json"]
    files = required_files + optional_files

    estimated_total = EXPECTED_MODEL_SIZE.get(model_name, 500 * 1024 * 1024)
    total_downloaded = 0

    # 先统计已存在的文件大小
    for filename in files:
        filepath = model_dir / filename
        if filepath.exists() and filepath.stat().st_size > 0:
            total_downloaded += filepath.stat().st_size

    # 按顺序尝试线路：A线路失败 → B线路 → 备用线路
    mirrors_to_try = HF_MIRRORS

    for mirror in mirrors_to_try:
        base_url = f"{mirror}/Systran/faster-whisper-{model_name}/resolve/main"
        all_success = True

        for filename in files:
            filepath = model_dir / filename
            # 校验文件完整性，完整的跳过，不完整的重新下载
            if _is_file_complete(filename, filepath, model_name):
                continue

            url = f"{base_url}/{filename}"
            print(f"[Bootstrap] 从 {mirror} 下载 {filename}...")

            if _download_file(url, filepath):
                total_downloaded += filepath.stat().st_size
                if progress_callback:
                    progress_callback(total_downloaded, estimated_total)
            else:
                if filename in optional_files:
                    print(f"[Bootstrap] {filename} 为可选文件，跳过")
                    continue
                all_success = False
                break

        if all_success:
            # 校验 model.bin 完整性
            model_bin = model_dir / "model.bin"
            expected = EXPECTED_MODEL_SIZE.get(model_name, 460 * 1024 * 1024)
            if model_bin.stat().st_size < expected * 0.8:
                print(f"[Bootstrap] model.bin 不完整，删除重新下载")
                try:
                    model_bin.unlink()
                except OSError:
                    pass
                continue

            # 转换 vocabulary
            _convert_vocabulary(model_dir)
            return True

    return False


# ============================================================
# Sherpa-onnx 模型下载（统一管理，替代 speech_recognizer.py 里的旧逻辑）
# ============================================================

def get_sherpa_model_dir(model_id: str) -> Path:
    """获取 sherpa 模型存储目录"""
    return get_models_dir() / model_id


def check_sherpa_model_exists(model_id: str) -> bool:
    """检查 sherpa 模型是否存在且完整（使用 file_patterns 验证）"""
    try:
        from sherpa_recognizer import get_model_info, verify_model_files
    except ImportError:
        # fallback：直接检查目录是否存在且非空
        model_dir = get_sherpa_model_dir(model_id)
        if not model_dir.is_dir():
            return False
        return any(model_dir.iterdir())

    model_info = get_model_info(model_id)
    if model_info is None:
        print(f"[Bootstrap] 未知模型 ID: {model_id}")
        return False

    model_dir = get_sherpa_model_dir(model_id)
    if not model_dir.is_dir():
        return False

    # 使用增强的验证函数（支持 file_patterns）
    ok, msg = verify_model_files(str(model_dir), model_info)
    if not ok:
        print(f"[Bootstrap] 模型 {model_id} 文件不完整: {msg}")
    return ok


def download_sherpa_model(model_id: str, progress_callback=None, custom_mirrors=None, cancel_event=None, status_callback=None, total_timeout=600) -> bool:
    """
    从 GitHub release 下载 sherpa-onnx 模型
    - 10+ 条国内镜像自动切换
    - 连接超时 15 秒自动切换
    - 下载速度过慢（<30KB/s 持续 8 秒）自动切换
    - 支持断点续传
    - 所有镜像失败后打印手动下载链接
    """
    try:
        from sherpa_recognizer import get_model_info
    except ImportError:
        print("[Bootstrap] 无法导入 sherpa_recognizer，下载失败")
        return False

    model_info = get_model_info(model_id)
    if model_info is None:
        print(f"[Bootstrap] 未知模型 ID: {model_id}")
        return False

    model_dir = get_sherpa_model_dir(model_id)
    model_dir.mkdir(parents=True, exist_ok=True)

    if check_sherpa_model_exists(model_id):
        print(f"[Bootstrap] 模型 {model_id} 已存在，跳过下载")
        return True

    tar_filename = model_info["tar_filename"]
    base_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models"
    official_url = f"{base_url}/{tar_filename}"

    # 镜像前缀列表（按优先级排序，国内可用的 GitHub 加速镜像）
    mirror_prefixes = [
        "https://ghfast.top/",
        "https://gh.llkk.cc/",
        "https://ghproxy.net/",
        "https://mirror.ghproxy.com/",
        "https://gh-proxy.com/",
        "https://gh.api.99988866.xyz/",
        "https://cors.isteed.cc/",
        "https://github.moeyy.xyz/",
        "https://gh.ddzds.cc/",
        "https://gh.con.sh/",
        "https://hub.gitmirror.com/",
        "https://kkgithub.com/",
    ]

    # 尝试从配置读取自定义镜像
    if custom_mirrors is None:
        try:
            from config import Config
            _cfg = Config()
            custom_mirrors = _cfg.get("custom_download_mirrors", [])
        except Exception:
            custom_mirrors = []

    # 用户自定义镜像（如果有）
    if custom_mirrors:
        mirror_prefixes = custom_mirrors + mirror_prefixes

    # 构建所有下载 URL（镜像 + 官方直连）
    tar_urls = []
    for prefix in mirror_prefixes:
        if prefix.endswith("kkgithub.com/"):
            # kkgithub 是域名替换，不是前缀代理
            tar_urls.append(f"https://kkgithub.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{tar_filename}")
        else:
            tar_urls.append(f"{prefix}{official_url}")
    tar_urls.append(official_url)  # 最后试官方直连

    import tarfile
    import tempfile
    import shutil
    import socket

    tar_path = os.path.join(tempfile.gettempdir(), f"vrc_sherpa_{model_id}.tar.bz2")
    CONNECT_TIMEOUT = 15  # 连接超时（秒）
    READ_TIMEOUT = 60     # 读取超时（秒）
    MIN_SPEED = 30 * 1024  # 最低速度 30KB/s
    SLOW_DURATION = 8       # 持续低速 8 秒则切换

    def _download_with_timeout(url, filepath):
        """带超时和速度检测的下载，支持断点续传"""
        existing_size = 0
        if os.path.exists(filepath):
            existing_size = os.path.getsize(filepath)

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        if existing_size > 0:
            req.add_header("Range", f"bytes={existing_size}-")

        try:
            resp = urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT)
        except socket.timeout:
            print(f"  连接超时（{CONNECT_TIMEOUT}秒），切换下一条线路")
            return False
        except Exception as e:
            print(f"  连接失败: {e}")
            return False

        # 获取总大小
        total_size = existing_size
        content_length = resp.headers.get("Content-Length")
        if content_length:
            if existing_size > 0 and resp.status == 206:
                total_size = existing_size + int(content_length)
            else:
                total_size = int(content_length)
                existing_size = 0  # 服务器不支持断点，重新下

        mode = "ab" if existing_size > 0 and resp.status == 206 else "wb"
        downloaded = existing_size
        chunk_size = 65536
        slow_start_time = None
        last_check_time = time.time()
        last_check_bytes = downloaded

        _start_ts = time.time()
        try:
            with open(filepath, mode) as f:
                while True:
                    if cancel_event is not None and cancel_event.is_set():
                        print("\n  用户取消下载")
                        return False
                    if total_timeout and (time.time() - _start_ts) > total_timeout:
                        print("\n  总超时，放弃下载")
                        return False
                    try:
                        chunk = resp.read(chunk_size)
                    except socket.timeout:
                        print(f"\n  读取超时，切换下一条线路")
                        return False
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    # 进度回调
                    if progress_callback and total_size > 0:
                        progress_callback(downloaded, total_size)

                    # 控制台进度
                    if total_size > 0:
                        pct = min(100, downloaded * 100 // total_size)
                        mb = downloaded // 1024 // 1024
                        total_mb = total_size // 1024 // 1024
                        print(f"\r[Bootstrap] 下载进度: {pct}% ({mb}/{total_mb}MB)", end="", flush=True)

                    # 速度检测
                    now = time.time()
                    elapsed = now - last_check_time
                    if elapsed >= 2:  # 每 2 秒检测一次速度
                        speed = (downloaded - last_check_bytes) / elapsed
                        last_check_time = now
                        last_check_bytes = downloaded
                        if speed < MIN_SPEED:
                            if slow_start_time is None:
                                slow_start_time = now
                            elif now - slow_start_time >= SLOW_DURATION:
                                print(f"\n  速度过慢（{int(speed//1024)}KB/s）持续{SLOW_DURATION}秒，切换下一条线路")
                                return False
                        else:
                            slow_start_time = None

            # 下载完成校验
            if total_size > 0 and downloaded < total_size:
                print(f"\n  下载不完整: {downloaded}/{total_size}")
                return False
            return True
        except Exception as e:
            print(f"\n  下载出错: {e}")
            return False

    def _extract_and_verify():
        """解压并验证模型文件（复制所有文件，保留子目录结构）"""
        tmp_dir = tempfile.mkdtemp()
        try:
            with tarfile.open(tar_path, 'r:bz2') as tar:
                # 安全解压：检查路径遍历
                for member in tar.getmembers():
                    member_path = os.path.join(tmp_dir, member.name)
                    if not member_path.startswith(os.path.abspath(tmp_dir)):
                        print(f"[Bootstrap] 跳过不安全的路径: {member.name}")
                        continue
                    tar.extract(member, tmp_dir)
        except Exception as e:
            print(f"[Bootstrap] 解压失败: {e}")
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return False

        # 复制所有文件到模型目录（保留子目录结构）
        copied = 0
        for root, dirs, files in os.walk(tmp_dir):
            for f in files:
                src = os.path.join(root, f)
                # 计算相对路径，保留子目录结构
                rel_path = os.path.relpath(src, tmp_dir)
                dst = os.path.join(model_dir, rel_path)
                # 确保目标目录存在
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    shutil.copy2(src, dst)
                    copied += 1
                except Exception as e:
                    print(f"[Bootstrap] 复制文件失败 {rel_path}: {e}")

        print(f"[Bootstrap] 共复制 {copied} 个文件到模型目录")

        # 验证必需文件
        try:
            from sherpa_recognizer import verify_model_files
            ok, msg = verify_model_files(str(model_dir), model_info)
            if not ok:
                print(f"[Bootstrap] 模型文件验证失败: {msg}")
                shutil.rmtree(tmp_dir, ignore_errors=True)
                return False
        except ImportError:
            # fallback：检查 required_files
            for required_file in model_info.get("required_files", []):
                found = False
                for root, dirs, files in os.walk(model_dir):
                    if required_file in files:
                        found = True
                        break
                if not found:
                    print(f"[Bootstrap] 缺少必需文件: {required_file}")
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                    return False

        shutil.rmtree(tmp_dir, ignore_errors=True)
        try:
            os.remove(tar_path)
        except OSError:
            pass
        return True

    # 主下载循环：逐条镜像尝试
    downloaded = False
    _dl_start = time.time()
    for i, url in enumerate(tar_urls):
        if cancel_event is not None and cancel_event.is_set():
            print("\n[Bootstrap] 下载已取消")
            return False
        if total_timeout and (time.time() - _dl_start) > total_timeout:
            print("\n[Bootstrap] 总下载超时（{}秒），放弃".format(total_timeout))
            break
        print(f"\n[Bootstrap] 尝试线路 {i+1}/{len(tar_urls)}: {url[:70]}...")
        if status_callback:
            try:
                status_callback(i+1, len(tar_urls), url)
            except Exception:
                pass
        if _download_with_timeout(url, tar_path):
            print("\n[Bootstrap] 下载完成，解压中...")
            if _extract_and_verify():
                print(f"[Bootstrap] 模型 {model_id} 下载完成")
                downloaded = True
                break
            else:
                print("[Bootstrap] 解压/验证失败，文件可能损坏，删除后尝试下一条线路")
                if os.path.exists(tar_path):
                    try:
                        os.remove(tar_path)
                    except OSError:
                        pass
        else:
            # 下载失败（超时/断流/速度过慢），保留已下载部分用于断点续传
            existing = os.path.getsize(tar_path) if os.path.exists(tar_path) else 0
            if existing > 0:
                print(f"  已保留 {existing // 1024 // 1024}MB 用于断点续传")
            # 不删除 tar_path，下一条线路会尝试 Range 续传

    if not downloaded:
        print("\n" + "="*60)
        print("[Bootstrap] 所有镜像下载失败！")
        print("="*60)
        print(f"模型: {model_info['name']}")
        print(f"文件: {tar_filename}")
        print(f"目标目录: {model_dir}")
        print("")
        print("手动下载方法：")
        print(f"1. 用浏览器或下载工具打开: {official_url}")
        print(f"   （国内可加前缀: https://ghproxy.net/{official_url}）")
        print(f"2. 下载完成后解压，找到以下文件:")
        for rf in model_info["required_files"]:
            print(f"   - {rf}")
        print(f"3. 把这些文件放到: {model_dir}")
        print("4. 重新运行程序")
        print("="*60)
        return False

    if check_sherpa_model_exists(model_id):
        print(f"[Bootstrap] 模型 {model_id} 验证通过")
        return True
    else:
        print(f"[Bootstrap] 模型 {model_id} 验证失败")
        return False


def check_ffmpeg() -> bool:
    """检查 FFmpeg 是否可用"""
    import shutil
    return shutil.which("ffmpeg") is not None


def download_ffmpeg(progress_callback=None) -> bool:
    """下载 FFmpeg（Windows 专用）"""
    if os.name != "nt":
        return False

    ffmpeg_dir = get_models_dir().parent / "ffmpeg"
    ffmpeg_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = ffmpeg_dir / "ffmpeg.exe"

    if ffmpeg_exe.exists():
        return True

    # 使用多个镜像源
    ffmpeg_urls = [
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
        "https://ghproxy.com/https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    ]

    for url in ffmpeg_urls:
        try:
            print(f"[Bootstrap] 下载 FFmpeg: {url}...")
            import zipfile
            zip_path = ffmpeg_dir / "ffmpeg.zip"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as response:
                total = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 8192
                with open(zip_path, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total)
            # 解压
            print("[Bootstrap] 解压 FFmpeg...")
            with zipfile.ZipFile(zip_path, "r") as zf:
                for name in zf.namelist():
                    if name.endswith("bin/ffmpeg.exe"):
                        with zf.open(name) as src, open(ffmpeg_exe, "wb") as dst:
                            dst.write(src.read())
                        break
            try:
                zip_path.unlink()
            except OSError:
                pass
            if ffmpeg_exe.exists():
                return True
        except Exception as e:
            print(f"[Bootstrap] FFmpeg 下载失败 ({url}): {e}")
            continue

    return False



def check_and_fix_numpy():
    """检查 NumPy 版本，如果 >=2 且使用 faster-whisper 相关依赖，自动降级到 <2，降级成功后自动重启"""
    try:
        import numpy as np
        version = tuple(int(x) for x in np.__version__.split('.')[:2])
        if version >= (2, 0):
            # 检查是否已经重启过（避免无限循环）
            import os
            if os.environ.get("VRC_TRANS_NUMPY_RESTARTED") == "1":
                print("[Bootstrap] NumPy 仍为 2.x，已重启过一次，跳过自动降级（请手动执行: pip install numpy<2）")
                return False
            
            print(f"[Bootstrap] 检测到 NumPy {np.__version__}，ctranslate2/faster-whisper 可能不兼容，尝试自动降级...")
            import subprocess
            import sys
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "numpy<2", "--quiet"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print("[Bootstrap] NumPy 降级成功，需要重启程序使变更生效")
                # 标记需要重启（由 main.py 负责执行重启，确保托盘等资源正确清理）
                os.environ["VRC_TRANS_NEED_RESTART"] = "1"
                os.environ["VRC_TRANS_RESTART_REASON"] = "numpy_downgraded"
                return True
            else:
                print(f"[Bootstrap] NumPy 降级失败: {result.stderr}")
                print("[Bootstrap] 请手动执行: pip install numpy<2")
                return False
        else:
            print(f"[Bootstrap] NumPy 版本 {np.__version__}，兼容")
            return True
    except ImportError:
        print("[Bootstrap] NumPy 未安装，跳过检查")
        return True
    except Exception as e:
        print(f"[Bootstrap] NumPy 检查失败: {e}")
        return False


def check_and_fix_noisereduce():
    """检查 noisereduce 版本，<3.0 则自动升级（旧版用了已移除的 np.long，与 NumPy 1.24+ 不兼容）"""
    try:
        # 用 importlib.metadata 查版本，不导入 noisereduce（旧版导入时就会崩）
        from importlib.metadata import version as get_version, PackageNotFoundError
        try:
            version_str = get_version("noisereduce")
        except PackageNotFoundError:
            print("[Bootstrap] noisereduce 未安装，降噪功能不可用（可选依赖）")
            return True
        
        version_tuple = tuple(int(x) for x in version_str.split('.')[:2])
        if version_tuple < (3, 0):
            print(f"[Bootstrap] 检测到 noisereduce {version_str}（过旧，用了已移除的 np.long），自动升级...")
            import subprocess
            import sys
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "noisereduce>=3.0.0", "--quiet"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print("[Bootstrap] noisereduce 升级成功，请重启程序使变更生效")
                return True
            else:
                print(f"[Bootstrap] noisereduce 升级失败: {result.stderr}")
                print("[Bootstrap] 请手动执行: pip install --upgrade noisereduce")
                return False
        else:
            print(f"[Bootstrap] noisereduce 版本 {version_str}，兼容")
            return True
    except Exception as e:
        print(f"[Bootstrap] noisereduce 检查失败: {e}")
        # 检查失败也尝试升级
        try:
            import subprocess
            import sys
            print("[Bootstrap] 尝试自动升级 noisereduce...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "noisereduce>=3.0.0", "--quiet"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print("[Bootstrap] noisereduce 升级成功，请重启程序使变更生效")
                return True
        except Exception:
            pass
        print("[Bootstrap] 请手动执行: pip install --upgrade noisereduce")
        return False


def check_and_fix_scipy():
    """检查 noisereduce 是否可用，不可用则尝试自动升级一次，失败就放弃（避免无限循环）"""
    import os
    # 如果已经尝试过修复，就不再尝试，直接用内置降噪
    if os.environ.get("VRC_TRANS_SCIPY_FIX_ATTEMPTED") == "1":
        print("[Bootstrap] 已尝试过修复 noisereduce，仍不可用，使用内置降噪")
        return False
    
    try:
        # 先实际导入测试 noisereduce
        try:
            import noisereduce as nr
            print(f"[Bootstrap] noisereduce {getattr(nr, '__version__', '?')} 可用")
            return True
        except Exception as e:
            err_msg = str(e)
            print(f"[Bootstrap] noisereduce 不可用: {type(e).__name__}: {err_msg}")
            print("[Bootstrap] 尝试自动升级 scipy + noisereduce...")
        
        # 标记已尝试修复（避免重启后无限循环）
        os.environ["VRC_TRANS_SCIPY_FIX_ATTEMPTED"] = "1"
        
        # 自动升级 scipy + noisereduce
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "scipy>=1.11", "noisereduce>=3.0.0", "--quiet"],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            print("[Bootstrap] scipy + noisereduce 升级成功，需要重启程序使变更生效")
            # 标记需要重启
            os.environ["VRC_TRANS_NEED_RESTART"] = "1"
            os.environ["VRC_TRANS_RESTART_REASON"] = "scipy_upgraded"
            return True
        else:
            print(f"[Bootstrap] 自动升级失败: {result.stderr}")
            print("[Bootstrap] 将使用内置降噪。可手动执行: pip install --upgrade scipy noisereduce")
            return False
    except Exception as e:
        print(f"[Bootstrap] scipy/noisereduce 检查失败: {e}")
        print("[Bootstrap] 将使用内置降噪")
        return False

def run_bootstrap(model_name: str = "small", show_gui: bool = True,
                  engine: str = "sherpa", sherpa_model_id: str = "streaming-paraformer-bilingual-zh-en") -> bool:
    """
    运行首次启动自检
    根据引擎类型检查对应的模型（sherpa 检查 sherpa 模型，faster 检查 whisper 模型）
    返回 True 表示可以继续启动
    """
    # 检查 NumPy 版本（faster-whisper/ctranslate2 兼容）
    check_and_fix_numpy()
    # 检查 noisereduce 版本（降噪可选依赖，旧版与 NumPy 1.24+ 不兼容）
    check_and_fix_noisereduce()
    # 检查 scipy 版本（noisereduce 依赖，旧版用了 np.long）
    check_and_fix_scipy()
    issues = []

    # 根据引擎检查对应的模型
    if engine == "sherpa":
        if not check_sherpa_model_exists(sherpa_model_id):
            issues.append(f"sherpa 模型 ({sherpa_model_id})")
    else:
        if not check_model_exists(model_name):
            issues.append(f"whisper {model_name} 模型")

    if not check_ffmpeg():
        issues.append("FFmpeg")

    if not issues:
        print("[Bootstrap] 所有依赖检查通过")
        return True

    print(f"[Bootstrap] 缺失: {', '.join(issues)}")

    if not show_gui:
        if engine == "sherpa":
            sherpa_issue = next((i for i in issues if "sherpa" in i), None)
            if sherpa_issue:
                print(f"[Bootstrap] 自动下载 sherpa 模型 {sherpa_model_id}...")
                download_sherpa_model(sherpa_model_id)
        else:
            whisper_issue = next((i for i in issues if "whisper" in i), None)
            if whisper_issue:
                print(f"[Bootstrap] 自动下载 {model_name} 模型...")
                download_model(model_name)
        return True

    # GUI 模式
    try:
        from PyQt5.QtWidgets import (
            QApplication, QDialog, QVBoxLayout, QLabel,
            QProgressBar
        )
        from PyQt5.QtCore import Qt, QThread, pyqtSignal

        class DownloadThread(QThread):
            progress = pyqtSignal(int, int)
            finished = pyqtSignal(bool)

            def run(self):
                success = True
                if engine == "sherpa":
                    sherpa_issue = next((i for i in issues if "sherpa" in i), None)
                    if sherpa_issue:
                        if not download_sherpa_model(sherpa_model_id, lambda d, t: self.progress.emit(d, t)):
                            success = False
                else:
                    whisper_issue = next((i for i in issues if "whisper" in i), None)
                    if whisper_issue:
                        if not download_model(model_name, lambda d, t: self.progress.emit(d, t)):
                            success = False
                self.finished.emit(success)

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        dialog = QDialog()
        dialog.setWindowTitle("首次运行初始化")
        dialog.setFixedWidth(400)
        layout = QVBoxLayout(dialog)
        label = QLabel(f"正在下载必要资源...\n\n缺失: {', '.join(issues)}")
        label.setWordWrap(True)
        layout.addWidget(label)
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        layout.addWidget(progress_bar)
        status_label = QLabel("")
        layout.addWidget(status_label)
        dialog.setLayout(layout)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

        thread = DownloadThread()

        def on_progress(d, t):
            if t > 0:
                pct = int(d / t * 100)
                progress_bar.setValue(pct)
                status_label.setText(f"{d // 1024 // 1024}MB / {t // 1024 // 1024}MB")

        def on_finished(success):
            dialog.accept()

        thread.progress.connect(on_progress)
        thread.finished.connect(on_finished)
        thread.start()
        dialog.exec_()
        return True
    except Exception as e:
        print(f"[Bootstrap] GUI 初始化失败: {e}")
        if engine == "sherpa":
            sherpa_issue = next((i for i in issues if "sherpa" in i), None)
            if sherpa_issue:
                download_sherpa_model(sherpa_model_id)
        else:
            whisper_issue = next((i for i in issues if "whisper" in i), None)
            if whisper_issue:
                download_model(model_name)
        return True


# ============================================================
# VB-CABLE 虚拟音频线自动下载安装
# ============================================================
def check_vb_cable_installed():
    """检测系统中是否已安装 VB-CABLE（或其他虚拟音频线）"""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        for d in devices:
            name = d.get("name", "").lower()
            if "cable" in name or "virtual" in name or "vb-audio" in name:
                return True
    except Exception:
        pass
    return False


def _get_default_audio_devices():
    """获取当前默认播放/录音设备的索引和名称"""
    info = {"playback": None, "recording": None}
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        default_output = sd.default.device[1] if len(sd.default.device) > 1 else None
        default_input = sd.default.device[0] if len(sd.default.device) > 0 else None
        if default_output is not None and default_output < len(devices):
            info["playback"] = (default_output, devices[default_output].get("name", ""))
        if default_input is not None and default_input < len(devices):
            info["recording"] = (default_input, devices[default_input].get("name", ""))
    except Exception as e:
        print(f"[Bootstrap] 获取默认音频设备失败: {e}")
    return info


def _restore_default_audio_devices(saved_info):
    """尝试恢复默认音频设备（进程级别）"""
    if not saved_info:
        return False
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        for device_type, (saved_idx, saved_name) in saved_info.items():
            if not saved_name:
                continue
            for i, d in enumerate(devices):
                if d.get("name", "") == saved_name:
                    if device_type == "playback":
                        sd.default.device = (sd.default.device[0], i)
                    else:
                        sd.default.device = (i, sd.default.device[1])
                    break
        return True
    except Exception as e:
        print(f"[Bootstrap] 恢复默认音频设备失败: {e}")
        return False


def install_vb_cable(parent=None):
    """下载并安装 VB-CABLE 虚拟音频线，安装后提示恢复默认音频设备"""
    import os
    import sys
    import tempfile
    import zipfile
    import urllib.request

    if os.name != "nt":
        if parent:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(parent, "VB-CABLE", "VB-CABLE 仅支持 Windows 系统。")
        return False

    if check_vb_cable_installed():
        if parent:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(parent, "VB-CABLE", "检测到系统中已有虚拟音频设备，无需重复安装。")
        return True

    download_url = "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack43.zip"
    mirror_prefixes = ["https://ghfast.top/", "https://ghproxy.net/", "https://mirror.ghproxy.com/"]
    saved_devices = _get_default_audio_devices()
    zip_path = os.path.join(tempfile.gettempdir(), "VBCABLE_Driver_Pack43.zip")
    extract_dir = os.path.join(tempfile.gettempdir(), "vbcable_install")

    from PyQt5.QtWidgets import QProgressDialog, QMessageBox, QApplication
    from PyQt5.QtCore import Qt, QThread, pyqtSignal

    class DownloadThread(QThread):
        progress = pyqtSignal(int, int)
        finished_ok = pyqtSignal(bool, str)

        def run(self):
            urls = [download_url] + [p + download_url for p in mirror_prefixes]
            for url in urls:
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        total = int(resp.headers.get("Content-Length", 0))
                        downloaded = 0
                        with open(zip_path, "wb") as f:
                            while True:
                                chunk = resp.read(65536)
                                if not chunk:
                                    break
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total > 0:
                                    self.progress.emit(downloaded, total)
                    if total > 0 and os.path.getsize(zip_path) < total * 0.9:
                        raise IOError("下载不完整")
                    self.finished_ok.emit(True, zip_path)
                    return
                except Exception as e:
                    print(f"[Bootstrap] VB-CABLE 下载失败: {e}")
                    continue
            self.finished_ok.emit(False, "所有下载源均失败")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    dlg = QProgressDialog("正在下载 VB-CABLE 虚拟音频线驱动...", "取消", 0, 100, parent)
    dlg.setWindowTitle("安装 VB-CABLE")
    dlg.setWindowModality(Qt.ApplicationModal)
    dlg.setMinimumDuration(0)
    dlg.setAutoClose(False)
    dlg.setAutoReset(False)
    dlg.setMinimumWidth(400)

    cancel_flag = {"cancelled": False}
    dlg.canceled.connect(lambda: cancel_flag.__setitem__("cancelled", True))

    thread = DownloadThread()
    result = {"ok": False, "path": ""}

    def on_progress(d, t):
        if t > 0:
            dlg.setValue(int(d / t * 100))
            dlg.setLabelText(f"正在下载 VB-CABLE...\n{d // 1024}KB / {t // 1024}KB")

    def on_finished(ok, path):
        result["ok"] = ok
        result["path"] = path
        dlg.close()

    thread.progress.connect(on_progress)
    thread.finished_ok.connect(on_finished)
    thread.start()
    dlg.exec_()

    if cancel_flag["cancelled"]:
        thread.wait(2000)
        return False

    if not result["ok"]:
        QMessageBox.warning(parent, "下载失败", "VB-CABLE 下载失败。\n\n请手动访问 https://vb-audio.com/Cable/ 下载安装。")
        return False

    try:
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)
    except Exception as e:
        QMessageBox.warning(parent, "解压失败", f"解压失败: {e}\n请手动安装。")
        return False

    setup_exe = None
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            if f.lower() in ("vbcable_setup_x64.exe", "vbcable_setup.exe"):
                setup_exe = os.path.join(root, f)
                break
        if setup_exe:
            break

    if not setup_exe:
        QMessageBox.warning(parent, "安装失败", "未找到安装程序，请手动安装。")
        return False

    reply = QMessageBox.question(
        parent, "安装 VB-CABLE",
        "即将以管理员身份运行 VB-CABLE 安装程序。\n\n"
        "安装过程中会弹出 UAC 提示，请点击「是」继续。\n"
        "安装完成后请点击安装程序里的「Install Driver」按钮。\n\n"
        "注意：安装驱动后可能需要重启电脑才能生效。\n\n是否继续？",
        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
    )
    if reply != QMessageBox.Yes:
        return False

    try:
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(None, "runas", setup_exe, "", None, 1)
    except Exception as e:
        print(f"[Bootstrap] 启动安装程序失败: {e}")
        try:
            os.startfile(extract_dir)
        except Exception:
            pass
        QMessageBox.information(parent, "手动安装", f"无法自动启动安装程序。\n\n请手动打开文件夹：\n{extract_dir}\n\n右键 VBCABLE_Setup_x64.exe → 以管理员身份运行。")
        return False

    QMessageBox.information(parent, "安装中", "VB-CABLE 安装程序已启动，请在弹出的窗口中完成安装。\n\n安装完成后点击「确定」。")

    _restore_default_audio_devices(saved_devices)

    try:
        os.remove(zip_path)
    except Exception:
        pass

    if check_vb_cable_installed():
        QMessageBox.information(parent, "安装完成",
                                "VB-CABLE 安装成功！\n\n"
                                "注意：VB-CABLE 安装后可能会自动把系统默认音频设备改成 CABLE。\n"
                                "如果发现声音不对，请右键系统托盘音量图标 → 声音设置，把默认设备改回原来的。\n\n"
                                "在 VRChat 中：麦克风选择「CABLE Output」，即可用翻译语音说话。")
        return True
    else:
        QMessageBox.warning(parent, "安装未完成", "未检测到 VB-CABLE 设备。\n\n可能需要重启电脑后驱动才会生效。\n重启后请重新运行程序。")
        return False


if __name__ == "__main__":
    run_bootstrap(show_gui=False)
