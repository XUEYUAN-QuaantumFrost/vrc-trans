# VRChat 实时翻译悬浮字幕 - 项目开发总结

> 整理日期：2026-08-20
> 项目状态：EXE 可正常运行，核心功能可用，待优化体验

---

## 一、项目概述

**项目名称**：VRChat 实时翻译悬浮字幕（暂名 VRC_Translate）
**项目定位**：为 VRChat 用户提供实时语音识别 + AI 翻译 + OSC 发送 + 悬浮字幕显示的桌面工具
**开发周期**：3 天（2026-08-18 ~ 2026-08-20）
**开发方式**：AI 辅助开发（豆包）+ 用户测试调试

### 核心功能清单

| 功能模块 | 状态 | 说明 |
|---------|------|------|
| 实时语音识别 | ✅ 可用 | 支持麦克风/电脑声音（立体声混音），默认 sherpa-onnx 引擎 |
| AI 翻译 | ✅ 可用 | 支持 DeepSeek / OpenAI / Azure / 豆包(火山方舟) / 自定义，API Key 按提供商分开存储 |
| OSC 发送 | ✅ 可用 | 翻译结果发送到 VRChat 聊天框，支持双语、打字指示器 |
| TTS 语音朗读 | ✅ 可用 | 支持 pyttsx3 本地 + edge-tts 在线，可选择输出设备（含虚拟音频线） |
| AI 代聊 | ✅ 可用 | 自动回复、人设设定、双语输出、透明聊天窗口 |
| 翻译历史记录 | ✅ 可用 | 悬浮窗口显示，最多 200 条，可锁定位置 |
| 悬浮字幕 | ✅ 可用 | 桌面顶部显示，可拖动、可锁定 |
| 设置界面 | ✅ 可用 | 多 Tab 配置，含还原工具、已下载模型列表 |
| 新手引导 | ✅ 可用 | 首次运行 5 步引导 |
| 深色主题 | ✅ 可用 | 默认黑色，字幕/历史窗口强制透明 |
| 关于窗口 | ✅ 可用 | 版本、依赖库版本、当前模型信息 |
| 一键修复 | ✅ 可用 | 删除模型+清配置，弹确认框 |
| 重装依赖 | ✅ 可用 | 重新下载所有依赖 |
| 卸载程序 | ✅ 可用 | uninstall.bat |
| 快捷键自定义 | ✅ 可用 | 默认 Ctrl+Alt+S/H/A |
| 过滤语气词 | ✅ 可用 | 开关控制，默认关闭 |
| 实时降噪 | ✅ 可用 | noisereduce 降噪，VRC 风格界面（强度滑块+麦克风阈值+实时音量指示器），离线模式有效 |
| AI 提供商扩展 | ✅ 可用 | 新增 Ollama（本地大模型）支持，共 6 家提供商 |
| TTS 火山引擎 | ✅ 可用 | 新增豆包/火山引擎 TTS，可调语速/音量/音调，12 种音色 |
| Web 配置界面 | ✅ 可用 | 浏览器访问 http://localhost:8765 查看和修改配置 |
| 授权系统 | ✅ 可用 | 基于机器码的本地授权验证，开发者工具生成授权码 |
| SteamVR 覆盖接口 | ⚠️ 预留 | 接口框架已完成，实际渲染需安装 openvr 并实现纹理渲染 |
| 自动检测默认麦克风 | ✅ 可用 | 启动时自动选中系统默认输入设备 |
| 托盘菜单 | ✅ 可用 | 显示/隐藏字幕、设置、退出 |

---

## 二、技术栈

| 层级 | 技术 |
|------|------|
| 语言 | Python 3.12 |
| GUI | PyQt5 |
| 语音识别 | sherpa-onnx（默认）/ faster-whisper（可选，EXE 模式不可用） |
| 翻译 | OpenAI 兼容接口（统一 ai_client.py） |
| OSC | python-osc |
| 音频采集 | sounddevice |
| VAD | webrtcvad |
| TTS | pyttsx3 + edge-tts + 火山引擎(豆包) |
| 降噪 | noisereduce |
| Web配置 | Python 内置 http.server |
| 授权 | 基于机器码的本地验证 |
| SteamVR | openvr (预留接口) |
| 打包 | PyInstaller（onefile 模式） |
| 主题 | 自定义 QSS 深色主题 |

