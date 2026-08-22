# VRChat 翻译悬浮字幕 - 需求改进方案 v2

> 基于用户长期使用反馈整理，共 5 项核心需求。
> 整理日期：2026-08-18

---

## 需求总览

| # | 需求 | 类型 | 优先级 | 涉及模块 |
|---|------|------|--------|----------|
| 1 | EXE 打包依赖不全，首次运行自动下载缺失资源 | 打包/部署 | P0 | build_exe.bat, 新增 bootstrap.py |
| 2 | 新增历史记录字幕窗口 | 功能新增 | P1 | main.py, 新增 history_window.py |
| 3 | 单条字幕语言精细修改 | 交互改进 | P1 | main.py, history_window.py, translator.py |
| 4 | OSC 发送双语字幕（原文+翻译） | 功能改进 | P1 | osc_sender.py, main.py, config.py, settings_dialog.py |
| 5 | AI 代聊功能 | 功能新增 | P2 | 新增 ai_chat.py, main.py, settings_dialog.py |

---

## 需求 1：EXE 打包依赖不全 + 首次运行自动下载

### 现状问题

当前 `build_exe.bat` 使用 PyInstaller `--onefile --windowed` 打包，但存在以下缺失：

1. **隐藏导入不完整**：
   - `ctranslate2` 的 CUDA 后端库（`cudnn_ops`, `cudnn` 等）未收集
   - `faster_whisper` 的 tokenizer 数据文件（`tokenizer.json`, `vocabulary`）可能丢失
   - `sounddevice` 依赖的 `_sounddevice_data` 端口音频库未 `--collect-binaries`
   - `webrtcvad` 依赖 `pkg_resources`（setuptools），但 `--onefile` 下可能找不到
   - `numpy` 的 `.pyd` 依赖链（`libopenblas`）需要 `--collect-binaries numpy`

2. **运行时依赖未打包**：
   - FFmpeg 二进制（faster-whisper 某些路径需要）
   - VC++ Runtime（用户机器可能没装）
   - whisper 模型文件（首次运行需联网下载，但国内 HuggingFace 不稳定）

3. **打包脚本本身的问题**：
   - 没有 `--add-data` 把 `i18n.py` 等同目录模块显式打入
   - 没有 `--collect-submodules` 覆盖 `openai`, `pythonosc`
   - 没有 spec 文件，每次命令行参数容易遗漏
   - `--windowed` 模式下控制台输出全丢，出错无法排查

### 改进方案

#### 1.1 重写 build_exe.bat → 使用 spec 文件

创建 `VRC_Translate.spec`，集中管理所有打包参数：

```python
# VRC_Translate.spec (核心参数)
a = Analysis(
    ['main.py'],
    hiddenimports=[
        'faster_whisper', 'webrtcvad', 'sounddevice', 'soundfile',
        'pythonosc', 'openai', 'ctranslate2', 'pkg_resources',
        'numpy', 'numpy.core._methods', 'setuptools',
    ],
    collect_all=['faster_whisper', 'ctranslate2', 'sounddevice'],
    collect_binaries=['numpy', 'soundfile'],
    collect_submodules=['openai', 'pythonosc'],
    datas=[
        ('i18n.py', '.'),
        ('config.py', '.'),
        # ... 所有同目录 .py
    ],
    ...
)
```

#### 1.2 新增 bootstrap.py — 首次运行自检+自动下载

程序启动时（在 `main()` 最前面）执行：

```
启动 → 检查依赖完整性 → 检查模型文件 → 检查 FFmpeg → 缺失则自动下载 → 进入主程序
```

- **模型下载**：从国内镜像（如 `hf-mirror.com`）下载 whisper 模型到 `%APPDATA%/vrc_trans/models/`
- **FFmpeg 下载**：内置一个精简版 ffmpeg.exe 或首次运行从 gyan.dev 下载
- **进度显示**：用 PyQt5 的 QProgressDialog 显示下载进度，避免黑窗
- **离线兜底**：如果下载失败，提示用户手动下载并给出路径

#### 1.3 打包产物结构

```
dist/
├── VRC_Translate.exe          # 主程序（onefile）
├── ffmpeg.exe                 # 随包附带（可选，体积+80MB）
├── models/                    # 可选：预打包 small 模型（+500MB）
└── README.txt                 # 首次使用说明
```

