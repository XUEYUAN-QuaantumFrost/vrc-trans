# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec 文件 for VRChat 翻译悬浮字幕 - V5 修复版
使用方法：pyinstaller VRC_Translate.spec

设计原则：
- 默认引擎是 sherpa-onnx，不收集 faster-whisper / ctranslate2 / torch 等重型依赖
- 模型运行时下载，不打进 EXE
- 精确收集 sherpa-onnx 和 onnxruntime 的必要文件
- 彻底排除可能导致冲突的大包
"""
import os
import sys
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files, collect_all

block_cipher = None

# 项目根目录
project_dir = os.path.dirname(os.path.abspath(SPEC))

# ============================================================
# 数据源文件（项目自身的 py 模块作为数据文件打包，确保运行时可导入）
# ============================================================
datas = []
for py_file in [
    'i18n.py', 'config.py', 'translator.py', 'osc_sender.py',
    'speech_recognizer.py', 'settings_dialog.py', 'history_window.py',
    'ai_chat.py', 'list_devices.py', 'bootstrap.py', 'logger.py',
    'tts.py', 'update_checker.py', 'ai_client.py', 'theme.py',
    'tutorial_window.py', 'about_window.py', 'sherpa_recognizer.py',
    'win_dark_titlebar.py', 'help_window.py', 'main_window.py',
]:
    src = os.path.join(project_dir, py_file)
    if os.path.exists(src):
        datas.append((src, '.'))

# ============================================================
# 二进制动态库收集
# ============================================================
binaries = []

# numpy 的动态库（onnxruntime 依赖）
try:
    binaries += collect_dynamic_libs('numpy')
except Exception as e:
    print(f"[SPEC] 收集 numpy 动态库失败: {e}")

# onnxruntime（sherpa-onnx 依赖）
try:
    ort_datas, ort_binaries, ort_hidden = collect_all('onnxruntime')
    datas += ort_datas
    binaries += ort_binaries
    print(f"[SPEC] onnxruntime: {len(ort_datas)} datas, {len(ort_binaries)} binaries")
except Exception as e:
    print(f"[SPEC] 收集 onnxruntime 失败: {e}")

# sherpa-onnx 中文识别引擎
try:
    so_datas, so_binaries, so_hidden = collect_all('sherpa_onnx')
    datas += so_datas
    binaries += so_binaries
    print(f"[SPEC] sherpa_onnx: {len(so_datas)} datas, {len(so_binaries)} binaries")
except Exception as e:
    print(f"[SPEC] 收集 sherpa_onnx 失败: {e}")

# ============================================================
# 隐藏导入（明确列出需要的模块）
# ============================================================
hiddenimports = [
    # 核心依赖
    'sherpa_onnx',
    'onnxruntime',
    'webrtcvad',
    'sounddevice',
    'soundfile',
    'pythonosc',
    'pythonosc.udp_client',
    'pythonosc.dispatcher',
    'openai',
    'numpy',
    'numpy.core._methods',
    'numpy.lib.format',
    # PyQt5
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    # TTS（可选）
    'pyttsx3',
    # 项目自身模块
    'logger',
    'tts',
    'update_checker',
    'ai_client',
    'sherpa_recognizer',
    'bootstrap',
    'speech_recognizer',
    'main_window',
    # setuptools / pkg_resources（webrtcvad 需要）
    'pkg_resources',
    'setuptools',
    'setuptools._distutils',
    # 音频后端
    'sounddevice._sounddevice_data',
    'cffi',
    'pycparser',
]

# ============================================================
# 排除列表（明确排除这些大包，避免被误收集导致打包失败或 EXE 崩溃）
# ============================================================
excludes = [
    # 深度学习框架（默认不用 faster-whisper）
    'torch', 'torchaudio', 'torchvision',
    'transformers', 'tokenizers', 'huggingface_hub',
    'ctranslate2', 'faster_whisper',
    'tensorboardX', 'tensorboard',
    'funasr', 'modelscope',
    # ONNX 相关（只用 onnxruntime，不用 onnx 包本身）
    'onnx', 'onnxconverter-common', 'skl2onnx', 'tf2onnx',
    # TensorFlow / Keras
    'tensorflow', 'keras', 'tf_keras',
    # 机器学习
    'sklearn', 'scikit-learn', 'scipy', 'pandas',
    # 可视化
    'matplotlib', 'seaborn', 'plotly', 'bokeh',
    # Jupyter / IPython
    'IPython', 'jupyter', 'jupyter_client', 'jupyter_core', 'nbformat', 'nbconvert',
    # 图像处理（不用）
    'PIL', 'pillow', 'cv2', 'opencv-python', 'scikit-image',
    # NLP 相关
    'sentencepiece', 'safetensors', 'datasets', 'evaluate',
    'accelerate', 'bitsandbytes', 'peft', 'trl', 'deepspeed',
    # 其他可能导致冲突的包
    'pywin32', 'win32com', 'pythoncom',
    'tornado', 'flask', 'django', 'fastapi', 'uvicorn',
    'zmq', 'pyzmq',
    'yaml', 'ruamel.yaml',
    'lxml', 'beautifulsoup4', 'bs4',
    'cryptography', 'pyOpenSSL',
    'werkzeug', 'jinja2', 'markupsafe',
    'blinker', 'click', 'itsdangerous',
]

# ============================================================
# Analysis
# ============================================================
a = Analysis(
    ['main.py'],
    pathex=[project_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VRC_Translate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 正式发布版不显示控制台；调试时可改回 True 查看报错
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico',
)
