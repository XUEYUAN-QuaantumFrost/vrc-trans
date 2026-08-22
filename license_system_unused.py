"""
注册码/授权系统（基础版）
- 基于机器码的本地授权验证
- 授权码格式：XXXX-XXXX-XXXX-XXXX
- 机器码基于 CPU ID + 硬盘序列号 + MAC 地址生成
- 授权信息存储在配置目录下的 license.json
"""
import os
import json
import hashlib
import platform
import uuid
from pathlib import Path


def get_config_dir() -> Path:
    """获取配置目录"""
    if os.name == "nt":
        base = os.environ.get("APPDATA", str(Path.home()))
    else:
        base = str(Path.home() / ".config")
    return Path(base) / "vrc_trans"


def get_machine_code() -> str:
    """
    生成机器码（基于 CPU ID + 硬盘序列号 + MAC 地址）
    返回 16 位十六进制字符串
    """
    try:
        # MAC 地址
        mac = uuid.getnode()
        # 主机名
        hostname = platform.node()
        # 平台信息
        system = platform.system()
        machine = platform.machine()
        # CPU 信息
        processor = platform.processor()

        # 组合生成机器码
        raw = f"{mac}:{hostname}:{system}:{machine}:{processor}"
        hash_obj = hashlib.md5(raw.encode("utf-8"))
        return hash_obj.hexdigest()[:16].upper()
    except Exception:
        # 失败时用 MAC 地址兜底
        try:
            return hashlib.md5(str(uuid.getnode()).encode()).hexdigest()[:16].upper()
        except Exception:
            return "0000000000000000"


def generate_license_key(machine_code: str, days: int = 365) -> str:
    """
    根据机器码生成授权码（开发者工具函数）
    实际使用时由开发者在自己的机器上运行此函数生成授权码
    """
    try:
        raw = f"{machine_code}:{days}:vrc_trans_license"
        hash_obj = hashlib.sha256(raw.encode("utf-8"))
        key = hash_obj.hexdigest()[:16].upper()
        # 格式化为 XXXX-XXXX-XXXX-XXXX
        return f"{key[0:4]}-{key[4:8]}-{key[8:12]}-{key[12:16]}"
    except Exception:
        return ""


def verify_license(key: str, machine_code: str = None) -> dict:
    """
    验证授权码
    返回 {"valid": bool, "message": str, "machine_code": str}
    """
    if machine_code is None:
        machine_code = get_machine_code()

    result = {
        "valid": False,
        "message": "",
        "machine_code": machine_code,
    }

    if not key or not key.strip():
        result["message"] = "未输入授权码"
        return result

    # 清理授权码格式
    key_clean = key.strip().upper().replace("-", "")

    if len(key_clean) != 16:
        result["message"] = "授权码格式错误（应为 16 位）"
        return result

    # 验证授权码（尝试常见的有效期）
    for days in [30, 90, 180, 365, 3650, 99999]:
        expected = generate_license_key(machine_code, days).replace("-", "")
        if key_clean == expected:
            result["valid"] = True
            result["message"] = f"授权验证成功（{days}天）"
            return result

    result["message"] = "授权码无效或与本机机器码不匹配"
    return result


def save_license(key: str) -> bool:
    """保存授权码到配置目录"""
    try:
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        license_file = config_dir / "license.json"
        data = {
            "license_key": key,
            "machine_code": get_machine_code(),
        }
        with open(license_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[License] 保存授权码失败: {e}")
        return False


def load_license() -> dict:
    """加载并验证已保存的授权码"""
    try:
        config_dir = get_config_dir()
        license_file = config_dir / "license.json"
        if not license_file.exists():
            return {"valid": False, "message": "未找到授权文件", "machine_code": get_machine_code()}

        with open(license_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        key = data.get("license_key", "")
        return verify_license(key)
    except Exception as e:
        return {"valid": False, "message": f"授权文件读取失败: {e}", "machine_code": get_machine_code()}


def is_licensed() -> bool:
    """检查是否已授权（便捷函数）"""
    result = load_license()
    return result.get("valid", False)


if __name__ == "__main__":
    # 开发者工具：生成授权码
    print("=== VRChat 翻译悬浮字幕 - 授权码生成工具 ===")
    machine_code = get_machine_code()
    print(f"本机机器码: {machine_code}")
    print()

    print("可选有效期：")
    for days in [30, 90, 180, 365, 3650]:
        key = generate_license_key(machine_code, days)
        print(f"  {days}天: {key}")
    print()
    print("提示：将授权码发给用户，用户在程序中输入后自动验证并保存。")