#### 涉及文件
- 新增 `VRC_Translate.spec`
- 新增 `bootstrap.py`（依赖自检+下载器）
- 修改 `build_exe.bat`（调用 spec，增加预打包选项）
- 修改 `main.py`（启动时调用 bootstrap）
- 修改 `speech_recognizer.py`（模型路径优先用 `%APPDATA%/vrc_trans/models/`）

---

## 需求 2：历史记录字幕窗口

### 现状问题

当前 `FloatingSubtitle` 只显示**最新一条**字幕，之前的内容直接被覆盖，用户无法回看。

### 改进方案

新增独立的 `HistoryWindow`（历史记录窗口），与主悬浮窗并存：

#### 2.1 窗口特性
- 独立无边框半透明窗口（风格与主悬浮窗一致）
- 可拖动、可调整大小、可锁定、鼠标穿透
- 垂直滚动列表，每条记录显示：时间戳 + 原文 + 翻译
- 默认显示最近 N 条（可配置，默认 20 条）
- 自动滚动到底部（新消息到来时）
- 可通过托盘菜单显示/隐藏

#### 2.2 数据结构
```python
# 每条历史记录
@dataclass
class HistoryEntry:
    id: int
    timestamp: float        # time.time()
    source: str             # "mic" / "computer" / "manual"
    original: str
    translated: str
    original_lang: str      # 检测到的源语言
    target_lang: str        # 翻译目标语言
```

#### 2.3 存储
- 内存中保留最近 500 条（环形缓冲区）
- 可选持久化到 `%APPDATA%/vrc_trans/history.jsonl`（每行一条 JSON）
- 启动时加载最近 100 条

#### 2.4 与主悬浮窗的关系
- 主悬浮窗：只显示最新一条（保持低干扰）
- 历史窗口：显示滚动列表（可回看）
- 两个窗口独立开关、独立位置记忆

#### 涉及文件
- 新增 `history_window.py`
- 修改 `main.py`（Controller 中增加历史记录推送，托盘增加开关）
- 修改 `config.py`（增加历史窗口相关配置）
- 修改 `i18n.py`（增加历史窗口相关翻译）

---

## 需求 3：单条字幕语言精细修改

### 现状问题

当前翻译目标语言是**全局配置**：
- 单路模式：只有一个 `target_lang`
- 双路模式：麦克风和电脑声音各有一个目标语言
- 但同一路内所有字幕都用同一个目标语言，无法针对某一条单独改

### 改进方案

在**历史记录窗口**中支持对单条记录进行语言操作：

#### 3.1 右键菜单（历史窗口中每条记录）
```
右键某条字幕 →
  ├─ 重新翻译为 → 中文 / 日语 / 英语 / 韩语 / ...（12种）
  ├─ 复制原文
  ├─ 复制翻译
  ├─ 重新发送到 OSC
  └─ 删除这条记录
```

#### 3.2 实现方式
- 历史记录中每条保留 `original`（原文），重新翻译时直接用原文 + 新目标语言调用 `translator.translate()`
- 翻译完成后更新该条记录的 `translated` 和 `target_lang`
- 如果该条是麦克风来源，重新翻译后可选择是否重新发送 OSC

#### 3.3 快捷操作
- 双击某条记录：弹出语言选择下拉，快速切换目标语言并重新翻译
- 托盘菜单增加"最近一条重新翻译为..."子菜单

#### 涉及文件
- 修改 `history_window.py`（右键菜单 + 双击交互）
- 修改 `translator.py`（已有 `translate(text, target_lang)` 支持，无需大改）
- 修改 `main.py`（Controller 增加单条重译方法）
- 修改 `i18n.py`（增加菜单项翻译）

---

## 需求 4：OSC 双语字幕

### 现状问题

当前 `osc_sender.send_chatbox()` 只发送**翻译后的文本**（或原文），VRChat 聊天框里只显示一种语言。
如果用户说中文，翻译成日语发出去，国内玩家看不懂日语；反之亦然。

### 改进方案

OSC 支持发送**双语格式**：原文 + 翻译，用分隔符拼接。

#### 4.1 发送格式（可配置）
```
格式1（换行分隔）：
  你好
  こんにちは

格式2（括号分隔）：
  你好 (こんにちは)

格式3（斜杠分隔）：
  你好 / こんにちは

格式4（仅翻译，当前行为）：
  こんにちは
```

