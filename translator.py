"""
翻译模块 - 支持多引擎
- AI 翻译（DeepSeek / OpenAI / Azure / 自定义，通过 AIClient 统一调用）
- Google Translate（免费，无需 API Key，通过公开接口）
- 百度翻译（需要 appid/secret，免费额度）
支持自定义提示词、多语言翻译、双路不同目标语言
"""
import threading
import json
import urllib.request
import urllib.parse
import hashlib
import random
import logger
from ai_client import AIClient

log = logger.get_logger("translator")

# 语言名称 -> 代码 映射（用于 Google/百度翻译）
LANG_CODE_MAP = {
    "中文": "zh", "简体中文": "zh", "繁体中文": "zh-TW",
    "日语": "ja", "日本語": "ja",
    "韩语": "ko", "한국어": "ko",
    "英语": "en", "英文": "en", "English": "en",
    "法语": "fr", "Français": "fr",
    "德语": "de", "Deutsch": "de",
    "俄语": "ru", "Русский": "ru",
    "西班牙语": "es", "Español": "es",
    "阿拉伯语": "ar",
    "蒙古语": "mn",
    "葡萄牙语": "pt", "Português": "pt",
    "意大利语": "it", "Italiano": "it",
    "泰语": "th",
    "越南语": "vi",
}


def _lang_to_code(lang_name: str) -> str:
    """语言名称转代码，找不到则返回 auto"""
    return LANG_CODE_MAP.get(lang_name, "auto")


