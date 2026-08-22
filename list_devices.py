"""
列出所有音频设备，帮你找到立体声混音和麦克风的编号
运行: python list_devices.py
"""
import sounddevice as sd

print("=" * 70)
print("音频设备列表")
print("=" * 70)
print(f"{'编号':<6}{'输入通道':<10}{'输出通道':<10}{'设备名称'}")
print("-" * 70)

devices = sd.query_devices()
for i, d in enumerate(devices):
    in_ch = d.get("max_input_channels", 0)
    out_ch = d.get("max_output_channels", 0)
    name = d.get("name", "未知")
    marker = ""
    if in_ch > 0 and "立体声" in name:
        marker = "  ← 立体声混音（录电脑声音用这个）"
    elif in_ch > 0 and ("麦克风" in name or "mic" in name.lower() or "Microphone" in name):
        marker = "  ← 麦克风"
    print(f"{i:<6}{in_ch:<10}{out_ch:<10}{name}{marker}")

print("-" * 70)
print("\n提示：")
print("  - 录电脑声音（VRChat/视频）选『立体声混音』的编号")
print("  - 录麦克风说话选『麦克风』的编号")
print("  - 把编号填到设置面板的对应位置")
print()

# 显示默认设备
default = sd.query_devices(kind="input")
print(f"当前默认输入设备: {default['name']} (编号: {sd.default.device[0]})")