#### 4.2 配置项
- `osc_bilingual`: bool（是否启用双语 OSC）
- `osc_bilingual_format`: str（"newline" / "parenthesis" / "slash" / "translate_only"）
- `osc_bilingual_order`: str（"original_first" / "translate_first"）

#### 4.3 注意事项
- VRChat 聊天框有**144 字符限制**，双语可能超长，需要截断并提示
- 换行格式在 VRChat 中是否生效需要验证（OSC chatbox 可能不支持 `\n`，如果不支持则用空格或括号）
- 超长时优先保证翻译完整，原文截断

#### 涉及文件
- 修改 `osc_sender.py`（增加 `send_bilingual()` 方法）
- 修改 `main.py`（Controller 中 OSC 发送逻辑支持双语）
- 修改 `config.py`（增加双语配置项）
- 修改 `settings_dialog.py`（OSC Tab 增加双语设置）
- 修改 `i18n.py`（增加设置项翻译）

---

## 需求 5：AI 代聊功能

### 需求理解

用户说的"AI 代聊"不是普通聊天，而是：
- 在 VRChat 场景中，用户输入一个话题/意图，AI 自动生成一段合适的社交话语
- 自动翻译并发送到 OSC 聊天框
- 类似"帮我跟日本人打个招呼"、"帮我委婉拒绝"、"帮我接话"这种场景

### 改进方案

新增 `AIChat` 模块，作为独立功能面板：

#### 5.1 功能形态
- 托盘菜单 → "AI 代聊" → 弹出小窗口
- 窗口包含：
  - 场景/意图输入框（如"跟旁边的日本人打招呼"）
  - 语气选择（友好 / 正式 / 幽默 / 害羞 / 高冷）
  - 目标语言（自动继承麦克风目标语言，可临时改）
  - "生成并发送"按钮
  - 生成结果预览（可编辑后再发送）

#### 5.2 AI 提示词设计
```
system: 你是 VRChat 社交助手。根据用户的意图，生成一句自然、符合场景的{语言}口语表达。
        要求：简短（不超过30字）、口语化、符合{语气}语气。
        只输出那句话本身，不要解释。
user: {用户意图}
```

#### 5.3 工作流
```
用户输入意图 → AI 生成目标语言句子 → 显示在预览框（可编辑）
  → 用户点"发送" → 同时显示在悬浮窗 + 发送 OSC → 记入历史
```

#### 5.4 快捷模板（预设按钮）
- 打招呼
- 感谢
- 道歉
- 告别
- 夸赞
- 请求加好友
- 邀请一起玩

#### 涉及文件
- 新增 `ai_chat.py`（AI 代聊逻辑 + 窗口）
- 修改 `main.py`（托盘增加入口，Controller 集成）
- 修改 `config.py`（增加代聊配置：默认语气、API 复用）
- 修改 `i18n.py`（增加代聊窗口翻译）
- 复用 `translator.py` 的 OpenAI client（同一个 API Key）

---

## 实现路线图建议

### 第一阶段（P0，先解决打包痛点）
1. 重写 `build_exe.bat` + 创建 `VRC_Translate.spec`
2. 新增 `bootstrap.py` 首次运行自检+下载
3. 测试打包 → 验证在干净 Windows 上能跑

### 第二阶段（P1，核心体验改进）
4. 新增 `history_window.py` 历史记录窗口
5. 历史窗口中实现单条字幕语言修改（右键+双击）
6. OSC 双语发送功能 + 设置面板

### 第三阶段（P2，新功能）
7. AI 代聊模块 + 窗口 + 预设模板

---

## 需要用户确认的问题

1. **打包体积**：是否接受把 FFmpeg 和 small 模型预打包进 EXE？（体积会从 ~100MB 涨到 ~700MB，但首次运行零配置）
2. **历史记录持久化**：是否需要把历史记录保存到文件（重启后还能看到）？还是只保留本次运行的内存记录？
3. **OSC 双语格式**：VRChat chatbox 是否支持换行？如果不支持，默认用括号格式可以吗？
4. **AI 代聊的 API**：复用 DeepSeek 的 API Key 就行，还是需要单独配置？
5. **实现顺序**：是否按上面的 P0→P1→P2 顺序来？还是有更急的项？
