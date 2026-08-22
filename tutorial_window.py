"""
新手引导窗口
第一次运行时自动弹出，一步步介绍功能
"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QStackedWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class TutorialWindow(QDialog):
    """新手引导窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新手引导")
        self.setFixedSize(520, 380)
        self.setWindowFlags(
            Qt.Dialog
            | Qt.WindowStaysOnTopHint
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
            | Qt.WindowCloseButtonHint
        )
        self._current_step = 0
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 20)

        # 标题
        title = QLabel("🚀 欢迎使用 VRChat 实时翻译悬浮字幕")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(10)

        # 内容区域（多步）
        self.stack = QStackedWidget()
        self.stack.addWidget(self._step1())
        self.stack.addWidget(self._step2())
        self.stack.addWidget(self._step3())
        self.stack.addWidget(self._step4())
        self.stack.addWidget(self._step5())
        layout.addWidget(self.stack, 1)

        # 步骤指示
        self.step_label = QLabel("1 / 5")
        self.step_label.setStyleSheet("color: gray; font-size: 11px;")
        self.step_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.step_label)

        # 按钮
        btn_layout = QHBoxLayout()
        self.prev_btn = QPushButton("上一步")
        self.prev_btn.clicked.connect(self._prev)
        self.prev_btn.setEnabled(False)
        btn_layout.addWidget(self.prev_btn)

        btn_layout.addStretch()

        self.skip_btn = QPushButton("跳过引导")
        self.skip_btn.clicked.connect(self._skip)
        btn_layout.addWidget(self.skip_btn)

        self.next_btn = QPushButton("下一步")
        self.next_btn.clicked.connect(self._next)
        btn_layout.addWidget(self.next_btn)

        layout.addLayout(btn_layout)

    def _make_step(self, title: str, content: str) -> QWidget:
        """创建一个步骤页面"""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        t = QLabel(title)
        t.setFont(QFont("Arial", 12, QFont.Bold))
        t.setStyleSheet("color: #0078d4;")
        layout.addWidget(t)

        c = QLabel(content)
        c.setWordWrap(True)
        c.setStyleSheet("font-size: 13px; line-height: 1.6;")
        c.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(c, 1)

        return w

    def _step1(self) -> QWidget:
        return self._make_step(
            "第一步：配置翻译 API",
            "右键点击右下角托盘图标 → 选择「设置」→「翻译」Tab。\n\n"
            "选择 AI 提供商并填入 API Key：\n"
            "• DeepSeek（推荐）：platform.deepseek.com\n"
            "• OpenAI：platform.openai.com\n"
            "• 豆包：console.volcengine.com/ark\n"
            "• Google 翻译：免费，无需 API Key\n\n"
            "每个提供商的 API Key 独立保存，切换时自动加载。"
        )

    def _step2(self) -> QWidget:
        return self._make_step(
            "第二步：配置语音识别",
            "在设置 →「语音识别」Tab：\n\n"
            "• 电脑声音：选择「立体声混音」（录制 VRChat 里其他人说话）\n"
            "• 麦克风：选择你的麦克风设备\n"
            "• 有 NVIDIA 显卡选 cuda + float16，速度快\n"
            "• 没显卡选 cpu + int8\n\n"
            "首次启动会自动下载语音识别模型（约460MB）。"
        )

    def _step3(self) -> QWidget:
        return self._make_step(
            "第三步：开启 VRChat OSC",
            "在 VRChat 中开启 OSC：\n"
            "设置 → OSC → 启用 OSC\n\n"
            "默认 IP 127.0.0.1，端口 9000，无需修改。\n\n"
            "开启后，你说的话会自动翻译并发送到 VRChat 聊天框，"
            "电脑里的声音会自动翻译成字幕显示在屏幕上。"
        )

    def _step4(self) -> QWidget:
        return self._make_step(
            "第四步：常用操作",
            "• 双击托盘图标：显示/隐藏字幕窗口\n"
            "• 右键托盘图标：打开设置、历史记录、AI 代聊、帮助\n"
            "• 拖拽字幕窗口：移动位置\n"
            "• 拖拽字幕窗口边缘：调整大小\n"
            "• 历史记录窗口：查看所有翻译记录，可重新翻译\n"
            "• AI 代聊：不在电脑旁时，AI 自动回复朋友消息"
        )

    def _step5(self) -> QWidget:
        return self._make_step(
            "完成！开始使用吧",
            "现在你已经了解了基本功能，可以开始使用了！\n\n"
            "如果遇到问题：\n"
            "• 设置 → 其他 →「还原工具」可以重装依赖、重新下载模型\n"
            "• 托盘 →「帮助」查看详细说明书\n"
            "• 托盘 →「关于」查看版本和依赖信息\n\n"
            "祝你使用愉快！🎮"
        )

    def _next(self):
        if self._current_step < self.stack.count() - 1:
            self._current_step += 1
            self.stack.setCurrentIndex(self._current_step)
            self._update_buttons()
        else:
            self._finish()

    def _prev(self):
        if self._current_step > 0:
            self._current_step -= 1
            self.stack.setCurrentIndex(self._current_step)
            self._update_buttons()

    def _skip(self):
        self._finish()

    def _finish(self):
        # 标记已看过引导
        try:
            from config import Config
            cfg = Config()
            cfg.set("tutorial_seen", True)
        except Exception:
            pass
        self.accept()

    def _update_buttons(self):
        self.prev_btn.setEnabled(self._current_step > 0)
        self.next_btn.setText("完成" if self._current_step == self.stack.count() - 1 else "下一步")
        self.step_label.setText(f"{self._current_step + 1} / {self.stack.count()}")


def should_show_tutorial() -> bool:
    """是否应该显示新手引导（第一次运行）"""
    try:
        from config import Config
        cfg = Config()
        return not cfg.get("tutorial_seen", False)
    except Exception:
        return True