---

## 三、关键技术决策与踩坑记录

### 3.1 EXE 打包崩溃问题（最大卡点）

**问题**：PyInstaller 打包后运行，在初始化 WhisperModel 时 `Windows fatal exception: access violation`，源码模式正常。

**排查过程**（依次尝试均无效）：
1. 加 onnxruntime/tokenizers/huggingface_hub 的 collect_all 收集 DLL
2. onefile 改 onedir 模式
3. cpu_threads 从 4 降到 2 再降到 1
4. 加 CUDA_VISIBLE_DEVICES=-1、ONNXRUNTIME_CPU_ONLY=1 等环境变量
5. 降级 ctranslate2 到 3.x → 失败，faster-whisper 0.10+ 强制依赖 >=4.0

**根因**：faster-whisper 依赖 ctranslate2，ctranslate2 的 DLL 在 PyInstaller 打包后与 NumPy 2.x / OpenMP 存在兼容性问题，必崩。

**最终解决方案**：彻底放弃 faster-whisper，改用 **sherpa-onnx** 作为默认识别引擎。sherpa-onnx 基于 onnxruntime，不依赖 ctranslate2，打包后正常运行。

### 3.2 模型下载问题

**问题 1**：hf-mirror.com 下载 sherpa-onnx 模型返回 404
**解决**：改用 GitHub release 压缩包下载（sherpa-onnx-paraformer-zh-2023-09-14.tar.bz2）

**问题 2**：GitHub 直连下载太慢/不动
**解决**：加国内镜像线路（ghproxy.net / mirror.ghproxy.com），A 失败自动切 B，加下载进度条

**问题 3**：解压后找不到 model.onnx
**原因**：tar 包里文件在子目录里（sherpa-onnx-paraformer-zh-2023-09-14/model.int8.onnx），且文件名是 model.int8.onnx 不是 model.onnx
**解决**：解压到临时目录后递归查找 .onnx 文件和 tokens.txt，复制到模型目录并重命名

### 3.3 其他已修复的 Bug

| Bug | 原因 | 修复 |
|-----|------|------|
| 子线程操作 UI 导致 access violation | 识别线程直接调用 history_window 控件 | 改为信号槽切主线程 |
| 音频 input overflow 刷屏 | sounddevice 队列太小 | latency='high'，队列 maxsize=100，overflow 不刷屏 |
| 历史窗口拖不动 | eventFilter 里写错常量名（event.MouseButtonPress） | 改为 QEvent.MouseButtonPress，补 import |
| 打包时 tensorboardX 导致卡顿 | PyInstaller 分析 tensorboardX→torch 依赖 | spec excludes 加 tensorboardX/tensorboard |
| spec 报 ct2_hidden 未定义 | 移除 ctranslate2 收集后 hiddenimports 还引用 | 去掉 ct2_hidden，移除 faster_whisper/ctranslate2 隐藏导入 |
| 模型显示为编码而非名称 | 下拉框用索引映射错误 | 改用 addItem 带 userData |
| 启动时更新检查失败 | 无服务器可查 | 移除启动时更新检查 |
| 字幕颜色变黑 | 深色主题 QSS 覆盖了字幕颜色 | 字幕/历史窗口强制透明背景，不被主题覆盖 |
| build_exe.bat 中文编码报错 | 中文注释在 cmd 里乱码 | 重写为纯英文版本 |

---

## 四、项目文件结构

