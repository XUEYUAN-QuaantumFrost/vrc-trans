# VRC Trans — VRChat 实时翻译悬浮字幕

> 一个挂在桌面上的实时翻译字幕工具，就像音乐播放器的歌词那样飘在屏幕上。
> 玩 VRChat 跟外国人聊天必备，支持麦克风/电脑声音识别、AI 翻译、OSC 自动发送、同声传译、TTS 语音朗读。

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Version](https://img.shields.io/badge/Version-2.4.0-orange)

---

## ✨ 功能特性

### 核心功能
- **悬浮字幕**：半透明字幕窗口飘在屏幕上，可拖动、改大小、改颜色、改字体、改透明度
- **双语识别**：支持麦克风和电脑声音同时识别（双向模式），也可以只选一路
- **流式识别**：基于 sherpa-onnx，边说边出结果，延迟几百毫秒
- **多引擎翻译**：DeepSeek / Google / 百度 / 任何 OpenAI 兼容接口
- **OSC 自动发送**：翻译结果自动发到 VRChat 聊天框，支持双语格式
- **历史记录**：所有翻译记录可回看、搜索、重新翻译
- **AI 代聊**：输入你想表达的意思，AI 帮你生成自然的外语发出去

### 进阶功能
- **同声传译**：别人说话 → 翻译 → TTS 念到你耳机里；你说话 → 翻译 → TTS 输出到虚拟音频线 → VRChat 里用翻译后的语音说话
- **TTS 语音朗读**：支持 pyttsx3（本地）/ Edge TTS（云端，多音色）/ 火山引擎（中文优质音色）
- **主界面控制面板**：所有常用设置直接在主界面调整，不用翻设置窗口
- **系统托盘**：最小化到托盘，右键快速操作
- **多语言界面**：简中 / 繁中 / 英 / 日 / 韩 / 法 / 德 / 西 / 俄 / 葡 等十几种语言
- **VB-CABLE 一键安装**：内置虚拟音频线下载安装引导

---

## 🚀 快速开始

### 方式一：下载 EXE（推荐普通用户）
去 [Releases](https://github.com/XUEYUAN-QuaantumFrost/vrc-trans/releases) 页面下载最新版 `VRC_Translate.zip`，解压后双击 `VRC_Translate.exe` 即可。

第一次运行会自动下载语音识别模型（约 1GB），耐心等它下完。

### 方式二：源码运行（开发者）
```bash
# 克隆仓库
git clone https://github.com/XUEYUAN-QuaantumFrost/vrc-trans.git
cd vrc-trans

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

---

## ⚙️ 配置说明

### 翻译引擎
- **Google**：免费，不用 API Key，但国内网络可能需要代理
- **DeepSeek**：推荐，便宜又快，去 [platform.deepseek.com](https://platform.deepseek.com) 申请 API Key
- **百度**：需要百度翻译 API 的 AppID 和密钥
- **自定义**：任何 OpenAI 兼容的接口都可以填

### 语音识别
- **sherpa-onnx**（默认）：中文准，流式低延迟，CPU 就能跑
- **faster-whisper**：通用多语言，源码模式可用，EXE 打包模式可能不稳定

### OSC 设置
- VRChat 里开启 OSC（设置 → OSC → Enable）
- 默认 IP `127.0.0.1`，端口 `9000`，一般不用改

### 同声传译出站
- 需要安装 VB-CABLE 虚拟音频线（程序内可一键安装）
- VRChat 里麦克风选择「CABLE Output」
- 你说话 → 识别 → 翻译 → TTS → 虚拟音频线 → VRChat 里别人听到翻译后的语音

---

## 🎮 使用技巧

| 操作 | 效果 |
|------|------|
| 双击悬浮窗 | 锁定/解锁位置（锁定后鼠标穿透） |
| 双击托盘图标 | 显示/隐藏字幕 |
| 托盘右键 | 快速改颜色、字体、透明度、开关功能 |
| 主界面开始按钮 | 开始/停止翻译 |
| `Ctrl+Alt+L` | 锁定/解锁字幕位置 |

---

## 📁 项目结构

```
vrc-trans/
├── main.py                 # 程序入口，托盘图标，主循环
├── main_window.py          # 主界面控制面板（融合版）
├── floating_subtitle.py    # 悬浮字幕窗口
├── speech_recognizer.py    # 语音识别（sherpa-onnx / faster-whisper）
├── translator.py           # AI 翻译（多引擎）
├── tts.py                  # 语音朗读
├── osc_sender.py           # OSC 发送到 VRChat
├── history_window.py       # 历史记录窗口
├── settings_dialog.py      # 设置对话框
├── ai_chat.py              # AI 代聊窗口
├── bootstrap.py            # 首次运行初始化、模型下载、VB-CABLE 安装
├── config.py               # 配置管理
├── theme.py                # 主题/样式
├── i18n.py                 # 多语言
├── requirements.txt        # Python 依赖
├── VRC_Translate.spec      # PyInstaller 打包配置
├── build_exe.bat           # 打包脚本
├── CHANGELOG.md            # 更新日志
├── DEVELOPMENT_JOURNAL.md  # 开发心路历程
└── version.json            # 版本号
```

---

## 🛠️ 打包成 EXE

```bash
pip install pyinstaller
build_exe.bat
```
打包完成后 EXE 在 `dist\VRC_Translate\` 文件夹里。

---

## ❓ 常见问题

**Q：识别没反应？**
A：检查录音来源和设备编号对不对。录电脑声音需要声卡支持立体声混音，或者用 VB-CABLE 虚拟线。

**Q：VRChat 收不到字？**
A：VRChat 设置里开启 OSC，确认端口是 9000。

**Q：翻译慢/报错？**
A：检查 API Key 对不对，网络能不能访问翻译引擎。Google 翻译国内可能需要代理。

**Q：模型下载很慢/失败？**
A：程序内置了多个下载镜像自动切换。如果都失败，可以手动从 Release 页面下载模型包，放到 `%APPDATA%\vrc_trans\models\` 目录。

**Q：faster-whisper 选了之后崩溃？**
A：EXE 模式下 faster-whisper 有兼容性问题，建议用默认的 sherpa-onnx。源码模式可以用 faster-whisper。

---

## 📝 开发日志

这个项目从 2026 年 8 月 16 日开始开发，完整的开发心路历程记录在 [DEVELOPMENT_JOURNAL.md](DEVELOPMENT_JOURNAL.md) 里，包括踩过的坑、做过的架构决策、每天的进展。

更新日志见 [CHANGELOG.md](CHANGELOG.md)。

---

## 🤝 贡献

欢迎提 Issue 和 Pull Request！
- 发现 bug 请提 Issue，附上 `%APPDATA%\vrc_trans\app.log` 的最后几行
- 想加功能可以先提 Issue 讨论
- 代码风格跟现有文件保持一致就行

---

## 📄 许可证

[MIT License](LICENSE) — 随便用，随便改，保留版权声明就行。

---

## 🙏 致谢

- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) — 流式语音识别
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — 备用识别引擎
- [DeepSeek](https://www.deepseek.com) — 翻译 API
- [VB-Audio](https://vb-audio.com/Cable/) — 虚拟音频线
- 所有给这个项目提过建议、测过 bug 的朋友们
