# VRC Trans — Real-time Translation Subtitles for VRChat

> Floating translation subtitles that hover on your screen like music lyrics. Chat with people from all over the world in VRChat without looking down at your phone.
> Dual audio recognition (mic + system sound), AI translation, OSC auto-send to VRChat chat, simultaneous interpretation, and TTS voice output — all built in.

[中文](README.zh-CN.md) | English

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Version](https://img.shields.io/badge/Version-0.2.4.6-orange)

---

## Why VRC Trans?

| Feature | VRC Trans | Web Translators | Other VRChat Tools |
|---------|-----------|----------------|--------------------|
| Floating overlay subtitles | ✅ Transparent, draggable | ❌ Browser window | Partial |
| OSC auto-send to VRChat chat | ✅ One-click bilingual send | ❌ Manual copy-paste | Partial |
| Simultaneous interpretation | ✅ TTS + virtual audio cable | ❌ Not available | Rarely included |
| Resumable model downloads | ✅ Pause and resume anytime | — | Often restart from scratch |
| All settings on main window | ✅ No nested menus | — | Buried in settings pages |
| Free and open source | ✅ MIT license | Free but closed source | Some paid |

**One click "Start" — translation, chat-box sending, and voice output are all handled for you.**

---

## Features

### Core
- **Floating subtitles**: Semi-transparent overlay on top of everything. Drag, resize, change color/font/opacity. Locked mode makes it click-through.
- **Dual audio recognition**: Recognize both your mic and system audio (foreign language playing in-game) at the same time.
- **Streaming recognition**: Powered by sherpa-onnx, results appear as people speak — low latency, no waiting.
- **OSC auto-send**: Translated text goes straight to VRChat chat box, with bilingual format support.
- **History**: Review, search, and re-translate past conversations.

### Advanced
- **True simultaneous interpretation**:
  - Others speak → recognize → translate → TTS plays in your headphones
  - You speak → recognize → translate → TTS outputs to virtual audio cable → others hear you in their language
- **Multiple translation engines**: DeepSeek / Google / Baidu / any OpenAI-compatible API
- **AI chat assistant**: Type what you want to say, AI writes it naturally in the foreign language
- **One-click VB-CABLE installer**: No need to hunt down virtual audio cable downloads yourself
- **System tray**: Minimize to tray, right-click quick toggles, no taskbar clutter

---

## Quick Start

### For Users (Recommended)
1. Download the latest `VRC_Translate.zip` from [Releases](https://github.com/XUEYUAN-QuaantumFrost/vrc-trans/releases)
2. Extract anywhere, run `VRC_Translate.exe`
3. First launch auto-downloads the speech recognition model (~1GB)

### For Developers
```bash
git clone https://github.com/XUEYUAN-QuaantumFrost/vrc-trans.git
cd vrc-trans
pip install -r requirements.txt
python main.py
```

---

## FAQ

**Q: No audio being recognized?**
A: Check your recording device selection. To capture system audio you need stereo mix or VB-CABLE.

**Q: VRChat not receiving text?**
A: Make sure OSC is enabled in VRChat settings (Settings → OSC → Enable), port 9000.

**Q: Translation errors or slow?**
A: Check your API key. Google Translate may need a proxy in some regions.

**Q: Model download failing?**
A: Built-in multiple mirrors auto-switch. You can also manually download from the Release page and place it in `%APPDATA%\vrc_trans\models\`.

---

## License
[MIT](LICENSE) — Use it, modify it, no strings attached.
