# VRChat 实时翻译悬浮字幕 - 项目说明

## 项目简介
桌面悬浮字幕工具，实时识别语音并通过 DeepSeek AI 翻译，支持双语显示、OSC 发送到 VRChat 聊天框。

## 当前功能
- 无边框半透明悬浮字幕窗口（可拖动、边缘调整大小、双击锁定/解锁、锁定后鼠标穿透）
- 系统托盘右键菜单（显示/隐藏、锁定、设置、字体、颜色、透明度、手动输入、历史记录、AI代聊、退出）
- 4 Tab 设置面板（翻译、OSC、语音识别、外观）
- 实时语音识别（webrtcvad 断句 + faster-whisper）
- DeepSeek API AI 翻译（支持自定义提示词）
- OSC 协议发送到 VRChat 聊天框
- **OSC 双语发送**（多行/括号/斜杠格式，支持打字指示器）
- **历史记录窗口**（可回看、右键重新翻译/复制/重发OSC、可选持久化）
- **单条字幕语言精细修改**（历史窗口中右键/双击重新翻译为任意语言）
- **AI 代聊**（根据意图生成社交话语，预设模板，可编辑后发送，支持免费/自定义API切换）
- **帮助说明书**（程序内帮助窗口，含快速开始、设置详解、快捷键、FAQ）
- **配置导入/导出/恢复默认**（设置面板底部按钮，一键备份迁移）
- **多源自动测速下载**（bootstrap 自动选择最快的 HuggingFace 镜像）
- 10 种语言界面（简中/繁中/英/日/韩/法/德/西/俄/葡），自动跟随系统
- 双向翻译模式（麦克风→OSC，电脑声音→字幕，独立开关和目标语言）
- 单路模式输出可自定义（独立控制显示字幕和发送OSC）
- 首次运行自动下载模型和 FFmpeg（bootstrap 自检）
- **多翻译引擎**：DeepSeek API / Google 翻译（免费）/ 百度翻译
- **OSC 超长自动分段**：超过 144 字符自动按标点切分多条发送
- **文字描边/阴影**：字幕文字可加描边和阴影效果
- **TTS 语音朗读**：自动朗读翻译结果，语速音量可调
- **音频设备下拉选择**：设置面板内直接刷新选择设备
- **自动更新检查**：启动时检测新版本
- **程序日志系统**：运行日志写入 app.log，便于排错
- **Inno Setup 安装包**：专业安装程序，带快捷方式和卸载
- **自定义程序图标**
- 配置持久化到 %APPDATA%/vrc_trans/config.json

## 文件结构
```
vrc_trans/
├── main.py              # 主程序（悬浮窗+托盘+控制器）
├── config.py            # 配置管理（JSON持久化）
├── i18n.py              # 多语言模块（10种语言）
├── settings_dialog.py   # 设置对话框（4个Tab）
├── translator.py        # DeepSeek翻译模块
├── speech_recognizer.py # 实时语音识别（webrtcvad+faster-whisper）
├── osc_sender.py        # OSC协议发送
├── history_window.py    # 历史记录窗口
├── ai_chat.py           # AI代聊窗口
├── help_window.py       # 帮助说明书窗口
├── bootstrap.py         # 首次运行自检+自动下载
├── list_devices.py      # 音频设备查询工具
├── logger.py            # 日志系统
├── tts.py               # TTS语音朗读
├── update_checker.py    # 自动更新检查
├── VRC_Translate.spec   # PyInstaller打包配置
├── install.iss          # Inno Setup安装包脚本
├── app.ico              # 程序图标
├── requirements.txt     # Python依赖列表
├── install.bat          # 一键安装依赖
├── start.bat            # 启动程序
├── build_exe.bat        # PyInstaller打包exe（使用spec）
├── IMPROVEMENT_PLAN.md  # 需求改进方案文档
└── README.md            # 使用说明
```

## 技术栈
- GUI: PyQt5
- 语音识别: faster-whisper (CTranslate2) + webrtcvad
- 翻译: DeepSeek API (openai库)
- OSC: python-osc
- 音频: sounddevice + soundfile
- 打包: PyInstaller (spec文件)

## 已知问题与解决方法
1. **webrtcvad import 失败 (pkg_resources not found)**: setuptools 版本太新，降级: `pip install "setuptools<80"`（已写入 install.bat）
2. **torch c10.dll 加载失败**: faster-whisper 不需要 torch，卸载即可: `pip uninstall torch openai-whisper -y`
3. **中文 bat 在 CMD 乱码**: 必须用英文版 bat 脚本
4. **模块名不能叫 locale.py**: 与 Python 内置模块冲突，已改名为 i18n.py
5. **input overflow 警告**: 模型加载时缓冲区暂时溢出，加载完成后自动消失，不影响使用
6. **VRChat OSC 144字符限制**: 双语发送时可能超长，建议用多行格式或精简原文

## 用户环境
- Windows, Python 3.12
- 音频设备: 立体声混音=2, 麦克风阵列=1
- GPU: NVIDIA 4060 (支持 CUDA 加速)
- 项目路径: C:\Users\m1504\Desktop\vrc_trans

## 待办/可优化方向
- [x] 打包成专业安装包（Inno Setup）
- [x] 自定义程序图标
- [x] 翻译历史记录
- [ ] 全局快捷键
- [x] TTS 朗读翻译结果
- [x] 更多字幕样式（描边、阴影）
- [x] 更多翻译引擎支持（Google/百度）
- [x] OSC 超长文本分段发送
- [x] 程序日志系统
- [x] 音频设备下拉选择
- [x] 自动更新检查

## 配置说明
- 配置文件: %APPDATA%\vrc_trans\config.json
- 历史记录文件: %APPDATA%\vrc_trans\history.jsonl（可选持久化）
- 模型目录: %APPDATA%\vrc_trans\models\（bootstrap 自动下载）
- 默认模型: small (CPU int8)，有 GPU 建议改 cuda + float16
- 默认 DeepSeek 模型: deepseek-v4-flash
- 默认翻译引擎: deepseek（可切换 google/baidu）
- 双向模式默认关闭，需在设置→语音识别中手动开启
- OSC 双语默认关闭，需在设置→OSC中手动开启
- 日志文件: %APPDATA%\vrc_trans\app.log（自动轮转，单文件2MB）
- TTS 默认关闭，需在设置→其他中开启（需 pyttsx3）
- 自动更新检查默认开启，可在设置→其他中关闭