```
vrc_trans/
├── main.py                  # 主程序（托盘/控制器/信号槽/主题/快捷键）
├── config.py                # 配置管理（默认值+旧配置迁移）
├── speech_recognizer.py     # 语音识别（sherpa-onnx/faster-whisper 双引擎）
├── sherpa_recognizer.py     # Sherpa-onnx 封装（Paraformer 离线模型）
├── translator.py            # 翻译调度
├── ai_client.py             # 统一 AI 客户端（5家提供商）
├── ai_chat.py               # AI 代聊
├── tts.py                   # TTS 语音朗读（pyttsx3+edge-tts+扬声器选择）
├── osc_sender.py            # OSC 发送
├── history_window.py        # 翻译历史窗口
├── settings_dialog.py       # 设置对话框
├── about_window.py          # 关于窗口
├── help_window.py           # 帮助窗口
├── tutorial_window.py       # 新手引导
├── theme.py                 # 深色主题 QSS
├── win_dark_titlebar.py     # Windows 深色标题栏
├── bootstrap.py             # 依赖检查+模型下载（多镜像+校验+增量）
├── logger.py                # 日志系统
├── i18n.py                  # 国际化
├── list_devices.py          # 列出音频设备
├── update_checker.py        # 更新检查（当前未启用）
├── VRC_Translate.spec       # PyInstaller 配置（onefile，console=True 调试版）
├── build_exe.bat            # 打包脚本（纯英文）
├── install.bat              # 依赖安装
├── start.bat                # 源码启动
├── uninstall.bat            # 卸载脚本
├── install.iss              # Inno Setup 安装包脚本
├── requirements.txt         # 依赖列表
├── README.md                # 说明文档（口语化风格）
├── app.ico                  # 程序图标
├── app_icon_256.png         # 图标 PNG
├── download_model.py        # ⚠️ 冗余旧文件，未被引用，可删
├── IMPROVEMENT_PLAN.md      # 改进计划（开发版保留）
└── PROJECT.md               # 项目文档（开发版保留）
```

---

## 五、配置说明

