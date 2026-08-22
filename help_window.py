"""
帮助/说明书窗口
包含：快速开始、设置详解、快捷键、常见问题
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTextEdit, QLabel
)
from PyQt5.QtCore import Qt
from i18n import tr


class HelpWindow(QWidget):
    """帮助说明书窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("help_title"))
        self.setMinimumSize(680, 520)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowStaysOnTopHint
        )
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        tabs.addTab(self._quickstart_page(), tr("help_tab_quickstart"))
        tabs.addTab(self._settings_page(), tr("help_tab_settings"))
        tabs.addTab(self._shortcuts_page(), tr("help_tab_shortcuts"))
        tabs.addTab(self._faq_page(), tr("help_tab_faq"))

        layout.addWidget(tabs)

    def _make_text(self, html: str) -> QTextEdit:
        """创建只读富文本框"""
        te = QTextEdit()
        te.setReadOnly(True)
        te.setHtml(html)
        te.setStyleSheet("QTextEdit { background: #fafafa; color: #222; border: none; }")
        return te

    # ===== 快速开始 =====
    def _quickstart_page(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        html = """
        <h2>🚀 快速开始</h2>
        <p>欢迎使用 VRChat 实时翻译悬浮字幕！按以下步骤配置即可上手。</p>

        <h3>第一步：启动程序</h3>
        <p><b>EXE 用户：</b>双击 <code>VRC_Translate.exe</code> 即可，无需安装任何依赖。</p>
        <p><b>源码用户：</b>双击运行 <code>install.bat</code> 安装依赖，然后双击 <code>start.bat</code> 启动。</p>
        <p>首次启动会自动下载语音识别模型（默认流式中英双语模型约200MB），请耐心等待。下载慢会自动切换镜像。</p>

        <h3>第二步：配置翻译 API</h3>
        <p>右键右下角托盘图标 → <b>设置</b> → 「翻译」Tab，选择 AI 提供商并填入 API Key：</p>
        <ul>
        <li><b>DeepSeek</b>（推荐，便宜好用）：<a href="https://platform.deepseek.com">https://platform.deepseek.com</a></li>
        <li><b>OpenAI / ChatGPT</b>：<a href="https://platform.openai.com">https://platform.openai.com</a></li>
        <li><b>豆包（火山引擎方舟）</b>：<a href="https://console.volcengine.com/ark">https://console.volcengine.com/ark</a></li>
        <li><b>Azure OpenAI</b>：<a href="https://portal.azure.com">https://portal.azure.com</a></li>
        <li><b>Google 翻译</b>：免费，无需 API Key，直接在翻译引擎选「Google」即可</li>
        </ul>
        <p>每个提供商的 API Key 独立保存，切换提供商会自动加载对应配置。</p>

        <h3>第三步：配置语音识别</h3>
        <ol>
        <li>切换到「语音识别」Tab</li>
        <li>在「电脑声音」下拉框选择「立体声混音」（录制电脑里的声音，如 VRChat 其他人说话）</li>
        <li>在「麦克风」下拉框选择你的麦克风设备</li>
        <li>在「识别模型」下拉框选择合适的模型：<b>流式模型</b>边说边识别延迟低（推荐），<b>离线模型</b>准确率高但需等说完。默认用 CPU 即可流畅运行。</li>
        <li>点击确定保存</li>
        </ol>

        <h3>第四步：开启 VRChat OSC</h3>
        <p>在 VRChat 中：设置 → OSC → 启用 OSC。默认端口 9000，无需修改。</p>

        <h3>完成！</h3>
        <p>现在说话就会自动识别、翻译并发送到 VRChat 聊天框。电脑里的声音也会自动翻译成字幕显示在屏幕上。</p>

        <h3>常见问题</h3>
        <ul>
        <li><b>模型加载失败：</b>设置 → 其他 → 「重新下载模型」</li>
        <li><b>依赖损坏：</b>设置 → 其他 → 「还原依赖」（仅源码模式）</li>
        <li><b>看不到字幕：</b>双击托盘图标显示/隐藏字幕窗口</li>
        <li><b>翻译不生效：</b>检查 API Key 是否填对，或改用免费的 Google 翻译</li>
        </ul>
        """
        layout.addWidget(self._make_text(html))
        return w

    # ===== 设置详解 =====
    def _settings_page(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        html = """
        <h2>⚙️ 设置详解</h2>

        <h3>翻译 Tab</h3>
        <ul>
        <li><b>界面语言</b>：程序界面显示语言，支持简中/繁中/英/日/韩等10种语言，选「跟随系统」自动检测</li>
        <li><b>API Key</b>：DeepSeek 密钥，不填则只识别不翻译</li>
        <li><b>API 地址</b>：默认 DeepSeek 官方地址，可改为兼容 OpenAI 格式的其他服务</li>
        <li><b>模型</b>：deepseek-v4-flash（快，推荐）/ deepseek-chat（均衡）/ deepseek-reasoner（慢但精准）</li>
        <li><b>目标语言</b>：单路模式下翻译成什么语言</li>
        <li><b>自定义提示词</b>：可指定翻译风格，如「使用关西腔」「正式书面语」等</li>
        <li><b>启用 AI 翻译</b>：关闭后只显示识别原文，不调用 API（省钱）</li>
        </ul>

        <h3>OSC Tab</h3>
        <ul>
        <li><b>启用 OSC</b>：是否发送到 VRChat 聊天框</li>
        <li><b>OSC IP / 端口</b>：VRChat OSC 地址，默认 127.0.0.1:9000</li>
        <li><b>自动发送</b>：识别完成后自动翻译并发送</li>
        <li><b>发送延迟</b>：识别后等多久再发，默认0秒即发</li>
        <li><b>自动激活输入框</b>：定期发送按键保持 VRChat 输入框焦点（实验功能）</li>
        <li><b>双语 OSC</b>：开启后原文+翻译一起发送，国内国外玩家都能看懂
            <ul>
            <li>多行格式：每行一种语言（推荐）</li>
            <li>括号格式：原文 (翻译)</li>
            <li>斜杠格式：原文 / 翻译</li>
            <li>仅翻译：只发翻译结果</li>
            </ul>
        </li>
        <li><b>打字指示器</b>：翻译过程中 VRChat 显示「正在输入」，体验更自然</li>
        </ul>

        <h3>语音识别 Tab</h3>
        <ul>
        <li><b>启用实时语音识别</b>：总开关</li>
        <li><b>双向模式</b>：同时运行麦克风和电脑声音两路识别（CPU占用翻倍，推荐高性能电脑）
            <ul>
            <li>麦克风→翻译→OSC：你说的话翻译成外语发到聊天框</li>
            <li>电脑声音→翻译→悬浮字幕：别人说的话翻译成中文字幕</li>
            <li>两路可独立设置目标语言</li>
            </ul>
        </li>
        <li><b>录音来源</b>：单路模式下选电脑声音或麦克风</li>
        <li><b>设备编号</b>：用 list_devices.py 查到的编号</li>
        <li><b>识别引擎</b>：Sherpa-onnx（推荐，中文准、支持流式低延迟）/ faster-whisper（通用多语言，EXE模式可能不稳定）</li>
            <li><b>识别模型</b>：11种模型可选，流式6种+离线5种，默认流式Paraformer中英双语</li>
        <li><b>模型大小</b>：tiny(快但不准) &lt; base &lt; small(推荐) &lt; medium &lt; large(慢但准)</li>
        <li><b>运行设备</b>：cpu / cuda（有N卡选cuda）</li>
        <li><b>计算精度</b>：int8（CPU推荐，省内存）/ float16（GPU推荐，快）</li>
        <li><b>VAD灵敏度</b>：0最宽松~3最严格，推荐2。太高会漏字，太低会把噪音当说话</li>
        <li><b>静音阈值</b>：停顿多久算一句话结束。调大减少断句，调小降低延迟</li>
        <li><b>最短/最长说话时长</b>：太短忽略（过滤杂音），太长强制切断</li>
        <li><b>过滤语气词</b>：每行一个，识别到这些词自动忽略不翻译</li>
        </ul>

        <h3>外观 Tab</h3>
        <ul>
        <li><b>字体</b>：悬浮窗字体和大小</li>
        <li><b>原文/翻译颜色</b>：分别设置两种文字颜色</li>
        <li><b>背景颜色/透明度</b>：悬浮窗背景，透明度0=完全透明</li>
        <li><b>圆角半径</b>：悬浮窗圆角大小</li>
        <li><b>窗口宽度</b>：悬浮窗宽度，高度自动适应内容</li>
        <li><b>显示原文/翻译</b>：可单独关闭某一行</li>
        <li><b>文字对齐</b>：居中/左对齐/右对齐</li>
        </ul>
        """
        layout.addWidget(self._make_text(html))
        return w

    # ===== 快捷键 =====
    def _shortcuts_page(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        html = """
        <h2>⌨️ 快捷键与操作</h2>

        <h3>鼠标操作</h3>
        <table border="1" cellpadding="6" cellspacing="0">
        <tr><th>操作</th><th>效果</th></tr>
        <tr><td>拖动悬浮窗中间</td><td>移动窗口位置</td></tr>
        <tr><td>拖动悬浮窗左/右边缘</td><td>调整窗口宽度</td></tr>
        <tr><td>双击悬浮窗</td><td>锁定/解锁位置（锁定后鼠标穿透）</td></tr>
        <tr><td>双击托盘图标</td><td>显示/隐藏悬浮窗</td></tr>
        <tr><td>右键托盘图标</td><td>打开功能菜单</td></tr>
        </table>

        <h3>历史记录窗口</h3>
        <table border="1" cellpadding="6" cellspacing="0">
        <tr><th>操作</th><th>效果</th></tr>
        <tr><td>拖动窗口边缘/角落</td><td>调整窗口大小</td></tr>
        <tr><td>双击标题栏区域</td><td>锁定/解锁窗口</td></tr>
        <tr><td>双击某条记录</td><td>快速选择语言重新翻译</td></tr>
        <tr><td>右键某条记录</td><td>菜单：重新翻译/复制/重发OSC/删除</td></tr>
        <tr><td>选中文字后 Ctrl+C</td><td>复制选中的文字</td></tr>
        </table>

        <h3>AI 代聊窗口</h3>
        <table border="1" cellpadding="6" cellspacing="0">
        <tr><th>操作</th><th>效果</th></tr>
        <tr><td>意图输入框按回车</td><td>触发生成</td></tr>
        <tr><td>点击预设模板按钮</td><td>快速填入常用意图</td></tr>
        </table>

        <h3>全局快捷键（规划中）</h3>
        <p>以下快捷键正在开发中，后续版本支持：</p>
        <ul>
        <li><code>Ctrl+Shift+H</code>：显示/隐藏历史记录</li>
        <li><code>Ctrl+Shift+A</code>：打开 AI 代聊</li>
        <li><code>Ctrl+Shift+M</code>：手动输入文字</li>
        <li><code>Ctrl+Shift+L</code>：锁定/解锁悬浮窗</li>
        </ul>
        """
        layout.addWidget(self._make_text(html))
        return w

    # ===== 常见问题 =====
    def _faq_page(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        html = """
        <h2>❓ 常见问题</h2>

        <h3>Q: 语音识别没反应？</h3>
        <p>A: 先运行 <code>list_devices.py</code> 确认设备编号正确。录电脑声音需要声卡支持立体声混音，部分笔记本声卡不支持。</p>

        <h3>Q: 模型下载失败/超时？</h3>
        <p>A: 程序会自动从国内镜像 hf-mirror.com 下载。如果仍失败，可以手动下载模型放到 <code>%APPDATA%/vrc_trans/models/</code> 目录。</p>

        <h3>Q: VRChat 收不到文字？</h3>
        <p>A: 确认 VRChat 已开启 OSC（设置 → OSC → Enable），端口默认 9000。检查防火墙是否阻止了本地连接。</p>

        <h3>Q: 翻译很慢？</h3>
        <p>A: 用 <code>deepseek-v4-flash</code> 模型最快。<code>deepseek-reasoner</code> 可能需要几十秒。也可以关闭「启用 AI 翻译」只用识别。</p>

        <h3>Q: 断句不准，一句话被拆成好几段？</h3>
        <p>A: 调大「静音阈值」（比如700-1000ms），或降低 VAD 灵敏度（改成1）。</p>

        <h3>Q: OSC 双语发送后文字被截断？</h3>
        <p>A: VRChat 聊天框有 144 字符硬限制。双语内容过长时建议用括号格式，或关闭双语只发翻译。</p>

        <h3>Q: 历史记录会占很多空间吗？</h3>
        <p>A: 默认不保存到文件，只在内存保留最近200条。可在历史窗口勾选「保存到文件」持久化，文件在 <code>%APPDATA%/vrc_trans/history.jsonl</code>。</p>

        <h3>Q: AI 代聊太费 API 额度？</h3>
        <p>A: 在 AI 代聊窗口可切换到「免费/自定义 API」模式，使用 SiliconFlow 等兼容 OpenAI 格式的免费服务。翻译功能仍可独立使用 DeepSeek。</p>

        <h3>Q: 打包成 EXE 后缺少依赖？</h3>
        <p>A: 使用项目自带的 <code>VRC_Translate.spec</code> 打包，已配置完整的 hidden-import 和数据收集。首次运行 bootstrap 会自动下载模型和 FFmpeg。</p>

        <h3>Q: webrtcvad 导入失败？</h3>
        <p>A: setuptools 版本太新，降级即可：<code>pip install "setuptools&lt;80"</code>。install.bat 已自动处理。</p>

        <h3>Q: 如何备份/迁移配置？</h3>
        <p>A: 托盘菜单 → 配置管理 → 导出配置，会生成一个 JSON 文件。在新机器上导入即可。也可以直接复制 <code>%APPDATA%/vrc_trans/config.json</code>。</p>
        """
        layout.addWidget(self._make_text(html))
        return w

    def closeEvent(self, event):
        event.ignore()
        self.hide()
