"""
统一 AI 客户端模块
支持多家 AI 提供商，所有调用走 OpenAI 兼容接口：
  - DeepSeek  (api.deepseek.com)
  - OpenAI    (api.openai.com, 即 ChatGPT)
  - Azure OpenAI (微软 Azure，需 endpoint + deployment)
  - 自定义    (任何 OpenAI 兼容接口，如 SiliconFlow、OneAPI 等)

用法：
    client = AIClient(provider="openai", api_key="sk-xxx", model="gpt-4o-mini")
    reply = client.chat("你是翻译官", "Hello world")
"""
import logger

log = logger.get_logger("ai_client")

# 提供商元信息：默认 base_url、推荐模型列表、显示名
PROVIDER_INFO = {
    "deepseek": {
        "label": "DeepSeek",
        "default_base": "https://api.deepseek.com",
        "default_model": "deepseek-v4-flash",
        "recommended_models": [
            "deepseek-v4-flash",
            "deepseek-chat",
            "deepseek-reasoner",
        ],
        "needs_azure": False,
    },
    "openai": {
        "label": "OpenAI (ChatGPT)",
        "default_base": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "recommended_models": [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "o1-mini",
        ],
        "needs_azure": False,
    },
    "azure": {
        "label": "Azure OpenAI (微软)",
        "default_base": "",
        "default_model": "",
        "recommended_models": [],
        "needs_azure": True,
    },
    "custom": {
        "label": "自定义 (OpenAI 兼容)",
        "default_base": "https://api.siliconflow.cn/v1",
        "default_model": "deepseek-ai/DeepSeek-V2.5",
        "recommended_models": [],
        "needs_azure": False,
    },
    "doubao": {
        "label": "豆包 (火山引擎方舟)",
        "default_base": "https://ark.cn-beijing.volces.com/api/v3",
        "default_model": "doubao-1-5-pro-32k-250115",
        "recommended_models": [
            "doubao-1-5-pro-32k-250115",
            "doubao-1-5-lite-32k-250115",
            "doubao-1-5-pro-256k-250115",
            "doubao-1-5-vision-pro-32k-250115",
        ],
        "needs_azure": False,
    },
    "ollama": {
        "label": "Ollama (本地大模型)",
        "default_base": "http://localhost:11434/v1",
        "default_model": "qwen2.5:7b",
        "recommended_models": [
            "qwen2.5:7b",
            "qwen2.5:14b",
            "llama3.2:3b",
            "llama3.1:8b",
            "mistral:7b",
            "gemma2:9b",
        ],
        "needs_azure": False,
        "no_api_key": True,  # Ollama 不需要 API Key
    },
}


def get_provider_label(provider: str) -> str:
    return PROVIDER_INFO.get(provider, {}).get("label", provider)


def get_providers() -> list:
    """返回 [(provider_key, label), ...]"""
    return [(k, v["label"]) for k, v in PROVIDER_INFO.items()]


class AIClient:
    """统一 AI 调用客户端"""

    def __init__(
        self,
        provider: str = "deepseek",
        api_key: str = "",
        api_base: str = "",
        model: str = "",
        azure_endpoint: str = "",
        azure_deployment: str = "",
        azure_api_version: str = "2024-02-15-preview",
        timeout: int = 30,
    ):
        self.provider = provider if provider in PROVIDER_INFO else "deepseek"
        self.api_key = api_key.strip()
        self.timeout = timeout

        info = PROVIDER_INFO[self.provider]

        # api_base：用户没填就用提供商默认
        self.api_base = (api_base or info["default_base"]).rstrip("/")

        # model：用户没填就用提供商默认
        self.model = model or info["default_model"]

        # Azure 专用
        self.azure_endpoint = azure_endpoint.strip()
        self.azure_deployment = azure_deployment.strip()
        self.azure_api_version = azure_api_version.strip() or "2024-02-15-preview"

        self._client = None

    def _get_client(self):
        """懒加载 OpenAI / AzureOpenAI 客户端"""
        if self._client is not None:
            return self._client

        if not self.api_key:
            return None

        try:
            if self.provider == "azure":
                from openai import AzureOpenAI
                if not self.azure_endpoint:
                    log.error("Azure OpenAI 需要配置 endpoint")
                    return None
                self._client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.azure_api_version,
                    azure_endpoint=self.azure_endpoint.rstrip("/"),
                    timeout=self.timeout,
                )
            else:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base if self.api_base else None,
                    timeout=self.timeout,
                )
            return self._client
        except Exception as e:
            log.error(f"创建 AI 客户端失败 ({self.provider}): {e}")
            return None

    def is_ready(self) -> bool:
        """是否可以调用（有 API Key 等必要配置）"""
        info = PROVIDER_INFO.get(self.provider, {})
        # Ollama 等本地模型不需要 API Key
        if info.get("no_api_key", False):
            return True
        if not self.api_key:
            return False
        if self.provider == "azure":
            return bool(self.azure_endpoint and self.azure_deployment)
        return True

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = None,
    ) -> str:
        """
        发送一次聊天请求，返回 AI 回复文本。
        失败时返回空字符串。
        """
        client = self._get_client()
        if client is None:
            log.warning(f"AI 客户端未就绪 (provider={self.provider})")
            return ""

        # Azure 用 deployment 名作为 model
        model = self.azure_deployment if self.provider == "azure" else self.model
        if not model:
            log.error("未指定模型 / deployment")
            return ""

        try:
            kwargs = dict(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
            )
            if max_tokens:
                kwargs["max_tokens"] = max_tokens

            response = client.chat.completions.create(**kwargs)
            result = response.choices[0].message.content
            if result:
                result = result.strip()
                # 清理常见的多余引号
                result = result.strip('"').strip("'").strip("「」").strip("『』").strip("()")
            return result or ""
        except Exception as e:
            log.error(f"AI 调用失败 ({self.provider}/{model}): {e}")
            return ""

    def chat_stream(
        self,
        system_prompt: str,
        user_message: str,
        on_chunk,
        temperature: float = 0.7,
    ):
        """
        流式调用，每收到一段文本调用 on_chunk(text)。
        失败时不调用 on_chunk。
        """
        client = self._get_client()
        if client is None:
            return

        model = self.azure_deployment if self.provider == "azure" else self.model
        if not model:
            return

        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    on_chunk(chunk.choices[0].delta.content)
        except Exception as e:
            log.error(f"AI 流式调用失败 ({self.provider}): {e}")


def build_client_from_config(config, prefix: str = "") -> AIClient:
    """
    从 Config 对象构建 AIClient。
    prefix 为空时读全局 AI 配置；
    prefix='aichat_' 时读 AI 代聊独立配置（空值自动回退到全局）。
    """
    def _get(key, default=""):
        val = config.get(prefix + key, default) if prefix else config.get(key, default)
        # AI 代聊配置为空时回退到全局
        if prefix and (val == "" or val is None):
            val = config.get(key, default)
        return val

    provider = _get("ai_provider", "deepseek")
    return AIClient(
        provider=provider,
        api_key=_get("ai_api_key", ""),
        api_base=_get("ai_api_base", ""),
        model=_get("ai_model", ""),
        azure_endpoint=_get("ai_azure_endpoint", ""),
        azure_deployment=_get("ai_azure_deployment", ""),
        azure_api_version=_get("ai_azure_api_version", "2024-02-15-preview"),
    )
