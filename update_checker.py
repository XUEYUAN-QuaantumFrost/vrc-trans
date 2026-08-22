"""
自动更新检查模块
启动时检查是否有新版本，有则提示用户
版本信息存储在远程 JSON 文件中
"""
import json
import threading
import urllib.request
import logger

log = logger.get_logger("update")

# 当前版本
CURRENT_VERSION = "2.3.0"

# 远程版本信息 URL（可替换为实际地址）
VERSION_CHECK_URL = "https://raw.githubusercontent.com/vrc-translate/vrc_trans/main/version.json"
# 备用检查 URL
VERSION_CHECK_URL_BACKUP = "https://gitee.com/vrc-translate/vrc_trans/raw/main/version.json"

# 检查超时（秒）
CHECK_TIMEOUT = 8


def check_for_update(callback=None):
    """
    检查更新（异步执行）
    callback(has_update: bool, latest_version: str, download_url: str, release_notes: str)
    """
    def _worker():
        try:
            result = _fetch_version_info()
            if result is None:
                log.info("更新检查：无法获取版本信息")
                if callback:
                    callback(False, "", "", "")
                return

            latest = result.get("version", "")
            download_url = result.get("download_url", "")
            release_notes = result.get("release_notes", "")

            has_update = _compare_versions(latest, CURRENT_VERSION) > 0
            if has_update:
                log.info(f"发现新版本: {CURRENT_VERSION} -> {latest}")
            else:
                log.info(f"当前已是最新版本: {CURRENT_VERSION}")

            if callback:
                callback(has_update, latest, download_url, release_notes)
        except Exception as e:
            log.error(f"更新检查失败: {e}")
            if callback:
                callback(False, "", "", "")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def _fetch_version_info() -> dict:
    """从远程获取版本信息，依次尝试主 URL 和备用 URL"""
    for url in [VERSION_CHECK_URL, VERSION_CHECK_URL_BACKUP]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "vrc-translate-updater"})
            with urllib.request.urlopen(req, timeout=CHECK_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "version" in data:
                    return data
        except Exception as e:
            log.debug(f"从 {url} 获取版本信息失败: {e}")
            continue
    return None


def _compare_versions(v1: str, v2: str) -> int:
    """
    比较版本号
    返回: 1=v1>v2, -1=v1<v2, 0=相等
    """
    def _parse(v):
        parts = []
        for p in v.strip().split("."):
            try:
                parts.append(int(p))
            except ValueError:
                parts.append(0)
        return parts

    a = _parse(v1)
    b = _parse(v2)
    # 补齐长度
    max_len = max(len(a), len(b))
    a += [0] * (max_len - len(a))
    b += [0] * (max_len - len(b))
    for x, y in zip(a, b):
        if x > y:
            return 1
        if x < y:
            return -1
    return 0
