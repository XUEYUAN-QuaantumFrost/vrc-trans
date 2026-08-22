"""
VRChat 实时翻译悬浮字幕
主程序入口
- 无边框悬浮窗，双语显示
- 系统托盘右键菜单
- 实时语音识别 + AI翻译 + OSC发送
"""
import sys
import os
import time
import threading
import faulthandler

# 屏蔽第三方库的烦人警告（NumPy版本不兼容、transformers禁用PyTorch等）
import warnings
warnings.filterwarnings("ignore")
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 避免 Intel OpenMP 库冲突（ctranslate2/numpy 都带 libiomp5md.dll，会导致 access violation）
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "2"  # 限制 OpenMP 线程数，减少内存占用和冲突
os.environ["MKL_NUM_THREADS"] = "2"  # Intel MKL 线程数
os.environ["OPENBLAS_NUM_THREADS"] = "2"  # OpenBLAS 线程数
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # 禁用 CUDA，强制 CPU，避免 GPU 驱动冲突
os.environ["ONNXRUNTIME_CPU_ONLY"] = "1"  # onnxruntime 强制 CPU

# 启用 faulthandler，捕获 C 层崩溃（如 ctranslate2 segfault）
faulthandler.enable()

# 强制 ctranslate2 只用 CPU，避免加载 CUDA 库失败
os.environ["CT2_CPU_ONLY"] = "1"

# 预加载 ctranslate2，避免与 PyQt5 的 DLL 冲突（必须在 PyQt5 之前导入）
try:
    import ctranslate2  # noqa: F401  # type: ignore
except ImportError:
    pass

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QSystemTrayIcon, QMenu, QAction, QColorDialog, QFontDialog,
    QSlider, QInputDialog, QMessageBox, QDialog, QTextEdit,
    QRadioButton, QButtonGroup, QPushButton, QGraphicsDropShadowEffect,
    QGroupBox
)
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QIcon, QPixmap, QPainterPath, QFontMetrics

from config import Config
from settings_dialog import SettingsDialog
from translator import Translator
from osc_sender import OSCSender
from history_window import HistoryWindow
from help_window import HelpWindow
from i18n import Locale, tr
import logger

log = logger.get_logger("main")



# ============================================================
#  带描边/阴影的文字标签
# ============================================================
class StrokeLabel(QLabel):
    """支持文字描边和阴影的 QLabel"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._stroke_enabled = False
        self._stroke_color = QColor("#000000")
        self._stroke_width = 2
        self._shadow_enabled = False
        self._shadow_color = QColor("#000000")
        self._shadow_blur = 4
        self._text_color = QColor("#FFFFFF")
        self.setMinimumHeight(1)  # 避免空文字时完全塌缩为0高度

    def set_text_color(self, color_str):
        self._text_color = QColor(color_str)
        self.update()

    def set_stroke(self, enabled, color="#000000", width=2):
        self._stroke_enabled = enabled
        self._stroke_color = QColor(color)
        self._stroke_width = width
        self.update()

    def set_shadow(self, enabled, color="#000000", blur=4):
        self._shadow_enabled = enabled
        self._shadow_color = QColor(color)
        self._shadow_blur = blur
        self.update()

    def sizeHint(self):
        """根据实际文字内容计算高度，空文字返回0，避免空白占位"""
        text = self.text()
        if not text or not text.strip():
            return QSize(0, 0)
        # 用 QFontMetrics 计算换行后的实际高度
        fm = QFontMetrics(self.font())
        width = max(self.width(), 100)
        # 模拟 wordwrap 计算行数
        rect = fm.boundingRect(0, 0, width, 10000,
                                Qt.TextWordWrap | Qt.AlignTop, text)
        h = rect.height() + 4  # 少量padding
        return QSize(width, h)

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        font = self.font()
        painter.setFont(font)
        text = self.text()
        if not text:
            painter.end()
            return
        # 计算文字位置（水平居中，顶部对齐，减小行间距）
        rect = self.rect()
        # 支持自动换行，顶部对齐避免多行时垂直居中产生多余空白
        flags = Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap
        # 阴影
        if self._shadow_enabled:
            offset = max(1, self._shadow_blur // 2)
            painter.setPen(QPen(self._shadow_color, self._stroke_width))
            painter.drawText(rect.adjusted(offset, offset, -offset, -offset), flags, text)
        # 描边
        if self._stroke_enabled:
            painter.setPen(QPen(self._stroke_color, self._stroke_width * 2))
            painter.drawText(rect, flags, text)
        # 填充文字（始终用自己的颜色，不被QSS覆盖）
        painter.setPen(QPen(self._text_color))
        painter.drawText(rect, flags, text)
        painter.end()


# ============================================================
#  悬浮字幕窗口
# ============================================================
class FloatingSubtitle(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self._drag_pos = None
        self._original_text = ""
        self._translate_text = ""
        self._corner_radius = 10
        self._edge_margin = 12      # 边缘检测宽度（加宽，更容易拖拽调整大小）
        self._resize_mode = None    # None / "move" / "left" / "right"
        self._drag_start_pos = None
        self._drag_start_width = 0
        self._drag_start_x = 0
        self._build_ui()
        self._apply_appearance()
        self._load_position()
        # 应用初始锁定状态
        self.set_locked(self.config.get("locked", False))

    def _build_ui(self):
        # 无边框 + 置顶 + 工具窗口（不占任务栏）
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(0)

        self.original_label = StrokeLabel("")
        self.original_label.setAlignment(Qt.AlignCenter)
        self.original_label.setWordWrap(True)

        self.translate_label = StrokeLabel("")
        self.translate_label.setAlignment(Qt.AlignCenter)
        self.translate_label.setWordWrap(True)

        layout.addWidget(self.original_label)
        layout.addWidget(self.translate_label)

        self.setMinimumWidth(200)
        self.setMinimumHeight(40)

    def _apply_appearance(self):
        """根据配置应用外观"""
        c = self.config
        font = QFont(c.get("font_family", "微软雅黑"), c.get("font_size", 18))

        self.original_label.setFont(font)
        self.translate_label.setFont(font)

        # 文字颜色（StrokeLabel 用自定义绘制，不用 stylesheet）
        self.original_label.set_text_color(c.get('original_color', '#87CEEB'))
        self.translate_label.set_text_color(c.get('translate_color', '#FFB6C1'))
        # 描边
        stroke_enabled = c.get('text_stroke_enabled', False)
        stroke_color = c.get('text_stroke_color', '#000000')
        stroke_width = c.get('text_stroke_width', 2)
        self.original_label.set_stroke(stroke_enabled, stroke_color, stroke_width)
        self.translate_label.set_stroke(stroke_enabled, stroke_color, stroke_width)
        # 阴影
        shadow_enabled = c.get('text_shadow_enabled', False)
        shadow_color = c.get('text_shadow_color', '#000000')
        shadow_blur = c.get('text_shadow_blur', 4)
        self.original_label.set_shadow(shadow_enabled, shadow_color, shadow_blur)
        self.translate_label.set_shadow(shadow_enabled, shadow_color, shadow_blur)

        # 文字对齐
        align_map = {"left": Qt.AlignLeft, "center": Qt.AlignCenter, "right": Qt.AlignRight}
        align = align_map.get(c.get("text_alignment", "center"), Qt.AlignCenter)
        self.original_label.setAlignment(align)
        self.translate_label.setAlignment(align)

        self.original_label.setVisible(c.get("show_original", True))
        self.translate_label.setVisible(c.get("show_translate", True))

        # 背景颜色和透明度通过 paintEvent 绘制
        self._bg_color = QColor(c.get("bg_color", "#000000"))
        self._bg_opacity = c.get("bg_opacity", 0.4)
        self._corner_radius = c.get("corner_radius", 10)
        self.update()

        # 调整宽度
        self.resize(c.get("window_width", 500), self.sizeHint().height())

    def _load_position(self):
        x = self.config.get("window_x", 100)
        y = self.config.get("window_y", 100)
        self.move(x, y)

    def paintEvent(self, event):
        """绘制半透明圆角背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg = QColor(self._bg_color)
        bg.setAlphaF(self._bg_opacity)
        painter.setBrush(QBrush(bg))
        painter.setPen(Qt.NoPen)
        r = getattr(self, '_corner_radius', 10)
        painter.drawRoundedRect(self.rect(), r, r)

    # ---- 文本更新 ----
    def set_text(self, original="", translate=""):
        self._original_text = original
        self._translate_text = translate
        # 根据显示模式控制标签可见性
        display_mode = self.config.get("subtitle_display_mode", "both")
        show_orig = display_mode in ("both", "original_only")
        show_trans = display_mode in ("both", "translate_only")
        # 空文字时也隐藏，避免空白占位
        self.original_label.setVisible(show_orig and bool(original and original.strip()))
        self.translate_label.setVisible(show_trans and bool(translate and translate.strip()))
        self.original_label.setText(original)
        self.translate_label.setText(translate)
        # 自适应高度
        QTimer.singleShot(10, self._adjust_height)

    def _adjust_height(self):
        # 只调整高度，保持当前宽度（避免覆盖用户拖拽的宽度）
        current_width = self.width()
        # 确保最小高度，避免空文字时窗口塌缩到不可见
        min_h = max(self.minimumHeight(), 40)
        new_h = max(self.sizeHint().height(), min_h)
        self.resize(current_width, new_h)

    # ---- 拖动 & 调整大小 ----
    def _hit_test(self, pos):
        """检测鼠标在哪个边缘"""
        x = pos.x()
        if x <= self._edge_margin:
            return "left"
        if x >= self.width() - self._edge_margin:
            return "right"
        return None

    def mousePressEvent(self, event):
        # 锁定时忽略所有鼠标事件，让事件穿透到下面的窗口
        if self.config.get("locked", False):
            event.ignore()
            return
        if event.button() == Qt.LeftButton:
            edge = self._hit_test(event.pos())
            if edge:
                # 边缘拖拽 = 调整大小
                self._resize_mode = edge
                self._drag_start_pos = event.globalPos()
                self._drag_start_width = self.width()
                self._drag_start_x = self.x()
            else:
                # 中间拖拽 = 移动窗口
                self._resize_mode = "move"
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self.config.get("locked", False):
            event.ignore()
            return

        if self._resize_mode == "move" and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        elif self._resize_mode == "left":
            delta = event.globalPos().x() - self._drag_start_pos.x()
            new_width = self._drag_start_width - delta
            if new_width >= 200:
                self.resize(new_width, self.height())
                self.move(self._drag_start_x + delta, self.y())
            event.accept()
        elif self._resize_mode == "right":
            delta = event.globalPos().x() - self._drag_start_pos.x()
            new_width = self._drag_start_width + delta
            if new_width >= 200:
                self.resize(new_width, self.height())
            event.accept()
        else:
            # 没在拖拽，更新光标形状
            edge = self._hit_test(event.pos())
            if edge:
                self.setCursor(Qt.SizeHorCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            event.ignore()

    def mouseReleaseEvent(self, event):
        if self.config.get("locked", False):
            event.ignore()
            return
        if self._resize_mode:
            self.config.set("window_width", self.width())
            self.config.set("window_x", self.x())
            self.config.set("window_y", self.y())
        self._drag_pos = None
        self._resize_mode = None
        self.setCursor(Qt.ArrowCursor)
        event.accept()

    def mouseDoubleClickEvent(self, event):
        """双击切换锁定/解锁（锁定后鼠标穿透，双击事件不会触发，需用托盘菜单/快捷键解锁）"""
        if self.config.get("locked", False):
            event.ignore()
            return
        locked = not self.config.get("locked", False)
        self.set_locked(locked)
        event.accept()

    # ---- 外部调用 ----
    def refresh_appearance(self):
        self._apply_appearance()

    def set_locked(self, locked):
        self.config.set("locked", locked)
        # 锁定时启用鼠标穿透，解锁时恢复
        # 窗口本身 + 所有子控件都要设置，确保完全穿透
        self.setAttribute(Qt.WA_TransparentForMouseEvents, locked)
        for child in self.findChildren(QWidget):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, locked)
        self.setToolTip(tr("locked_tooltip") if locked else tr("unlocked_tooltip"))
        # 强制刷新，确保属性立即生效
        self.update()
        self.repaint()


