# VRC Trans — VRChat 实时翻译悬浮字幕

> 像歌词一样飘在屏幕上的实时翻译字幕，玩 VRChat 跟外国人聊天再也不用盯着手机翻译了。
> 麦克风/电脑声音双路识别、AI 翻译、OSC 自动发聊天框、同声传译、TTS 语音朗读，全给你配齐了。

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Version](https://img.shields.io/badge/Version-0.2.4.6-orange)

---

## 🤔 为什么选这个而不是别的翻译工具？

| 特性 | VRC Trans | 常见网页翻译 | VRCLT 类工具 |
|------|-----------|-------------|-------------|
| 悬浮字幕不挡画面 | ✅ 半透明可拖动 | ❌ 要开浏览器 | 部分支持 |
| OSC 自动发 VRChat 聊天框 | ✅ 一键发送双语 | ❌ 要手动复制 | 部分支持 |
| 同声传译（你说外语别人听） | ✅ TTS+虚拟音频线 | ❌ 没有 | 大多没有 |
| 模型下载断点续传 | ✅ 断了接着下 | — | 经常失败重头来 |
| 主界面所有设置一键调 | ✅ 不用翻设置页 | — | 要进多层菜单 |
| 完全免费开源 | ✅ MIT 随便改 | 免费但闭源 | 部分付费 |

**一句话：你只需要点一下"开始"，剩下的翻译、发字、念给对方听，它全包了。**

---

## ✨ 功能特性

### 核心体验
- **悬浮字幕**：半透明飘在屏幕最上层，可拖动、改大小、改颜色、改字体、调透明度，锁定后鼠标穿透不挡操作
- **双路音频识别**：麦克风说的 + 电脑里播的外语，同时识别同时翻，双向沟通不耽误
- **流式出字**：基于 sherpa-onnx 边说边出结果，延迟几百毫秒，不用等人家说完
- **OSC 自动发字**：翻译完直接打到 VRChat 聊天框，支持双语格式（中文一行外语一行）
- **历史记录**：所有对话可回看、搜索、重新翻译，不怕漏了哪句

### 进阶黑科技
- **真正的同声传译**：
  - 别人说话 → 识别 → 翻译 → TTS 念到你耳机里
  - 你说话 → 识别 → 翻译 → TTS 输出到虚拟音频线 → VRChat 里别人听到的就是翻译后的外语
- **多引擎翻译**：DeepSeek / Google / 百度 / 任何 OpenAI 兼容接口，随你切
- **AI 代聊**：输入你想表达的意思，AI 帮你写成自然的外语直接发出去
- **VB-CABLE 一键安装**：内置虚拟音频线下载安装引导，不用自己到处找
- **系统托盘常驻**：最小化到托盘，右键快速开关，不占任务栏

---

## 🚀 快速开始

### 普通用户（推荐）
1. 去 [Releases](https://github.com/XUEYUAN-QuaantumFrost/vrc-trans/releases) 下载最新版 `VRC_Translate.zip`
2. 解压到任意文件夹，双击 `VRC_Translate.exe`
3. 第一次启动会自动下载语音识别模型（约 1GB），等它下完就能用了

### 开发者（源码运行）
```bash
git clone https://github.com/XUEYUAN-QuaantumFrost/vrc-trans.git
cd vrc-trans
pip install -r requirements.txt
python main.py
```

---

## ⚙️ 常用设置说明

**翻译引擎选哪个？**
- 追求便宜好用：**DeepSeek**（去 platform.deepseek.com 申请 API Key，几块钱能用很久）
- 不想折腾：**Google**（免费，国内网络可能需要代理）

**OSC 设置**
- VRChat 里打开：设置 → OSC → Enable
- 默认地址 `127.0.0.1:9000`，一般不用改

**同声传译怎么开？**
1. 程序里点"一键安装 VB-CABLE"（虚拟音频线）
2. VRChat 麦克风选择「CABLE Output」
3. 你说中文 → 自动翻译成外语 → 通过虚拟音频线进 VRChat → 别人听到的就是外语

---

## 🎮 快捷键和小技巧

| 操作 | 效果 |
|------|------|
| 双击悬浮字幕 | 锁定/解锁位置（锁定后鼠标穿透） |
| 双击托盘图标 | 显示/隐藏字幕 |
| 托盘右键 | 快速改颜色、字体、透明度 |
| `Ctrl+Alt+L` | 快速锁定字幕位置 |

---

## ❓ 常见问题

**Q：识别没声音？**
A：检查录音设备选对了没。要录电脑里的声音需要立体声混音，或者用 VB-CABLE。

**Q：VRChat 里收不到字？**
A：确认 VRChat 设置里 OSC 开了，端口是 9000。

**Q：翻译报错/很慢？**
A：检查 API Key 对不对。Google 翻译国内可能需要代理。

**Q：模型下载失败？**
A：程序内置了多个镜像自动切换。实在不行去 Release 页手动下模型包，放到 `%APPDATA%\vrc_trans\models\` 里。

---

## 📁 项目结构

```
vrc-trans/
├── main.py                 # 程序入口，托盘图标，主循环
├── main_window.py          # 主界面控制面板
├── floating_subtitle.py     # 悬浮字幕窗口
├── speech_recognizer.py    # 语音识别（sherpa-onnx / faster-whisper）
├── translator.py            # AI 翻译（多引擎）
├── tts.py                  # 语音朗读
├── osc_sender.py           # OSC 发送到 VRChat
├── history_window.py       # 历史记录窗口
├── ai_chat.py              # AI 代聊窗口
├── bootstrap.py            # 首次运行初始化、模型下载
├── config.py               # 配置管理
├── i18n.py                 # 多语言
└── requirements.txt        # Python 依赖
```

---

## 🤝 贡献

欢迎提 Issue 和 PR！
- 发现 bug 请附上 `%APPDATA%\vrc_trans\app.log` 的最后几行
- 想加功能先提 Issue 讨论一下
- 开发日志见 [DEVELOPMENT_JOURNAL.md](DEVELOPMENT_JOURNAL.md)，更新日志见 [CHANGELOG.md](CHANGELOG.md)

---

## 📄 许可证

[MIT License](LICENSE) — 随便用，随便改，保留版权声明就行。

---

## 🙏 致谢

- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) — 流式语音识别引擎
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — 备用识别引擎
- [DeepSeek](https://www.deepseek.com) — 高性价比翻译 API
- [VB-Audio](https://vb-audio.com/Cable/) — 虚拟音频线
- 所有测过 bug、提过建议的朋友们