### 配置文件位置
- Windows：`%APPDATA%\vrc_trans\config.json`
- 模型下载位置：`%APPDATA%\vrc_trans\models\`

### 当前默认值

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| whisper_engine | sherpa | 识别引擎（sherpa/faster） |
| mic_target_lang | 英语 | 麦克风翻译目标语言 |
| auto_send_delay | 0 | OSC 发送延迟 |
| auto_activate_interval | 1 | OSC 激活间隔 |
| history_font_size | 18 | 历史记录字体大小 |
| filter_filler_words | False | 过滤语气词（默认不过滤） |
| theme | dark | 主题 |
| history_max_entries | 200 | 历史记录最大条数 |
| tutorial_seen | False | 新手引导是否已看 |

### AI 提供商
- DeepSeek：https://api.deepseek.com，默认模型 deepseek-v4-flash
- OpenAI：https://api.openai.com/v1
- Azure：自定义端点
- 豆包(火山方舟)：https://ark.cn-beijing.volces.com/api/v3，默认模型 doubao-1-5-pro-32k-250115
- 自定义：任意 OpenAI 兼容接口

---

## 六、待办事项（按优先级）

### 高优先级（影响核心体验）
- [x] **降噪功能**：集成 noisereduce 实时降噪，开关控制（离线模式有效）
- [x] **流式识别**：改用 sherpa-onnx OnlineRecognizer 流式识别，降低延迟
- [x] **自动检测默认麦克风**：启动时自动选中系统默认输入设备
- [x] **spec console 改回 False**：正式发布版已去掉控制台窗口

### 中优先级（功能完善）
- [ ] **联系开发者信息**：about_window.py 结构已完善，待用户填入真实联系方式
- [ ] **程序正式名称**：内部名称 VRC_Translate，正式名称待用户确定
- [x] **清理冗余文件**：已删除 download_model.py
- [x] **sherpa 模型下载完善**：已集成到 bootstrap.py，11 条镜像自动切换
- [ ] **AI 记忆功能**：代聊时记住对话历史和用户人格（标记为以后做，本次不做）
- [x] **免费 AI 接口/本地 Ollama 支持**：已添加 Ollama 提供商，无需 API Key
- [x] **TTS 火山引擎（豆包）支持**：已添加，可调语速/音量/音调
- [x] **Web 配置界面**：已实现，浏览器访问 http://localhost:8765
- [⏸️] **注册码/授权系统**：代码已写好（license_system_unused.py），需服务器校验，暂未启用，等以后有服务器再集成

### 低优先级（锦上添花）
- [x] **SteamVR 覆盖显示**：接口框架已预留，实际渲染需安装 openvr
- [x] **Web 配置界面**：已实现，基于 Python 内置 http.server
- [ ] **Linux / Android / Mac 版本**（远期规划）
- [x] **注册码/授权系统**：已实现基础版
- [ ] **官网搭建**：用户提到以后要建网站推广

---

## 七、已知限制

1. **faster-whisper 引擎在 EXE 模式下不可用**：会 access violation 崩溃，仅源码模式可用。设置里保留了选项但 EXE 用户请勿选择。
2. **sherpa-onnx 为离线识别**：需要等一句话说完才开始识别，延迟约 1-2 秒。流式识别可优化。
3. **无内置降噪**：直接录制麦克风原始音频，依赖系统/声卡层面的降噪（如奥创）。
4. **NumPy 2.x 兼容性**：当前环境 NumPy 2.x 与部分库有警告，不影响运行但可能有隐患。
5. **打包体积**：onefile EXE 约 100-150MB（含 PyQt5 + onnxruntime + sherpa-onnx）。

---

## 八、打包与发布流程

### 打包步骤
1. 确保安装所有依赖：`pip install -r requirements.txt`
2. 安装 sherpa-onnx：`pip install sherpa-onnx`
3. 运行 `build_exe.bat`
4. 输出位置：`dist\VRC_Translate.exe`（单个文件）
5. 首次运行会自动下载 sherpa-onnx 模型（约 200MB）

### 发布给用户
- 发送 `VRC_Translate.exe` + `app.ico` + `README.md`
- 用户首次运行自动下载模型和依赖
- 配置和模型存在 `%APPDATA%\vrc_trans\`

### 干净打包文件夹
- 使用 `vrc_trans_release/` 文件夹（不含开发文档、模型、缓存）
- 不要用开发版 `vrc_trans/` 直接打包（含 IMPROVEMENT_PLAN.md 等内部文件）

---

## 九、参考项目

- **VRCLS (VRChat LinguaSync)**：https://github.com/VoiceLinkVR/VRCLS
  - Python 版已停止维护，新版用 C# 重写
  - 架构复盘很有参考价值：单进程+多线程+queue 是正确方向
  - 用 sherpa-onnx 流式识别，延迟低
  - 支持麦克风/桌面音频双路、TTS、OSC、SteamVR 覆盖

---

## 十、开发环境信息

- 开发机：Ubuntu Linux（无法交叉编译 Windows EXE，需用户在 Windows 上打包）
- 用户测试机：Windows，Python 3.12，VRChat 后台运行
- 朋友测试机：Intel 12代 + RTX 3050 笔记本，在台湾

---

*本文档随项目持续更新。每次重大改动后请同步更新此文件。*

---

## 十一、更新日志

### 2026-08-20 模型系统大升级（v2）

**核心改动**：从单一离线模型升级为多模型架构，支持流式识别。

**新增功能**：
1. **流式识别（OnlineRecognizer）** — 边说边出结果，延迟从 1-2 秒降到几百毫秒。内置 endpoint 检测，无需 webrtcvad 断句。
2. **多模型支持** — 内置 11 种模型可选：
   - 流式模型 6 种：Paraformer 中英双语（推荐默认）、Paraformer 中粤英三语、Zipformer 中英双语、Zipformer 轻量中英、Zipformer 中文 int8（2025新版）、Zipformer 超轻量中文（14M）
   - 离线模型 5 种：Paraformer 中文 2024新版、Paraformer 轻量中文、Paraformer 中文旧版（兼容）、Paraformer 英文、SenseVoice 五语言（中英日韩粤）
3. **统一模型下载框架** — 模型下载逻辑从 speech_recognizer.py 移到 bootstrap.py，支持多镜像自动切换（ghproxy.net / mirror.ghproxy.com / gh-proxy.com / GitHub直连）。
4. **设置界面模型选择** — 语音识别 Tab 新增 Sherpa 模型下拉框，根据选择的引擎自动切换显示。
5. **流式部分结果实时显示** — 流式识别时字幕实时更新（显示原文 + "..."），一句话结束后触发正常翻译流程。

**修改的文件**：
- `sherpa_recognizer.py` — 完全重写，新增 MODEL_REGISTRY、StreamingSherpaRecognizer、OfflineSherpaRecognizer、工厂函数
- `speech_recognizer.py` — 重写，新增流式处理循环 `_streaming_process_loop()`，支持 `on_partial_result` 回调
- `bootstrap.py` — 新增 `check_sherpa_model_exists()`、`download_sherpa_model()`、`get_sherpa_model_dir()`
- `config.py` — 新增 `sherpa_model_id` 配置项，默认 `streaming-paraformer-bilingual-zh-en`
- `settings_dialog.py` — 新增 `sherpa_model_combo` 下拉框，引擎切换显示逻辑
- `main.py` — 新增 `speech_partial_signal` 信号和 `_on_speech_partial()` 处理方法，三处 SpeechRecognizer 创建增加 `sherpa_model_id` 和 `on_partial_result`

**默认模型变更**：从 `paraformer-zh-2023-09-14`（离线）改为 `streaming-paraformer-bilingual-zh-en`（流式中英双语）。

**向后兼容**：旧配置自动迁移，旧的 `SherpaOnnxRecognizer` 类保留为兼容包装器。

### 2026-08-20 下载源机制大优化 + UI细节修复（v3）

**下载源优化**：
1. 镜像从6条扩充到11条（新增 github.moeyy.xyz、gh.ddzds.cc、gh.con.sh、hub.gitmirror.com、kkgithub.com）
2. 连接超时15秒自动切换下一条镜像
3. 下载速度低于30KB/s持续8秒自动切换
4. 支持断点续传（HTTP Range）
5. 所有镜像失败后打印手动下载链接和操作步骤
6. config.json 新增 custom_download_mirrors 配置项，支持用户自定义镜像源

**UI细节修复（5项）**：
1. 字幕长句子行间距过大：StrokeLabel 从垂直居中改为顶部对齐，减小 layout 边距
2. faster-whisper 模型大小选项不显示：改用 QStackedWidget 切换模型选择器，更可靠
3. 历史窗口横线残留：修复 _append_item 重复添加问题，refresh_appearance 自动清理空 item
4. 锁定时鼠标穿透：字幕窗口补充 update() 确保生效；历史窗口启用 WA_TransparentForMouseEvents，新增 Ctrl+Alt+L 快捷键切换锁定
5. 全部21个下拉框添加 toolTip 鼠标悬停提示

**faster-whisper 崩溃防护**：
- speech_recognizer.py 中 faster-whisper 初始化失败时自动回退到 sherpa-onnx
- 不再因为选了 faster-whisper 就导致整个程序崩溃

**修改的文件**：
- bootstrap.py — download_sherpa_model 完全重写（超时/速度检测/断点续传/手动下载指引）
- config.py — 新增 custom_download_mirrors 配置项
- help_window.py — 修复文字颜色（全局深色主题导致浅灰字在白底看不清）+ 更新过时内容
- main.py — 字幕行间距修复 + 锁定 update() + 历史窗口锁定快捷键
- history_window.py — 横线残留修复 + 锁定鼠标穿透
- settings_dialog.py — QStackedWidget 模型切换 + 21个下拉框 toolTip
- speech_recognizer.py — faster-whisper 崩溃自动回退到 sherpa-onnx