# ============================================================
#  业务控制器（信号桥接，线程安全）
# ============================================================
class Controller(QObject):
    show_text_signal = pyqtSignal(str, str)  # original, translate
    speech_result_signal = pyqtSignal(str)   # 语音识别结果（跨线程）
    speech_partial_signal = pyqtSignal(str)  # 流式识别部分结果（跨线程，实时更新字幕）
    mic_finalize_signal = pyqtSignal(str, str)  # 麦克风结果最终处理（跨线程）
    computer_finalize_signal = pyqtSignal(str, str)  # 电脑声音结果最终处理（跨线程）
    translate_done_signal = pyqtSignal(str, str)  # 翻译完成（跨线程）

    def __init__(self, config, floating, history_window=None):
        super().__init__()
        self.config = config
        self.floating = floating
        self.history_window = history_window
        self.translator = None
        self.osc = None
        self.speech = None
        self.speech_mic = None
        self.speech_computer = None
        self._send_timer = None
        self._pending_text = ""
        self._auto_activate_timer = None

        self.show_text_signal.connect(self._on_show_text)
        self.speech_result_signal.connect(self._handle_input)
        self.speech_partial_signal.connect(self._on_speech_partial)
        self.mic_finalize_signal.connect(self._mic_finalize)
        self.computer_finalize_signal.connect(self._computer_finalize)
        self.translate_done_signal.connect(self._finalize)
        # 连接历史窗口信号
        if self.history_window:
            self.history_window.retranslate_requested.connect(self._on_retranslate_history)
            self.history_window.resend_osc_requested.connect(self._on_resend_osc_history)
        self._init_modules()

    def _init_modules(self):
        c = self.config
        # 翻译
        self.translator = Translator(
            api_key=c.get("ai_api_key", "") or c.get("api_key", ""),
            api_base=c.get("ai_api_base", "") or c.get("api_base", "https://api.deepseek.com"),
            model=c.get("ai_model", "") or c.get("model", "deepseek-v4-flash"),
            target_lang=c.get("target_lang", "中文"),
            custom_prompt=c.get("custom_prompt", ""),
            timeout=30,
            engine=c.get("translate_engine", "deepseek"),
            baidu_appid=c.get("baidu_appid", ""),
            baidu_secret=c.get("baidu_secret", ""),
            provider=c.get("ai_provider", "deepseek"),
            azure_endpoint=c.get("ai_azure_endpoint", ""),
            azure_deployment=c.get("ai_azure_deployment", ""),
            azure_api_version=c.get("ai_azure_api_version", "2024-02-15-preview"),
        )
        # OSC
        self.osc = OSCSender(
            ip=c.get("osc_ip", "127.0.0.1"),
            port=c.get("osc_port", 9000),
        )
        # 语音识别
        if c.get("enable_speech", True):
            self._start_speech()

        # 自动激活输入框
        if c.get("enable_auto_activate", True):
            self._start_auto_activate()

    # ---- 公共接口：主界面开始/停止按钮 ----
    def start(self):
        """开始翻译（主界面「开始翻译」按钮调用）"""
        # 已经在运行就不重复启动
        if self.speech or getattr(self, 'speech_mic', None) or getattr(self, 'speech_computer', None):
            return
        self.config.set("enable_speech", True)
        self._start_speech()

    def stop(self):
        """停止翻译（主界面「停止翻译」按钮调用）"""
        self.config.set("enable_speech", False)
        self._stop_speech()

    def reload_modules(self):
        """设置变更后重新加载模块"""
        c = self.config
        # 更新翻译器（用新的统一 AI 配置，兼容旧键）
        self.translator.update_ai_config(
            api_key=c.get("ai_api_key", "") or c.get("api_key", ""),
            api_base=c.get("ai_api_base", "") or c.get("api_base", "https://api.deepseek.com"),
            model=c.get("ai_model", "") or c.get("model", "deepseek-v4-flash"),
            provider=c.get("ai_provider", "deepseek"),
            azure_endpoint=c.get("ai_azure_endpoint", ""),
            azure_deployment=c.get("ai_azure_deployment", ""),
            azure_api_version=c.get("ai_azure_api_version", "2024-02-15-preview"),
        )
        self.translator.target_lang = c.get("target_lang", "中文")
        self.translator.custom_prompt = c.get("custom_prompt", "")
        self.translator.engine = c.get("translate_engine", "deepseek")
        self.translator.baidu_appid = c.get("baidu_appid", "")
        self.translator.baidu_secret = c.get("baidu_secret", "")

        # 更新 OSC
        self.osc.update_endpoint(
            c.get("osc_ip", "127.0.0.1"),
            c.get("osc_port", 9000),
        )

        # 语音识别：设置变更后重启（确保双路/单路切换生效）
        if c.get("enable_speech", True):
            self._stop_speech()
            self._start_speech()
        else:
            self._stop_speech()

        # 自动激活
        if c.get("enable_auto_activate", True):
            self._start_auto_activate()
        else:
            self._stop_auto_activate()

    # ---- 语音识别 ----
    def _start_speech(self):
        from speech_recognizer import SpeechRecognizer
        c = self.config

        # 辅助函数：获取某路的引擎/模型配置（单独配置优先，留空用全局）
        def _get_eng_config(prefix):
            engine = c.get(f"{prefix}_whisper_engine", "") or c.get("whisper_engine", "sherpa")
            model = c.get(f"{prefix}_whisper_model", "") or c.get("whisper_model", "small")
            sherpa_id = c.get(f"{prefix}_sherpa_model_id", "") or c.get("sherpa_model_id", "streaming-paraformer-bilingual-zh-en")
            return engine, model, sherpa_id

        if c.get("dual_mode", False):
            # ===== 双向模式：同时启动两路 =====
            self.speech = None  # 单路模式不用
            # 麦克风 → OSC
            if c.get("enable_mic_to_osc", True):
                mic_engine, mic_model, mic_sherpa_id = _get_eng_config("mic")
                self.speech_mic = SpeechRecognizer(
                    record_source="mic",
                    device_computer=c.get("device_computer", 2),
                    device_mic=c.get("device_mic", 1),
                    whisper_model=mic_model,
                    whisper_engine=mic_engine,
                    sherpa_model_id=mic_sherpa_id,
                    whisper_device=c.get("whisper_device", "cpu"),
                    compute_type=c.get("compute_type", "int8"),
                    silence_threshold=c.get("silence_threshold", 250),
                    min_speech_duration=c.get("min_speech_duration", 200),
                    max_speech_duration=c.get("max_speech_duration", 10000),
                    vad_aggressiveness=c.get("vad_aggressiveness", 1),
                    filter_words=c.get("filter_words", ["嗯", "啊", "呃", "哦"]),
                    on_result=self._on_mic_result,
                    on_partial_result=self._on_speech_partial_result,
                    config=c,
                )
                self.speech_mic.start()
            else:
                self.speech_mic = None
            # 电脑声音 → 字幕
            if c.get("enable_computer_to_subtitle", True):
                comp_engine, comp_model, comp_sherpa_id = _get_eng_config("computer")
                self.speech_computer = SpeechRecognizer(
                    record_source="computer",
                    device_computer=c.get("device_computer", 2),
                    device_mic=c.get("device_mic", 1),
                    whisper_model=comp_model,
                    whisper_engine=comp_engine,
                    sherpa_model_id=comp_sherpa_id,
                    whisper_device=c.get("whisper_device", "cpu"),
                    compute_type=c.get("compute_type", "int8"),
                    silence_threshold=c.get("silence_threshold", 250),
                    min_speech_duration=c.get("min_speech_duration", 200),
                    max_speech_duration=c.get("max_speech_duration", 10000),
                    vad_aggressiveness=c.get("vad_aggressiveness", 1),
                    filter_words=c.get("filter_words", ["嗯", "啊", "呃", "哦"]),
                    on_result=self._on_computer_result,
                    on_partial_result=self._on_speech_partial_result,
                    config=c,
                )
                self.speech_computer.start()
            else:
                self.speech_computer = None
        else:
            # ===== 单路模式（原逻辑）=====
            self.speech_mic = None
            self.speech_computer = None
            self.speech = SpeechRecognizer(
                record_source=c.get("record_source", "computer"),
                device_computer=c.get("device_computer", 2),
                device_mic=c.get("device_mic", 1),
                whisper_model=c.get("whisper_model", "small"),
                whisper_engine=c.get("whisper_engine", "sherpa"),
                sherpa_model_id=c.get("sherpa_model_id", "streaming-paraformer-bilingual-zh-en"),
                whisper_device=c.get("whisper_device", "cpu"),
                compute_type=c.get("compute_type", "int8"),
                silence_threshold=c.get("silence_threshold", 250),
                min_speech_duration=c.get("min_speech_duration", 300),
                max_speech_duration=c.get("max_speech_duration", 15000),
                vad_aggressiveness=c.get("vad_aggressiveness", 2),
                filter_words=c.get("filter_words", ["嗯", "啊", "呃", "哦"]),
                on_result=self._on_speech_result,
                on_partial_result=self._on_speech_partial_result,
                config=c,
            )
            self.speech.start()

    def _stop_speech(self):
        if self.speech:
            self.speech.stop()
            self.speech = None
        # 双向模式：两路模型错开释放，避免 onnxruntime 同时释放导致堆损坏
        if getattr(self, 'speech_mic', None):
            self.speech_mic.stop()
            self.speech_mic = None
            # 如果两路都存在，中间加延迟，错开 onnxruntime session 释放
            if getattr(self, 'speech_computer', None):
                import time
                time.sleep(0.5)
        if getattr(self, 'speech_computer', None):
            self.speech_computer.stop()
            self.speech_computer = None

    def _on_speech_result(self, text, detected_lang="unknown"):
        """单路模式：语音识别结果回调（在子线程）"""
        if not text or not text.strip():
            return
        self.speech_result_signal.emit(text.strip())

    def _on_speech_partial_result(self, text):
        """流式识别部分结果回调（在子线程），实时更新字幕"""
        self.speech_partial_signal.emit(text if text else "")

    def _on_speech_partial(self, text):
        """主线程：流式识别部分结果处理，实时更新字幕显示（不触发翻译）"""
        if text and text.strip():
            # 只显示原文，翻译列显示省略号
            self.show_text_signal.emit(text.strip(), "...")
        # 如果 text 为空（一句话结束时的清空信号），不做任何操作，
        # 因为最终结果会通过 _on_speech_result 正常处理

    def _on_mic_result(self, text, detected_lang="unknown"):
        """双向模式-麦克风：识别 → 翻译 → OSC发送"""
        if not text or not text.strip():
            return
        text = text.strip()
        target_lang = self.config.get("mic_target_lang", "日语")
        # 仅原文模式跳过AI翻译，省token
        if self.config.get("subtitle_display_mode", "both") == "original_only":
            self._mic_translate_done(text, text)
        elif self.config.get("enable_translate", True) and self.translator.api_key:
            self.translator.translate_async(text, lambda r: self._mic_translate_done(text, r), target_lang)
        else:
            self._mic_translate_done(text, text)

    def _mic_translate_done(self, original, translated):
        """麦克风翻译完成 → OSC发送（子线程切主线程）"""
        self.mic_finalize_signal.emit(original, translated)

    def _mic_finalize(self, original, translated):
        """主线程：麦克风结果 OSC 发送 + 历史记录 + TTS 朗读 + 同声传译出站"""
        target_lang = self.config.get("mic_target_lang", "日语")
        self._add_history(original, translated, "mic", target_lang=target_lang)
        if self.config.get("enable_osc", True) and self.osc:
            self._send_osc_bilingual(original, translated)
        self._maybe_tts(original, translated)
        # 麦克风识别结果朗读（跟读/确认）
        if self.config.get("tts_read_mic_result", False):
            self._simul_tts(original, "tts_output_devices")
        # 同声传译出站：你说的话 → 翻译 → TTS 输出到虚拟音频线（VRChat 里用翻译语音说话）
        if self.config.get("simultaneous_interpretation_enabled", False) and self.config.get("simul_outbound_tts_enabled", True):
            self._simul_tts(translated, "simul_outbound_tts_device")

    def _on_computer_result(self, text, detected_lang="unknown"):
        """双向模式-电脑声音：识别 → 翻译 → 显示字幕"""
        if not text or not text.strip():
            return
        text = text.strip()
        target_lang = self.config.get("computer_target_lang", "中文")
        # 立即显示原文（信号跨线程自动到主线程）
        self.show_text_signal.emit(text, tr("translating"))
        # 仅原文模式跳过AI翻译，省token
        if self.config.get("subtitle_display_mode", "both") == "original_only":
            self._computer_translate_done(text, text)
        elif self.config.get("enable_translate", True) and self.translator.api_key:
            self.translator.translate_async(text, lambda r: self._computer_translate_done(text, r), target_lang)
        else:
            self._computer_translate_done(text, text)

    def _computer_translate_done(self, original, translated):
        """电脑声音翻译完成 → 信号切主线程处理（避免子线程操作UI崩溃）"""
        # print(f"[Debug] 电脑声音翻译完成，切主线程")
        self.computer_finalize_signal.emit(original, translated)

    def _computer_finalize(self, original, translated):
        """主线程：电脑声音结果 → 显示字幕 + 历史记录 + TTS + 同声传译入站"""
        target_lang = self.config.get("computer_target_lang", "中文")
        self._add_history(original, translated, "computer", target_lang=target_lang)
        self.show_text_signal.emit(original, translated)
        self._maybe_tts(original, translated)
        # 同声传译入站：别人说的话 → 翻译 → TTS 朗读到你的耳机/扬声器
        if self.config.get("simultaneous_interpretation_enabled", False) and self.config.get("simul_inbound_tts_enabled", True):
            self._simul_tts(translated, "simul_inbound_tts_device")

    # ---- 输入处理 ----
    def _handle_input(self, text):
        """处理一段输入文本：立即显示原文 + 立即翻译，OSC可延迟"""
        # print(f"[Debug] _handle_input: {text[:50]}")
        self._pending_text = text
        # 立即显示原文
        self.show_text_signal.emit(text, "翻译中...")
        # 立即开始翻译（不等延迟）
        self._do_translate()

    def _do_translate(self):
        """执行翻译（立即）"""
        text = self._pending_text
        if not text:
            return
        # 仅原文模式跳过AI翻译，省token
        if self.config.get("subtitle_display_mode", "both") == "original_only":
            self._on_translate_done(text)
            return
        # print(f"[Debug] _do_translate: api_key={'有' if self.translator.api_key else '无'}")
        if self.config.get("enable_translate", True) and self.translator.api_key:
            self.translator.translate_async(text, self._on_translate_done)
        else:
            self._on_translate_done(text)

    def _do_translate_and_send(self):
        """兼容旧调用：直接翻译"""
        self._do_translate()

    def _on_translate_done(self, translated):
        """翻译完成回调（子线程 -> 信号切主线程）"""
        original = self._pending_text
        # print(f"[Debug] 翻译完成: {translated[:50]}")
        self.translate_done_signal.emit(original, translated)

    def _finalize(self, original, translated):
        """主线程中最终处理：单路模式下根据配置决定显示字幕和/或发OSC"""
        source = self.config.get("record_source", "computer")
        target_lang = self.config.get("target_lang", "中文")
        self._add_history(original, translated, source, target_lang=target_lang)
        if self.config.get("single_show_subtitle", True):
            self.show_text_signal.emit(original, translated)
        if self.config.get("single_send_osc", True) and self.config.get("enable_osc", True) and self.osc:
            self._send_osc_bilingual(original, translated)
        self._maybe_tts(original, translated)

    def _maybe_tts(self, original, translated):
        """根据配置决定是否 TTS 朗读"""
        if not self.config.get("tts_enabled", False):
            return
        import tts
        import json
        text = original if self.config.get("tts_read_original", False) else translated
        if text and text.strip():
            # 解析输出设备列表
            devices_str = self.config.get("tts_output_devices", "")
            output_devices = None
            if devices_str:
                try:
                    output_devices = json.loads(devices_str)
                except Exception:
                    output_devices = None
            engine = self.config.get("tts_engine", "pyttsx3")
            # 根据引擎选择音色
            if engine == "edge":
                voice = self.config.get("tts_edge_voice", "zh-CN-XiaoxiaoNeural")
            elif engine == "volcengine":
                voice = self.config.get("tts_volc_voice", "BV001_streaming")
            else:
                voice = self.config.get("tts_voice", "") or None
            tts.speak(
                text,
                engine=engine,
                rate=self.config.get("tts_rate", 200),
                volume=self.config.get("tts_volume", 1.0),
                voice_id=voice,
                output_devices=output_devices,
                # 火山引擎参数
                volc_appid=self.config.get("tts_volc_appid", ""),
                volc_token=self.config.get("tts_volc_token", ""),
                volc_pitch=self.config.get("tts_volc_pitch", 1.0),
            )

    def _simul_tts(self, text, device_config_key):
        """同声传译专用 TTS：输出到指定设备（入站到耳机，出站到虚拟音频线）"""
        if not text or not text.strip():
            return
        try:
            import tts
            device_str = self.config.get(device_config_key, "")
            output_devices = None
            if device_str:
                try:
                    # 支持单个设备索引或 JSON 数组
                    if device_str.strip().startswith("["):
                        import json
                        output_devices = json.loads(device_str)
                    else:
                        output_devices = [int(device_str)]
                except Exception:
                    output_devices = None
            engine = self.config.get("tts_engine", "pyttsx3")
            if engine == "edge":
                voice = self.config.get("tts_edge_voice", "zh-CN-XiaoxiaoNeural")
            elif engine == "volcengine":
                voice = self.config.get("tts_volc_voice", "BV001_streaming")
            else:
                voice = self.config.get("tts_voice", "") or None
            tts.speak(
                text,
                engine=engine,
                rate=self.config.get("tts_rate", 200),
                volume=self.config.get("tts_volume", 1.0),
                voice_id=voice,
                output_devices=output_devices,
                volc_appid=self.config.get("tts_volc_appid", ""),
                volc_token=self.config.get("tts_volc_token", ""),
                volc_pitch=self.config.get("tts_volc_pitch", 1.0),
            )
        except Exception as e:
            print(f"[SimulTTS] 同声传译 TTS 失败: {e}")

    def _on_show_text(self, original, translate):
        # print(f"[Debug] 显示字幕: 原文={original[:30]} 翻译={translate[:30]}")
        self.floating.set_text(original, translate)
        self.floating.show()
        self.floating.raise_()
        # 强制立即重绘，避免窗口显示后内容消失
        self.floating.update()
        self.floating.repaint()

    # ---- 自动激活输入框 ----
    def _start_auto_activate(self):
        self._stop_auto_activate()
        interval = int(self.config.get("auto_activate_interval", 4) * 1000)
        self._auto_activate_timer = QTimer()
        self._auto_activate_timer.timeout.connect(self._activate_input)
        self._auto_activate_timer.start(interval)

    def _stop_auto_activate(self):
        if self._auto_activate_timer:
            self._auto_activate_timer.stop()
            self._auto_activate_timer = None

    def _activate_input(self):
        """模拟激活 VRChat 输入框（Windows 专用）"""
        if os.name != "nt":
            return
        try:
            # 找到 VRChat 窗口并发送一个无害的按键来保持焦点
            # 这里用简单的方式：发送 Shift 键（不会输入字符）
            import ctypes
            # 仅作占位，实际可根据需要扩展
            pass
        except Exception:
            pass

    def manual_send(self, text, mode="both"):
        """手动发送文本
        mode: both / osc_only / subtitle_only
        """
        text = text.strip()
        if not text:
            return
        self._pending_text = text
        self._manual_mode = mode
        # 立即显示原文
        self.show_text_signal.emit(text, tr("translating"))
        # 翻译
        if self.config.get("enable_translate", True) and self.translator.api_key:
            self.translator.translate_async(text, self._on_manual_translate_done)
        else:
            self._on_manual_translate_done(text)

    def _on_manual_translate_done(self, translated):
        """手动输入翻译完成"""
        original = self._pending_text
        mode = getattr(self, '_manual_mode', 'both')
        target_lang = self.config.get("target_lang", "中文")

        # 添加历史记录
        self._add_history(original, translated, "manual", target_lang=target_lang)

        # 根据模式决定输出
        if mode in ("both", "subtitle_only"):
            self.show_text_signal.emit(original, translated)
        if mode in ("both", "osc_only"):
            if self.config.get("enable_osc", True) and self.osc:
                self._send_osc_bilingual(original, translated)

    # ---- 历史记录 ----
    def _add_history(self, original, translated, source="manual",
                     original_lang="unknown", target_lang=""):
        """添加一条历史记录"""
        if self.history_window:
            self.history_window.add_entry(
                original=original,
                translated=translated,
                source=source,
                original_lang=original_lang,
                target_lang=target_lang,
            )

    def _on_retranslate_history(self, entry_id, target_lang):
        """历史窗口请求重新翻译某条"""
        if not self.history_window:
            return
        entry = self.history_window.get_entry(entry_id)
        if not entry:
            return
        original = entry.original
        if not original:
            return

        def _done(result):
            if self.history_window:
                self.history_window.update_entry(entry_id, translated=result, target_lang=target_lang)

        if self.config.get("enable_translate", True) and self.translator.api_key:
            self.translator.translate_async(original, _done, target_lang)
        else:
            _done(original)

    def _on_resend_osc_history(self, entry_id):
        """历史窗口请求重新发送某条到 OSC"""
        if not self.history_window or not self.osc:
            return
        entry = self.history_window.get_entry(entry_id)
        if not entry:
            return
        self._send_osc_bilingual(entry.original, entry.translated)

    # ---- 双语 OSC 发送 ----
    def _send_osc_bilingual(self, original, translated):
        """根据配置发送双语或单语 OSC"""
        if not self.osc:
            return
        # 打字指示器
        if self.config.get("enable_osc_typing", True):
            self.osc.send_typing(False)

        if not self.config.get("osc_bilingual", False):
            # 单语模式：仅翻译
            send_text = translated if translated else original
            self.osc.send_chatbox(send_text, send_immediately=True)
            return

        # 双语模式
        fmt = self.config.get("osc_bilingual_format", "multiline")
        order = self.config.get("osc_bilingual_order", "original_first")
        text = self._build_bilingual_text(original, translated, fmt, order)
        self.osc.send_chatbox(text, send_immediately=True)

    @staticmethod
    def _build_bilingual_text(original, translated, fmt, order):
        """构建双语文本"""
        if not translated or translated == original:
            return original or translated or ""
        if order == "translate_first":
            first, second = translated, original
        else:
            first, second = original, translated

        # VRChat chatbox 限制 144 字符，多行格式超长时自动改用括号格式
        VRC_LIMIT = 144
        if fmt == "multiline":
            multiline_text = f"{first}\n{second}"
            if len(multiline_text) <= VRC_LIMIT:
                return multiline_text
            # 超长：自动改用括号格式，如果还是超长就截断译文
            parenthesis_text = f"{first} ({second})"
            if len(parenthesis_text) <= VRC_LIMIT:
                return parenthesis_text
            # 还是超长：截断译文，保留原文完整
            avail = VRC_LIMIT - len(first) - 3  # 3 = " (" + ")"
            if avail > 10:
                return f"{first} ({second[:avail-1]}…)"
            else:
                return first[:VRC_LIMIT]
        elif fmt == "parenthesis":
            text = f"{first} ({second})"
            if len(text) > VRC_LIMIT:
                avail = VRC_LIMIT - len(first) - 3
                if avail > 10:
                    return f"{first} ({second[:avail-1]}…)"
                return first[:VRC_LIMIT]
            return text
        elif fmt == "slash":
            text = f"{first} / {second}"
            if len(text) > VRC_LIMIT:
                avail = VRC_LIMIT - len(first) - 3
                if avail > 10:
                    return f"{first} / {second[:avail-1]}…"
                return first[:VRC_LIMIT]
            return text
        elif fmt == "translate_only":
            return translated[:VRC_LIMIT]
        else:
            return f"{first}\n{second}"[:VRC_LIMIT]

    def shutdown(self):
        self._stop_speech()
        self._stop_auto_activate()
        if self._send_timer:
            self._send_timer.stop()
        # 退出前强制垃圾回收，确保 sherpa-onnx/onnxruntime 资源完全释放，避免堆损坏
        import gc
        gc.collect()
        import time
        time.sleep(0.3)