class Translator:
    def __init__(self, api_key="", api_base="https://api.deepseek.com",
                 model="deepseek-v4-flash", target_lang="中文",
                 custom_prompt="", timeout=15,
                 engine="deepseek",
                 baidu_appid="", baidu_secret="",
                 provider="deepseek",
                 azure_endpoint="", azure_deployment="", azure_api_version="2024-02-15-preview"):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.target_lang = target_lang
        self.custom_prompt = custom_prompt
        self.timeout = timeout
        self.engine = engine  # deepseek(AI) / google / baidu
        self.baidu_appid = baidu_appid
        self.baidu_secret = baidu_secret
        # AI 提供商
        self.provider = provider
        self.azure_endpoint = azure_endpoint
        self.azure_deployment = azure_deployment
        self.azure_api_version = azure_api_version
        self._ai_client = None
        self._ai_error_cooldown = 0  # AI 错误冷却结束时间戳
        self._ai_error_reported = False  # 错误是否已报告（避免刷屏）

    def _get_ai_client(self):
        """获取统一 AI 客户端（懒加载）"""
        if self._ai_client is None:
            self._ai_client = AIClient(
                provider=self.provider,
                api_key=self.api_key,
                api_base=self.api_base,
                model=self.model,
                azure_endpoint=self.azure_endpoint,
                azure_deployment=self.azure_deployment,
                azure_api_version=self.azure_api_version,
                timeout=self.timeout,
            )
        return self._ai_client

    def update_ai_config(self, **kwargs):
        """更新 AI 配置并重置客户端（设置保存后调用）"""
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        self._ai_client = None
        self._ai_error_cooldown = 0  # AI 错误冷却结束时间戳
        self._ai_error_reported = False  # 错误是否已报告（避免刷屏）

    def _build_system_prompt(self, target_lang=None) -> str:
        lang = target_lang if target_lang else self.target_lang
        base = (
            f"你是专业翻译。把用户输入的内容翻译成{lang}。"
            f"只输出翻译结果，不要加解释。"
            f"如果输入已经是{lang}，直接返回原文。"
        )
        if self.custom_prompt:
            base += f"\n额外要求：{self.custom_prompt}"
        return base

    def translate(self, text: str, target_lang=None) -> str:
        """
        翻译文本，失败时返回原文
        target_lang: 可选，临时指定目标语言（不传则用默认）
        """
        if not text or not text.strip():
            return ""
        text = text.strip()
        # 根据引擎选择翻译方式
        if self.engine == "google":
            return self._translate_google(text, target_lang)
        elif self.engine == "baidu":
            return self._translate_baidu(text, target_lang)
        else:
            return self._translate_ai(text, target_lang)

    def _translate_ai(self, text: str, target_lang=None) -> str:
        """AI 翻译（通过 AIClient，支持 DeepSeek/OpenAI/Azure/自定义）"""
        if not self.api_key:
            return text
        # 错误冷却：检测到致命错误后暂时停止 AI 翻译，避免频繁报错刷屏
        import time
        if self._ai_error_cooldown > 0:
            if time.time() < self._ai_error_cooldown:
                return text  # 冷却期内直接返回原文
            else:
                self._ai_error_cooldown = 0
                self._ai_error_reported = False
        client = self._get_ai_client()
        if not client.is_ready():
            return text
        try:
            result = client.chat(
                system_prompt=self._build_system_prompt(target_lang),
                user_message=text,
                temperature=0.3,
            )
            self._ai_error_reported = False  # 成功后重置错误标记
            return result if result else text
        except Exception as e:
            err_str = str(e)
            # 检测致命错误：余额不足、402、401 未授权等
            is_fatal = any(kw in err_str.lower() for kw in [
                "insufficient balance", "402", "401", "unauthorized",
                "invalid api key", "rate limit", "quota"
            ])
            if is_fatal:
                # 致命错误：冷却 5 分钟，只报一次错
                if not self._ai_error_reported:
                    log.error(f"AI 翻译失败（致命错误，将暂停 AI 翻译 5 分钟）({self.provider}): {e}")
                    self._ai_error_reported = True
                self._ai_error_cooldown = time.time() + 300  # 5 分钟冷却
            else:
                # 普通错误：只报一次错，冷却 30 秒
                if not self._ai_error_reported:
                    log.error(f"AI 翻译失败 ({self.provider}): {e}")
                    self._ai_error_reported = True
                self._ai_error_cooldown = time.time() + 30  # 30 秒冷却
            return text

    def _translate_google(self, text: str, target_lang=None) -> str:
        """
        Google 免费翻译（通过公开 translate.googleapis.com 接口）
        无需 API Key，但可能有频率限制
        """
        lang = target_lang if target_lang else self.target_lang
        target_code = _lang_to_code(lang)
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "auto",
                "tl": target_code,
                "dt": "t",
                "q": text,
            }
            full_url = url + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(full_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # data[0] 是翻译结果数组，每个元素 [翻译文本, 原文, ...]
            if data and data[0]:
                translated = "".join(seg[0] for seg in data[0] if seg[0])
                return translated.strip()
            return text
        except Exception as e:
            log.error(f"Google 翻译失败: {e}")
            return text

    def _translate_baidu(self, text: str, target_lang=None) -> str:
        """
        百度翻译 API
        需要 baidu_appid 和 baidu_secret
        免费额度：每月 5 万字符
        """
        if not self.baidu_appid or not self.baidu_secret:
            log.warning("百度翻译未配置 appid/secret，降级返回原文")
            return text
        lang = target_lang if target_lang else self.target_lang
        target_code = _lang_to_code(lang)
        # 百度翻译中文用 zh，英文用 en 等
        baidu_code = target_code.lower().replace("-", "")
        if baidu_code == "zhtw":
            baidu_code = "cht"
        try:
            salt = str(random.randint(32768, 65536))
            sign_str = self.baidu_appid + text + salt + self.baidu_secret
            sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest()
            url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
            params = {
                "q": text,
                "from": "auto",
                "to": baidu_code,
                "appid": self.baidu_appid,
                "salt": salt,
                "sign": sign,
            }
            data = urllib.parse.urlencode(params).encode("utf-8")
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            if "trans_result" in result:
                translated = "\n".join(item["dst"] for item in result["trans_result"])
                return translated.strip()
            else:
                log.error(f"百度翻译返回错误: {result}")
                return text
        except Exception as e:
            log.error(f"百度翻译失败: {e}")
            return text

    def translate_async(self, text: str, callback, target_lang=None):
        """
        异步翻译（在子线程中执行，完成后调用 callback(result)）
        target_lang: 可选，临时指定目标语言
        """
        def _worker():
            result = self.translate(text, target_lang)
            callback(result)
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t
