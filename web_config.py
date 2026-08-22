"""
Web 配置界面（轻量级 HTTP 服务）
- 通过浏览器访问 http://localhost:PORT 查看和修改配置
- 基于 Python 内置 http.server，无需额外依赖
- 启动方式：在设置中开启 Web 配置，或命令行参数 --web-config
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

_web_server = None
_web_thread = None
_web_port = 8765


class ConfigHandler(BaseHTTPRequestHandler):
    """配置 HTTP 请求处理器"""

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self._serve_html()
        elif parsed.path == "/api/config":
            self._serve_config()
        elif parsed.path == "/api/status":
            self._serve_status()
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/config":
            self._update_config()
        else:
            self.send_error(404)

    def _serve_html(self):
        """返回简单的配置页面 HTML"""
        html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>VRChat 翻译悬浮字幕 - Web 配置</title>
<style>
body { font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }
h1 { color: #333; }
.form-group { margin: 15px 0; }
label { display: block; margin-bottom: 5px; font-weight: bold; }
input, select { width: 100%; padding: 8px; box-sizing: border-box; }
button { padding: 10px 20px; background: #4CAF50; color: white; border: none; cursor: pointer; }
button:hover { background: #45a049; }
.status { padding: 10px; margin: 10px 0; border-radius: 4px; }
.status.ok { background: #d4edda; color: #155724; }
.status.err { background: #f8d7da; color: #721c24; }
</style>
</head>
<body>
<h1>VRChat 翻译悬浮字幕 - Web 配置</h1>
<div id="status"></div>
<div id="config-form">
  <div class="form-group">
    <label>识别引擎</label>
    <select id="whisper_engine">
      <option value="sherpa">Sherpa-onnx</option>
      <option value="faster">faster-whisper</option>
    </select>
  </div>
  <div class="form-group">
    <label>Sherpa 模型 ID</label>
    <input type="text" id="sherpa_model_id" value="streaming-paraformer-bilingual-zh-en">
  </div>
  <div class="form-group">
    <label>翻译目标语言</label>
    <input type="text" id="target_lang" value="日语">
  </div>
  <div class="form-group">
    <label>AI 提供商</label>
    <select id="ai_provider">
      <option value="deepseek">DeepSeek</option>
      <option value="openai">OpenAI</option>
      <option value="doubao">豆包</option>
      <option value="ollama">Ollama（本地）</option>
      <option value="custom">自定义</option>
    </select>
  </div>
  <div class="form-group">
    <label>API Key</label>
    <input type="password" id="ai_api_key">
  </div>
  <div class="form-group">
    <label>OSC 发送</label>
    <select id="enable_osc">
      <option value="true">开启</option>
      <option value="false">关闭</option>
    </select>
  </div>
  <div class="form-group">
    <label>实时降噪</label>
    <select id="enable_noise_reduction">
      <option value="false">关闭</option>
      <option value="true">开启</option>
    </select>
  </div>
  <button onclick="saveConfig()">保存配置</button>
</div>
<script>
function loadConfig() {
  fetch('/api/config')
    .then(r => r.json())
    .then(cfg => {
      document.getElementById('whisper_engine').value = cfg.whisper_engine || 'sherpa';
      document.getElementById('sherpa_model_id').value = cfg.sherpa_model_id || 'streaming-paraformer-bilingual-zh-en';
      document.getElementById('target_lang').value = cfg.target_lang || '日语';
      document.getElementById('ai_provider').value = cfg.ai_provider || 'deepseek';
      document.getElementById('ai_api_key').value = cfg.ai_api_key || '';
      document.getElementById('enable_osc').value = cfg.enable_osc ? 'true' : 'false';
      document.getElementById('enable_noise_reduction').value = cfg.enable_noise_reduction ? 'true' : 'false';
    });
}
function saveConfig() {
  const cfg = {
    whisper_engine: document.getElementById('whisper_engine').value,
    sherpa_model_id: document.getElementById('sherpa_model_id').value,
    target_lang: document.getElementById('target_lang').value,
    ai_provider: document.getElementById('ai_provider').value,
    ai_api_key: document.getElementById('ai_api_key').value,
    enable_osc: document.getElementById('enable_osc').value === 'true',
    enable_noise_reduction: document.getElementById('enable_noise_reduction').value === 'true',
  };
  fetch('/api/config', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(cfg)
  })
  .then(r => r.json())
  .then(res => {
    const status = document.getElementById('status');
    if (res.success) {
      status.innerHTML = '<div class="status ok">配置保存成功！部分设置需要重启程序生效。</div>';
    } else {
      status.innerHTML = '<div class="status err">保存失败：' + res.error + '</div>';
    }
  });
}
loadConfig();
</script>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _serve_config(self):
        """返回当前配置 JSON"""
        try:
            from config import Config
            cfg = Config()
            config_dict = dict(cfg._config) if hasattr(cfg, '_config') else {}
            # 隐藏敏感信息
            if 'ai_api_key' in config_dict and config_dict['ai_api_key']:
                config_dict['ai_api_key'] = config_dict['ai_api_key'][:8] + "..."
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(config_dict, ensure_ascii=False, indent=2).encode("utf-8"))
        except Exception as e:
            self.send_error(500, str(e))

    def _serve_status(self):
        """返回服务状态"""
        status = {"status": "running", "port": _web_port}
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(status).encode("utf-8"))

    def _update_config(self):
        """更新配置"""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            from config import Config
            cfg = Config()
            for key, value in data.items():
                cfg.set(key, value)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
        except Exception as e:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

    def log_message(self, format, *args):
        """静默日志，不打印到控制台"""
        pass


def start_web_config(port=8765):
    """启动 Web 配置服务（后台线程）"""
    global _web_server, _web_thread, _web_port
    if _web_server is not None:
        return False
    _web_port = port
    try:
        _web_server = HTTPServer(("0.0.0.0", port), ConfigHandler)
        _web_thread = threading.Thread(target=_web_server.serve_forever, daemon=True)
        _web_thread.start()
        print(f"[WebConfig] Web 配置服务已启动: http://localhost:{port}")
        return True
    except Exception as e:
        print(f"[WebConfig] 启动失败: {e}")
        _web_server = None
        return False


def stop_web_config():
    """停止 Web 配置服务"""
    global _web_server, _web_thread
    if _web_server is not None:
        _web_server.shutdown()
        _web_server = None
        _web_thread = None
        print("[WebConfig] Web 配置服务已停止")


def is_web_config_running() -> bool:
    """检查 Web 配置服务是否在运行"""
    return _web_server is not None


if __name__ == "__main__":
    # 单独运行时启动 Web 配置服务
    start_web_config()
    print("按 Ctrl+C 退出...")
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        stop_web_config()