# ============================================================
#  手动输入对话框
# ============================================================
class ManualInputDialog(QDialog):
    """手动输入文字对话框，可选择发送目标"""
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(tr("manual_input_title"))
        self.setMinimumWidth(400)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(tr("manual_input_prompt")))
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(80)
        layout.addWidget(self.text_edit)

        # 发送目标选择
        mode_group = QGroupBox("发送到：")
        mode_layout = QHBoxLayout(mode_group)
        self.mode_buttons = QButtonGroup(self)

        self.radio_both = QRadioButton("字幕 + OSC")
        self.radio_osc = QRadioButton("仅 OSC")
        self.radio_subtitle = QRadioButton("仅字幕")

        self.mode_buttons.addButton(self.radio_both, 0)
        self.mode_buttons.addButton(self.radio_osc, 1)
        self.mode_buttons.addButton(self.radio_subtitle, 2)

        mode_layout.addWidget(self.radio_both)
        mode_layout.addWidget(self.radio_osc)
        mode_layout.addWidget(self.radio_subtitle)
        layout.addWidget(mode_group)

        # 恢复上次选择
        mode = self.config.get("manual_input_mode", "both")
        {"both": self.radio_both, "osc_only": self.radio_osc, "subtitle_only": self.radio_subtitle}.get(mode, self.radio_both).setChecked(True)

        # 按钮
        btn_layout = QHBoxLayout()
        speak_btn = QPushButton("🔊 朗读")
        speak_btn.setToolTip("用 TTS 朗读输入框中的文字")
        speak_btn.clicked.connect(self._on_speak)
        btn_layout.addWidget(speak_btn)
        btn_layout.addStretch()
        ok_btn = QPushButton(tr("btn_ok"))
        cancel_btn = QPushButton(tr("btn_cancel"))
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _on_ok(self):
        # 保存模式选择
        mode_id = self.mode_buttons.checkedId()
        mode_map = {0: "both", 1: "osc_only", 2: "subtitle_only"}
        self.config.set("manual_input_mode", mode_map.get(mode_id, "both"))
        self.accept()

    def _on_speak(self):
        """朗读输入框中的文字"""
        text = self.text_edit.toPlainText().strip()
        if not text:
            return
        try:
            import tts
            import json
            # 解析输出设备
            devices_str = self.config.get("tts_output_devices", "")
            output_devices = None
            if devices_str:
                try:
                    output_devices = json.loads(devices_str)
                except Exception:
                    output_devices = None
            engine = self.config.get("tts_engine", "pyttsx3")
            if engine == "edge":
                voice = self.config.get("tts_edge_voice", "zh-CN-XiaoxiaoNeural")
            elif engine == "volcengine":
                voice = self.config.get("tts_volc_voice", "BV001_streaming")
            else:
                voice = self.config.get("tts_voice", "") or None
            tts.speak(
                text,
                engine=engine,
                rate=self.config.get("tts_rate", 200),
                volume=self.config.get("tts_volume", 1.0),
                voice_id=voice,
                output_devices=output_devices,
                volc_appid=self.config.get("tts_volc_appid", ""),
                volc_token=self.config.get("tts_volc_token", ""),
                volc_pitch=self.config.get("tts_volc_pitch", 1.0),
            )
        except Exception as e:
            print(f"[ManualInput] 朗读失败: {e}")

    def get_text(self):
        return self.text_edit.toPlainText().strip()

    def get_mode(self):
        mode_id = self.mode_buttons.checkedId()
        return {0: "both", 1: "osc_only", 2: "subtitle_only"}.get(mode_id, "both")


# ============================================================
#  系统托盘
# ============================================================
class TrayIcon(QSystemTrayIcon):
    def __init__(self, config, floating, controller, parent=None, history_window=None):
        super().__init__(parent)
        self.config = config
        self.floating = floating
        self.controller = controller
        self.app = parent
        self.history_window = history_window
        self.ai_chat_window = None
        self.help_window = None
        self._config_reload_timer = None  # 配置变更防抖定时器

        self.setIcon(self._make_icon())
        self.setToolTip(tr("tray_title"))

        self._build_menu()
        self.activated.connect(self._on_activated)

    def _make_icon(self):
        """生成一个简单的托盘图标"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor("#87CEEB")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 24, 24)
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "译")
        painter.end()
        return QIcon(pixmap)

    def _build_menu(self):
        menu = QMenu()

        # 显示主界面
        show_main_action = QAction("显示主界面", self)
        show_main_action.triggered.connect(self._show_main_window)
        menu.addAction(show_main_action)

        menu.addSeparator()

        # 显示/隐藏
        self.toggle_visible_action = QAction(tr("hide_subtitle"), self)
        self.toggle_visible_action.triggered.connect(self._toggle_visible)
        menu.addAction(self.toggle_visible_action)

        menu.addSeparator()

        # 锁定/解锁
        self.toggle_lock_action = QAction(tr("lock_position"), self)
        self.toggle_lock_action.triggered.connect(self._toggle_lock)
        menu.addAction(self.toggle_lock_action)

        menu.addSeparator()

        # 设置
        settings_action = QAction(tr("settings"), self)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        # 字体
        font_action = QAction(tr("font"), self)
        font_action.triggered.connect(self._choose_font)
        menu.addAction(font_action)

        # 字幕颜色子菜单
        color_menu = menu.addMenu(tr("subtitle_color"))
        orig_color_action = QAction(tr("original_color"), self)
        orig_color_action.triggered.connect(lambda: self._choose_color("original_color"))
        color_menu.addAction(orig_color_action)
        trans_color_action = QAction(tr("translate_color"), self)
        trans_color_action.triggered.connect(lambda: self._choose_color("translate_color"))
        color_menu.addAction(trans_color_action)

        # 背景颜色
        bg_color_action = QAction(tr("bg_color"), self)
        bg_color_action.triggered.connect(lambda: self._choose_color("bg_color"))
        menu.addAction(bg_color_action)

        # 背景透明度
        opacity_action = QAction(tr("bg_opacity"), self)
        opacity_action.triggered.connect(self._choose_opacity)
        menu.addAction(opacity_action)

        menu.addSeparator()

        # 手动输入
        manual_action = QAction(tr("manual_input"), self)
        manual_action.triggered.connect(self._manual_input)
        menu.addAction(manual_action)

        # 历史记录
        self.toggle_history_action = QAction(tr("history_window"), self)
        self.toggle_history_action.triggered.connect(self._toggle_history)
        menu.addAction(self.toggle_history_action)

        # 同声传译
        self.toggle_simul_action = QAction("同声传译：关", self)
        self.toggle_simul_action.setToolTip("开启后，别人说的话翻译后朗读到耳机，你说的话翻译后输出到虚拟音频线")
        self.toggle_simul_action.triggered.connect(self._toggle_simul)
        menu.addAction(self.toggle_simul_action)

        # AI 代聊
        ai_chat_action = QAction(tr("ai_chat"), self)
        ai_chat_action.triggered.connect(self._open_ai_chat)
        menu.addAction(ai_chat_action)

        # 帮助/说明书
        help_action = QAction(tr("help_menu"), self)
        help_action.triggered.connect(self._open_help)
        menu.addAction(help_action)

        # 关于
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._open_about)
        menu.addAction(about_action)

        # TTS 语音朗读开关
        self.toggle_tts_action = QAction(tr("tts_enable"), self)
        self.toggle_tts_action.triggered.connect(self._toggle_tts)
        menu.addAction(self.toggle_tts_action)

        menu.addSeparator()

        # 退出
        quit_action = QAction(tr("quit"), self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        self._update_menu_text()

    def _update_menu_text(self):
        self.toggle_visible_action.setText(
            tr("hide_subtitle") if self.floating.isVisible() else tr("show_subtitle")
        )
        self.toggle_lock_action.setText(
            tr("unlock_position") if self.config.get("locked", False) else tr("lock_position")
        )
        self.toggle_tts_action.setText(
            tr("tts_disable") if self.config.get("tts_enabled", False) else tr("tts_enable")
        )
        self.toggle_simul_action.setText(
            "同声传译：开" if self.config.get("simultaneous_interpretation_enabled", False) else "同声传译：关"
        )

    def _on_main_config_changed(self):
        """主界面配置变更后防抖刷新：500ms 内多次变更只重载一次模块"""
        try:
            self.floating.refresh_appearance()
        except Exception:
            pass
        try:
            if self.history_window:
                self.history_window.refresh_appearance()
        except Exception:
            pass
        self._update_menu_text()
        # 防抖：500ms 内多次变更只重载一次模块，避免点击卡顿
        if self._config_reload_timer is None:
            from PyQt5.QtCore import QTimer
            self._config_reload_timer = QTimer()
            self._config_reload_timer.setSingleShot(True)
            self._config_reload_timer.timeout.connect(self._do_reload_modules)
        self._config_reload_timer.start(500)

    def _do_reload_modules(self):
        """真正执行模块重载（防抖定时器触发）"""
        try:
            self.controller.reload_modules()
        except Exception as e:
            print(f"[Main] 模块重载失败: {e}")

    def _on_appearance_changed(self):
        """仅外观变更：只刷新外观，不重载模块（无卡顿）"""
        try:
            self.floating.refresh_appearance()
        except Exception:
            pass
        try:
            if self.history_window:
                self.history_window.refresh_appearance()
        except Exception:
            pass

    def _install_vbcable(self):
        """下载并安装 VB-CABLE 虚拟音频线，安装后恢复默认音频设备"""
        try:
            from bootstrap import install_vb_cable
            install_vb_cable(parent=self)
        except Exception as e:
            print(f"[Main] VB-CABLE 安装失败: {e}")
            QMessageBox.warning(None, "VB-CABLE", f"安装失败: {e}\n请手动访问 https://vb-audio.com/Cable/ 下载安装")

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._toggle_visible()

    def _show_main_window(self):
        """显示主界面（若主界面对象不存在则尝试创建）"""
        mw = getattr(self, 'main_window', None)
        if mw is None:
            # 首次创建失败时，通过托盘菜单重新创建
            try:
                from main_window import MainWindow
                mw = MainWindow(self.config, history_window=getattr(self, 'history_window', None))
                self.main_window = mw
                mw.start_clicked.connect(self.controller.start)
                mw.stop_clicked.connect(self.controller.stop)
                mw.settings_clicked.connect(self._open_settings)
                mw.history_clicked.connect(self._toggle_history)
                mw.manual_input_clicked.connect(self._manual_input)
                mw.ai_chat_clicked.connect(self._open_ai_chat)
                mw.help_clicked.connect(self._open_help)
                mw.about_clicked.connect(self._open_about)
                mw.quit_clicked.connect(self._quit)
                mw.config_changed.connect(self._on_main_config_changed)
                mw.appearance_changed.connect(self._on_appearance_changed)
                mw.install_vbcable_clicked.connect(self._install_vbcable)
                mw.lock_toggled.connect(self.floating.set_locked)
                mw.target_lang_changed.connect(lambda _lang: self.controller.reload_modules())
                mw.translate_engine_changed.connect(lambda _eng: self.controller.reload_modules())
                def _is_running(r):
                    return r is not None and getattr(r, '_running', False)
                if _is_running(self.controller.speech) or _is_running(getattr(self.controller, 'speech_mic', None)) or _is_running(getattr(self.controller, 'speech_computer', None)):
                    mw.set_running(True)
            except Exception as e:
                print(f"[Main] 主界面创建失败: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.warning(None, "主界面", f"主界面创建失败：{e}")
                return
        mw.show()
        mw.raise_()
        mw.activateWindow()
        if hasattr(mw, 'refresh'):
            mw.refresh()

    def _toggle_visible(self):
        if self.floating.isVisible():
            self.floating.hide()
            self.config.set("visible", False)
            # 隐藏字幕时也隐藏历史记录窗口
            if self.history_window and self.history_window.isVisible():
                self.history_window.hide()
        else:
            self.floating.show()
            self.config.set("visible", True)
        self._update_menu_text()

    def _toggle_lock(self):
        locked = not self.config.get("locked", False)
        self.floating.set_locked(locked)
        self._update_menu_text()

    def _open_settings(self):
        # 防止重复创建设置窗口
        if hasattr(self, '_settings_dlg') and self._settings_dlg is not None:
            self._settings_dlg.raise_()
            self._settings_dlg.activateWindow()
            return
        # 传入当前活动的识别器，用于设置界面的实时音量指示器
        recognizer = getattr(self, 'speech', None) or getattr(self, 'speech_mic', None) or getattr(self, 'speech_computer', None)
        self._settings_dlg = SettingsDialog(self.config, self.floating, recognizer)
        dlg = self._settings_dlg
        # 设置窗口默认显示在主窗口旁边，而不是屏幕左上角
        self._position_dialog_next_to_main(dlg)
        if dlg.exec_():
            self.floating.refresh_appearance()
            if self.history_window:
                self.history_window.refresh_appearance()
            self.controller.reload_modules()
            # 刷新主界面状态
            mw = getattr(self, 'main_window', None)
            if mw is not None:
                mw.refresh()
            # 语言变更后重建托盘菜单
            self._build_menu()
            self.showMessage(tr("config_saved"), tr("settings_saved"),
                             QSystemTrayIcon.Information, 2000)
        self._settings_dlg = None

    def _position_dialog_next_to_main(self, dlg):
        # 把对话框放到主窗口右侧（空间不够则放左侧），垂直居中对齐
        mw = getattr(self, 'main_window', None)
        if mw is None or not mw.isVisible():
            screen = QApplication.primaryScreen().availableGeometry()
            dlg.move(screen.center().x() - dlg.width() // 2,
                     screen.center().y() - dlg.height() // 2)
            return
        mg = mw.geometry()
        screen = QApplication.primaryScreen().availableGeometry()
        gap = 12
        right_x = mg.right() + gap
        if right_x + dlg.width() <= screen.right():
            x = right_x
        elif mg.left() - gap - dlg.width() >= screen.left():
            x = mg.left() - gap - dlg.width()
        else:
            x = screen.center().x() - dlg.width() // 2
        y = mg.center().y() - dlg.height() // 2
        y = max(screen.top() + 10, min(y, screen.bottom() - dlg.height() - 10))
        dlg.move(x, y)

    def _choose_font(self):
        font, ok = QFontDialog.getFont(
            QFont(self.config.get("font_family"), self.config.get("font_size")),
            None, tr("choose_font")
        )
        if ok:
            self.config.set("font_family", font.family())
            self.config.set("font_size", font.pointSize())
            self.floating.refresh_appearance()

    def _choose_color(self, key):
        current = self.config.get(key, "#FFFFFF")
        color = QColorDialog.getColor(QColor(current), None, tr("bg_color"))
        if color.isValid():
            self.config.set(key, color.name())
            self.floating.refresh_appearance()

    def _choose_opacity(self):
        current = int(self.config.get("bg_opacity", 0.4) * 100)
        value, ok = QInputDialog.getInt(
            None, tr("opacity_title"), tr("opacity_prompt"),
            current, 0, 100, 5
        )
        if ok:
            self.config.set("bg_opacity", value / 100.0)
            self.floating.refresh_appearance()

    def _manual_input(self):
        dlg = ManualInputDialog(self.config)
        if dlg.exec_():
            text = dlg.get_text()
            mode = dlg.get_mode()
            if text:
                self.controller.manual_send(text, mode=mode)

    def _toggle_history(self):
        """显示/隐藏历史记录窗口"""
        if not self.history_window:
            return
        if self.history_window.isVisible():
            self.history_window.hide()
            self.config.set("history_visible", False)
        else:
            self.history_window.show()
            self.history_window.raise_()
            self.config.set("history_visible", True)

    def _toggle_simul(self):
        """切换同声传译开关"""
        enabled = not self.config.get("simultaneous_interpretation_enabled", False)
        self.config.set("simultaneous_interpretation_enabled", enabled)
        self._update_menu_text()
        if enabled:
            self.showMessage(
                "同声传译已开启",
                "别人说的话将翻译后朗读到耳机，你说的话将翻译后输出到虚拟音频线。\n请确保已在设置中配置好输出设备。",
                QSystemTrayIcon.Information,
                4000,
            )
        else:
            self.showMessage("同声传译已关闭", "同声传译功能已关闭。", QSystemTrayIcon.Information, 2000)

    def _open_ai_chat(self):
        """打开 AI 代聊窗口"""
        if self.ai_chat_window is None:
            from ai_chat import AIChatWindow
            self.ai_chat_window = AIChatWindow(self.config, self.controller)
        self.ai_chat_window.show()
        self.ai_chat_window.raise_()
        self.ai_chat_window.activateWindow()

    def _open_help(self):
        """打开帮助/说明书窗口"""
        if self.help_window is None:
            self.help_window = HelpWindow()
        self.help_window.show()
        self.help_window.raise_()
        self.help_window.activateWindow()

    def _open_about(self):
        """打开关于窗口"""
        from about_window import AboutDialog
        dlg = AboutDialog()
        dlg.exec_()

    def _toggle_tts(self):
        """切换 TTS 朗读开关"""
        enabled = not self.config.get("tts_enabled", False)
        self.config.set("tts_enabled", enabled)
        self._update_menu_text()
        if enabled:
            import tts
            if not tts.is_available():
                QMessageBox.warning(None, "TTS", "TTS 不可用，请安装 pyttsx3：pip install pyttsx3")
                self.config.set("tts_enabled", False)
                self._update_menu_text()
                return
            self.showMessage("TTS", tr("tts_enabled_msg"), QSystemTrayIcon.Information, 2000)
        else:
            import tts
            tts.stop()

    def _check_update(self):
        """手动检查更新"""
        from update_checker import check_for_update, CURRENT_VERSION
        self.showMessage(tr("check_update"), tr("checking_update"), QSystemTrayIcon.Information, 2000)
        def _callback(has_update, latest, url, notes):
            if has_update:
                msg = tr("update_available") + ": " + CURRENT_VERSION + " -> " + latest + "\n\n" + notes + "\n\n" + url
                QMessageBox.information(None, tr("check_update"), msg)
            else:
                QMessageBox.information(None, tr("check_update"), tr("update_latest"))
        check_for_update(_callback)

    def _quit(self):
        self.controller.shutdown()
        self.app.quit()


# ============================================================
#  主入口
# ============================================================
def main():
    # 全局异常捕获：确保任何错误都打印到控制台
    def _global_excepthook(exc_type, exc_value, exc_traceback):
        import traceback
        print("\n" + "="*60)
        print("[FATAL ERROR] 程序发生未捕获异常:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print("="*60 + "\n")
        # 不调用 input() 阻塞 GUI 线程，只打印日志
        # 非致命异常让程序继续运行，方便用户截图反馈
    sys.excepthook = _global_excepthook

    # 高 DPI 支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关窗不退出，保留托盘

    # 应用深色主题（默认）
    try:
        from theme import apply_theme
        apply_theme(app, "dark")
    except Exception as e:
        print(f"[Theme] 主题应用失败: {e}")

    # 设置 Windows 深色标题栏
    try:
        from win_dark_titlebar import apply_dark_to_all_windows
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(500, apply_dark_to_all_windows)
        dark_timer = QTimer()
        dark_timer.timeout.connect(apply_dark_to_all_windows)
        dark_timer.start(2000)
    except Exception as e:
        print(f"[DarkTitlebar] 设置失败: {e}")

    # 首次运行自检：检查模型/FFmpeg，缺失则自动下载
    try:
        from bootstrap import run_bootstrap
        config_tmp = Config()
        run_bootstrap(
            model_name=config_tmp.get("whisper_model", "small"),
            show_gui=True,
            engine=config_tmp.get("whisper_engine", "sherpa"),
            sherpa_model_id=config_tmp.get("sherpa_model_id", "streaming-paraformer-bilingual-zh-en"),
        )
    except Exception as e:
        print(f"[Main] Bootstrap skipped: {e}")

    # 检查是否需要重启（NumPy 降级等）
    if os.environ.get("VRC_TRANS_NEED_RESTART") == "1":
        reason = os.environ.get("VRC_TRANS_RESTART_REASON", "unknown")
        print(f"[Main] 检测到需要重启（原因: {reason}），正在重启程序...")
        # 清除环境变量，避免子进程继承后无限重启
        os.environ.pop("VRC_TRANS_NEED_RESTART", None)
        os.environ.pop("VRC_TRANS_RESTART_REASON", None)
        import subprocess
        # 启动新进程（Windows 上创建新控制台，避免与当前进程输出混乱）
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
        subprocess.Popen([sys.executable] + sys.argv, cwd=os.getcwd(), **kwargs)
        # 退出当前进程（此时托盘还没创建，不需要清理）
        sys.exit(0)

    # 检查 noisereduce 是否可用，不可用则后台自动升级 scipy + noisereduce
    _upgrade_done = {"done": False, "success": False, "need_restart": False}
    
    def _check_and_fix_noisereduce_background():
        # 如果已经尝试过修复，就不再尝试，直接用内置降噪
        if os.environ.get("VRC_TRANS_SCIPY_FIX_ATTEMPTED") == "1":
            print("[Main] 已尝试过修复 noisereduce，仍不可用，使用内置降噪")
            _upgrade_done["done"] = True
            _upgrade_done["success"] = False
            _upgrade_done["need_restart"] = False
            return
        try:
            import noisereduce as nr
            print(f"[Main] noisereduce {getattr(nr, '__version__', '?')} 可用，使用高质量降噪")
            _upgrade_done["done"] = True
            _upgrade_done["success"] = True
            _upgrade_done["need_restart"] = False  # 本来就能用，不需要重启
            return
        except Exception as e:
            print(f"[Main] noisereduce 不可用: {type(e).__name__}: {e}")
            print("[Main] 正在后台自动升级 scipy + noisereduce，请稍候...")
            # 标记已尝试修复
            os.environ["VRC_TRANS_SCIPY_FIX_ATTEMPTED"] = "1"
            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", "scipy>=1.11", "noisereduce>=3.0.0", "--quiet"],
                    capture_output=True, text=True, timeout=300
                )
                _upgrade_done["done"] = True
                if result.returncode == 0:
                    print("[Main] scipy + noisereduce 升级成功！需要重启程序才能生效")
                    _upgrade_done["success"] = True
                    _upgrade_done["need_restart"] = True  # 升级成功，需要重启
                    # 标记需要重启
                    os.environ["VRC_TRANS_NEED_RESTART"] = "1"
                    os.environ["VRC_TRANS_RESTART_REASON"] = "noisereduce_upgraded"
                else:
                    print(f"[Main] 自动升级失败: {result.stderr}")
                    print("[Main] 将使用内置降噪（效果略差）。可手动执行: pip install --upgrade scipy noisereduce")
            except Exception as e2:
                print(f"[Main] 自动升级异常: {e2}")
                print("[Main] 将使用内置降噪。可手动执行: pip install --upgrade scipy noisereduce")
                _upgrade_done["done"] = True
    
    import threading
    _noise_thread = threading.Thread(target=_check_and_fix_noisereduce_background, daemon=True)
    _noise_thread.start()
    
    # 主线程轮询升级结果，显示托盘消息（避免在后台线程用 QTimer）
    def _poll_upgrade_result():
        if _upgrade_done["done"] and _upgrade_done["success"] and _upgrade_done.get("need_restart", False):
            # 只有升级成功后才需要重启，noisereduce 本来就能用不需要重启
            try:
                tray.showMessage(
                    "降噪依赖已升级",
                    "scipy 和 noisereduce 已自动升级，程序将在 3 秒后自动重启",
                    QSystemTrayIcon.Information,
                    5000,
                )
            except Exception:
                pass
            # 3 秒后自动重启（先清理托盘）
            def _do_restart():
                try:
                    tray.hide()
                except Exception:
                    pass
                try:
                    controller.shutdown()
                except Exception:
                    pass
                # 清除环境变量，避免子进程继承后无限重启
                os.environ.pop("VRC_TRANS_NEED_RESTART", None)
                os.environ.pop("VRC_TRANS_RESTART_REASON", None)
                import subprocess
                kwargs = {}
                if sys.platform == "win32":
                    kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
                subprocess.Popen([sys.executable] + sys.argv, cwd=os.getcwd(), **kwargs)
                app.quit()
                sys.exit(0)
            QTimer.singleShot(3000, _do_restart)
        elif not _upgrade_done["done"]:
            QTimer.singleShot(2000, _poll_upgrade_result)
    
    QTimer.singleShot(3000, _poll_upgrade_result)

    config = Config()

    # 设置界面语言
    Locale().set_language(config.get("language", "auto"))

    # 全局界面字体大小
    ui_font_size = config.get("ui_font_size", 0)
    if ui_font_size and ui_font_size > 0:
        font = app.font()
        font.setPointSize(ui_font_size)
        app.setFont(font)

    # 悬浮窗
    floating = FloatingSubtitle(config)
    if config.get("visible", True):
        floating.show()

    # 历史记录窗口
    history_window = HistoryWindow(config)
    if config.get("history_visible", False):
        history_window.show()

    # 控制器
    controller = Controller(config, floating, history_window)

    # 托盘
    tray = TrayIcon(config, floating, controller, app, history_window)
    tray.show()
    tray.showMessage(
        tr("tray_title"),
        tr("tray_started"),
        QSystemTrayIcon.Information,
        3000,
    )

    # 主界面
    main_window = None
    try:
        from main_window import MainWindow
        main_window = MainWindow(config, history_window=history_window)
        # 先把引用给托盘并立即显示，避免后续信号连接出错导致窗口不出现
        tray.main_window = main_window
        main_window.show()
        main_window.raise_()
        main_window.activateWindow()
    except Exception as e:
        print(f"[Main] 主界面创建失败: {e}")
        import traceback
        traceback.print_exc()

    # 连接主界面信号（即使部分失败也不影响窗口显示）
    if main_window is not None:
        try:
            main_window.start_clicked.connect(controller.start)
            main_window.stop_clicked.connect(controller.stop)
            main_window.settings_clicked.connect(tray._open_settings)
            main_window.history_clicked.connect(tray._toggle_history)
            main_window.manual_input_clicked.connect(tray._manual_input)
            main_window.ai_chat_clicked.connect(tray._open_ai_chat)
            main_window.help_clicked.connect(tray._open_help)
            main_window.about_clicked.connect(tray._open_about)
            main_window.quit_clicked.connect(tray._quit)
            main_window.config_changed.connect(tray._on_main_config_changed)
            main_window.appearance_changed.connect(tray._on_appearance_changed)
            main_window.install_vbcable_clicked.connect(tray._install_vbcable)
            main_window.lock_toggled.connect(floating.set_locked)
            def _on_subtitle_toggle(checked):
                if checked:
                    floating.show()
                else:
                    floating.hide()
                config.set("visible", checked)
            main_window.subtitle_toggled.connect(_on_subtitle_toggle)
            def _on_tts_toggle(checked):
                config.set("tts_enabled", checked)
                tray._update_menu_text()
                main_window.refresh()
            main_window.tts_toggled.connect(_on_tts_toggle)
            def _on_simul_toggle(checked):
                config.set("simultaneous_interpretation_enabled", checked)
                tray._update_menu_text()
                if checked:
                    tray.showMessage("同声传译已开启", "别人说的话将翻译后朗读到耳机，你说的话将翻译后输出到虚拟音频线。", QSystemTrayIcon.Information, 4000)
            main_window.simul_toggled.connect(_on_simul_toggle)
            def _on_target_lang_changed(_lang):
                # config 已由主界面写入，只需重载模块
                controller.reload_modules()
            main_window.target_lang_changed.connect(_on_target_lang_changed)
            def _on_engine_changed(_eng):
                controller.reload_modules()
                main_window.refresh()
            main_window.translate_engine_changed.connect(_on_engine_changed)
            # 同步主界面初始状态：程序启动时若已自动开始识别，按钮显示「停止翻译」
            try:
                def _is_running(r):
                    return r is not None and getattr(r, '_running', False)
                if _is_running(controller.speech) or _is_running(getattr(controller, 'speech_mic', None)) or _is_running(getattr(controller, 'speech_computer', None)):
                    main_window.set_running(True)
            except Exception:
                pass
        except Exception as e:
            print(f"[Main] 主界面信号连接失败: {e}")
            import traceback
            traceback.print_exc()

    # 新手引导（第一次运行自动弹出）
    try:
        from tutorial_window import should_show_tutorial, TutorialWindow
        if should_show_tutorial():
            QTimer.singleShot(1000, lambda: TutorialWindow().exec_())
    except Exception as e:
        print(f"[Tutorial] 新手引导启动失败: {e}")

    # 注册快捷键
    try:
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        # 显示/隐藏字幕（parent 用 floating 窗口）
        sc1 = QShortcut(QKeySequence(config.get("hotkey_toggle_subtitle", "Ctrl+Alt+S")), floating)
        sc1.activated.connect(lambda: floating.setVisible(not floating.isVisible()))
        # 显示/隐藏历史记录（parent 用 history_window）
        sc2 = QShortcut(QKeySequence(config.get("hotkey_toggle_history", "Ctrl+Alt+H")), history_window)
        sc2.activated.connect(lambda: history_window.setVisible(not history_window.isVisible()))
        # 历史窗口锁定切换快捷键（锁定后鼠标穿透，需用快捷键解锁）
        sc3 = QShortcut(QKeySequence(config.get("hotkey_toggle_history_lock", "Ctrl+Alt+L")), history_window)
        sc3.activated.connect(lambda: history_window.set_locked(not history_window.config.get("history_locked", False)))
    except Exception as e:
        print(f"[Hotkey] 快捷键注册失败: {e}")

    log.info("程序启动完成，进入事件循环")
    # 启动时自动检查更新（暂时禁用，等有服务器后再开启）
    # if config.get("check_update_on_start", True):
    #     from update_checker import check_for_update, CURRENT_VERSION
    #     def _update_cb(has_update, latest, url, notes):
    #         if has_update:
    #             tray.showMessage(
    #                 tr("update_available"),
    #                 "v" + latest + "\n" + tr("update_tip"),
    #                 QSystemTrayIcon.Information, 8000
    #             )
    #     QTimer.singleShot(3000, lambda: check_for_update(_update_cb))
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
