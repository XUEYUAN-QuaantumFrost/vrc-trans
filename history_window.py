"""
历史记录窗口模块
- 无边框半透明窗口，风格与主悬浮窗一致
- 显示翻译历史记录（时间戳 + 来源 + 原文 + 翻译）
- 支持右键菜单：重新翻译、复制、重发OSC、删除
- 支持双击快速重新翻译
- 支持清空、持久化开关
"""
import time
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QCheckBox, QMenu, QAction,
    QInputDialog, QApplication, QScrollBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QEvent
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QCursor

from i18n import tr

# 重新翻译可选的目标语言列表
RETARGET_LANGUAGES = [
    "中文", "繁體中文", "日语", "韩语", "英语", "法语", "德语",
    "俄语", "西班牙语", "阿拉伯语", "蒙古语", "葡萄牙语", "意大利语",
    "越南语", "泰语",
]

# 来源标签显示名
SOURCE_LABELS = {
    "mic": "MIC",
    "computer": "PC",
    "manual": "MANUAL",
    "aichat": "AI",
}


@dataclass
class HistoryEntry:
    """一条历史记录"""
    id: int
    timestamp: float
    source: str           # mic / computer / manual / aichat
    original: str
    translated: str
    original_lang: str = "unknown"
    target_lang: str = ""

    def time_str(self) -> str:
        return time.strftime("%H:%M:%S", time.localtime(self.timestamp))


class HistoryItemWidget(QWidget):
    """单条历史记录的自定义 widget（只创建一次 layout，更新时只改子 widget 内容，不重建 layout）"""
    def __init__(self, entry: HistoryEntry, font_size: int = 18, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.font_size = font_size
        # 子 widget 作为成员变量，更新时只改内容，不重建
        self._time_label = None
        self._src_label = None
        self._orig_label = None
        self._trans_label = None
        self._build_ui()
        self._update_content()
        self._update_style()

    def _build_ui(self):
        """只调用一次：创建 layout 和所有子 widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        # 顶部行：时间 + 来源
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        self._time_label = QLabel()
        top_row.addWidget(self._time_label)
        self._src_label = QLabel()
        top_row.addWidget(self._src_label)
        top_row.addStretch()
        layout.addLayout(top_row)

        # 原文
        self._orig_label = QLabel()
        self._orig_label.setWordWrap(True)
        self._orig_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self._orig_label)

        # 翻译
        self._trans_label = QLabel()
        self._trans_label.setWordWrap(True)
        self._trans_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self._trans_label)

    def _update_content(self):
        """更新子 widget 的文本和可见性（不重建 layout）"""
        if self._time_label:
            self._time_label.setText(self.entry.time_str())
        if self._src_label:
            src = SOURCE_LABELS.get(self.entry.source, self.entry.source.upper())
            self._src_label.setText(f"[{src}]")
        if self._orig_label:
            has_orig = bool(self.entry.original)
            self._orig_label.setText(self.entry.original if has_orig else "")
            self._orig_label.setVisible(has_orig)
        if self._trans_label:
            has_trans = bool(self.entry.translated and self.entry.translated != self.entry.original)
            self._trans_label.setText(self.entry.translated if has_trans else "")
            self._trans_label.setVisible(has_trans)

    def _update_style(self):
        """更新子 widget 的样式表（字体大小）"""
        small_size = max(self.font_size - 4, 8)
        if self._time_label:
            self._time_label.setStyleSheet(f"color: rgba(255,255,255,0.5); font-size: {small_size}px;")
        if self._src_label:
            self._src_label.setStyleSheet(f"color: rgba(255,255,255,0.4); font-size: {small_size}px;")
        if self._orig_label:
            self._orig_label.setStyleSheet(f"color: #87CEEB; font-size: {self.font_size}px;")
        if self._trans_label:
            self._trans_label.setStyleSheet(f"color: #FFB6C1; font-size: {self.font_size}px;")

    def update_entry(self, entry: HistoryEntry):
        """更新记录内容（只改子 widget 文本，不重建 layout）"""
        self.entry = entry
        self._update_content()
        self.updateGeometry()

    def set_font_size(self, font_size: int):
        """更新字体大小（只改样式表，不重建 layout）"""
        self.font_size = font_size
        self._update_style()
        self.updateGeometry()


class HistoryWindow(QWidget):
    """历史记录窗口"""
    # 信号：请求重新翻译某条
    retranslate_requested = pyqtSignal(int, str)   # entry_id, target_lang
    # 信号：请求重新发送 OSC
    resend_osc_requested = pyqtSignal(int)         # entry_id
    # 信号：请求删除某条
    delete_requested = pyqtSignal(int)             # entry_id
    # 信号：历史记录发生变化（新增/更新/清空），主界面内嵌历史面板用
    history_changed = pyqtSignal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.entries: List[HistoryEntry] = []
        self._next_id = 1
        self._drag_pos = None
        self._edge_margin = 8
        self._resize_mode = None
        self._drag_start_pos = None
        self._drag_start_geometry = None

        self._build_ui()
        self._apply_appearance()
        self._load_position()
        self.set_locked(self.config.get("history_locked", False))

        # 加载持久化记录
        if self.config.get("history_save_to_file", False):
            self._load_from_file()

    def _build_ui(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")  # 强制透明，不被深色主题覆盖

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 容器 widget（用于绘制圆角背景）
        self._container = QWidget()
        self._container.setObjectName("historyContainer")
        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(10, 6, 10, 10)
        container_layout.setSpacing(4)

        # 顶部工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        title_label = QLabel("⋮⋮  " + tr("history_title"))
        title_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 16px; font-weight: bold;")
        title_label.setCursor(Qt.SizeAllCursor)
        title_label.installEventFilter(self)
        self._drag_handle = title_label
        toolbar.addWidget(title_label)
        toolbar.addStretch()

        self.save_cb = QCheckBox(tr("history_save_toggle"))
        self.save_cb.setChecked(self.config.get("history_save_to_file", False))
        self.save_cb.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 13px;")
        self.save_cb.stateChanged.connect(self._on_save_toggle)
        toolbar.addWidget(self.save_cb)

        # 锁定按钮
        self.lock_btn = QPushButton("🔒" if self.config.get("history_locked", False) else "🔓")
        self.lock_btn.setFixedHeight(20)
        self.lock_btn.setFixedWidth(28)
        self.lock_btn.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.15); color: white; border: none; "
            "border-radius: 4px; font-size: 14px; }"
            "QPushButton:hover { background: rgba(255,255,255,0.25); }"
        )
        self.lock_btn.clicked.connect(self._toggle_lock)
        self.lock_btn.setToolTip("锁定/解锁窗口位置")
        toolbar.addWidget(self.lock_btn)

        self.clear_btn = QPushButton(tr("history_clear"))
        self.clear_btn.setFixedHeight(20)
        self.clear_btn.setStyleSheet(
            "QPushButton { background: rgba(255,80,80,0.3); color: white; border: none; "
            "border-radius: 4px; padding: 0 8px; font-size: 13px; }"
            "QPushButton:hover { background: rgba(255,80,80,0.5); }"
        )
        self.clear_btn.clicked.connect(self._on_clear)
        toolbar.addWidget(self.clear_btn)

        container_layout.addLayout(toolbar)

        # 历史列表
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            "QListWidget { background: transparent; border: none; outline: none; }"
            "QListWidget::item { background: transparent; border-bottom: 1px solid rgba(255,255,255,0.08); }"
            "QListWidget::item:selected { background: rgba(255,255,255,0.1); }"
            "QScrollBar:vertical { background: transparent; width: 6px; }"
            "QScrollBar::handle:vertical { background: rgba(255,255,255,0.2); border-radius: 3px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._on_context_menu)
        self.list_widget.itemDoubleClicked.connect(self._on_double_click)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        container_layout.addWidget(self.list_widget, 1)

        main_layout.addWidget(self._container)

        self.setMinimumSize(250, 150)
        self.resize(
            self.config.get("history_window_width", 450),
            self.config.get("history_window_height", 300)
        )

    def _apply_appearance(self):
        c = self.config
        self._bg_color = QColor(c.get("bg_color", "#000000"))
        self._bg_opacity = c.get("bg_opacity", 0.4)
        self._corner_radius = c.get("corner_radius", 10)
        self.update()

    def _load_position(self):
        x = self.config.get("history_window_x", 100)
        y = self.config.get("history_window_y", 200)
        self.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg = QColor(self._bg_color)
        bg.setAlphaF(self._bg_opacity)
        painter.setBrush(QBrush(bg))
        painter.setPen(Qt.NoPen)
        r = getattr(self, '_corner_radius', 10)
        painter.drawRoundedRect(self.rect(), r, r)

    # ---- 公开 API ----
    def add_entry(self, original: str, translated: str, source: str = "manual",
                  original_lang: str = "unknown", target_lang: str = "") -> HistoryEntry:
        """添加一条历史记录"""
        if not original and not translated:
            return None

        entry = HistoryEntry(
            id=self._next_id,
            timestamp=time.time(),
            source=source,
            original=original,
            translated=translated,
            original_lang=original_lang,
            target_lang=target_lang,
        )
        self._next_id += 1
        self.entries.append(entry)

        # 限制最大条数
        max_items = self.config.get("history_max_items", 200)
        while len(self.entries) > max_items:
            old = self.entries.pop(0)
            self._remove_item_by_id(old.id)

        # 添加到列表
        self._append_item(entry)
        self._scroll_to_bottom()

        # 持久化
        if self.config.get("history_save_to_file", False):
            self._save_to_file()
        self.history_changed.emit()

        return entry

    def update_entry(self, entry_id: int, translated: str = None, target_lang: str = None):
        """更新某条记录（重新翻译后调用）"""
        for entry in self.entries:
            if entry.id == entry_id:
                if translated is not None:
                    entry.translated = translated
                if target_lang is not None:
                    entry.target_lang = target_lang
                # 更新列表中的 widget
                for i in range(self.list_widget.count()):
                    item = self.list_widget.item(i)
                    widget = self.list_widget.itemWidget(item)
                    if widget and widget.entry.id == entry_id:
                        widget.update_entry(entry)
                        break
                break
        if self.config.get("history_save_to_file", False):
            self._save_to_file()
        self.history_changed.emit()

    def get_entry(self, entry_id: int) -> Optional[HistoryEntry]:
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None

    def clear_all(self):
        """清空所有记录"""
        self.entries.clear()
        self.list_widget.clear()
        self.list_widget.update()
        if self.config.get("history_save_to_file", False):
            self._save_to_file()
        self.history_changed.emit()

    def refresh_appearance(self):
        self._apply_appearance()
        # 更新所有历史条目的字体大小，同时清理没有 widget 的空 item
        font_size = self.config.get("history_font_size", 18)
        to_remove = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget and hasattr(widget, 'set_font_size'):
                widget.set_font_size(font_size)
                item.setSizeHint(widget.sizeHint())
            elif widget is None:
                to_remove.append(i)
        # 倒序移除空 item
        for i in reversed(to_remove):
            self.list_widget.takeItem(i)
        self.list_widget.update()

    def set_locked(self, locked: bool):
        self.config.set("history_locked", locked)
        # 锁定时鼠标穿透，可点击下方内容；用快捷键 Ctrl+Alt+L 解锁
        self.setAttribute(Qt.WA_TransparentForMouseEvents, locked)
        if hasattr(self, 'lock_btn'):
            self.lock_btn.setText("🔒" if locked else "🔓")
        self.update()

    def _toggle_lock(self):
        """切换锁定状态"""
        locked = not self.config.get("history_locked", False)
        self.set_locked(locked)

    # ---- 内部方法 ----
    def _append_item(self, entry: HistoryEntry):
        item = QListWidgetItem()
        font_size = self.config.get("history_font_size", 18)
        widget = HistoryItemWidget(entry, font_size=font_size)
        item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)
        # 内存优化：超过最大条数时删除最早的记录
        max_entries = self.config.get("history_max_items", 200)
        while self.list_widget.count() > max_entries:
            self.list_widget.takeItem(0)

    def _remove_item_by_id(self, entry_id: int):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget and widget.entry.id == entry_id:
                self.list_widget.takeItem(i)
                break

    def _scroll_to_bottom(self):
        scrollbar = self.list_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _selected_entry(self) -> Optional[HistoryEntry]:
        item = self.list_widget.currentItem()
        if not item:
            return None
        widget = self.list_widget.itemWidget(item)
        if widget:
            return widget.entry
        return None

    # ---- 事件处理 ----
    def _on_context_menu(self, pos: QPoint):
        entry = self._selected_entry()
        if not entry:
            return

        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: rgba(40,40,40,0.95); color: white; border: 1px solid rgba(255,255,255,0.2); }"
            "QMenu::item:selected { background: rgba(100,100,255,0.4); }"
        )

        # 重新翻译子菜单
        retranslate_menu = menu.addMenu(tr("history_retranslate"))
        for lang in RETARGET_LANGUAGES:
            action = QAction(lang, self)
            action.triggered.connect(lambda checked, l=lang: self._do_retranslate(l))
            retranslate_menu.addAction(action)

        menu.addSeparator()

        copy_orig = QAction(tr("history_copy_original"), self)
        copy_orig.triggered.connect(self._copy_original)
        menu.addAction(copy_orig)

        copy_trans = QAction(tr("history_copy_translate"), self)
        copy_trans.triggered.connect(self._copy_translate)
        menu.addAction(copy_trans)

        menu.addSeparator()

        resend = QAction(tr("history_resend_osc"), self)
        resend.triggered.connect(self._do_resend_osc)
        menu.addAction(resend)

        delete = QAction(tr("history_delete"), self)
        delete.triggered.connect(self._do_delete)
        menu.addAction(delete)

        menu.exec_(self.list_widget.mapToGlobal(pos))

    def _on_double_click(self, item):
        """双击：弹出语言选择快速重新翻译"""
        widget = self.list_widget.itemWidget(item)
        if not widget:
            return
        entry = widget.entry
        lang, ok = QInputDialog.getItem(
            self, tr("history_retranslate"),
            tr("target_lang"), RETARGET_LANGUAGES, 0, False
        )
        if ok and lang:
            self.retranslate_requested.emit(entry.id, lang)

    def _do_retranslate(self, target_lang: str):
        entry = self._selected_entry()
        if entry:
            self.retranslate_requested.emit(entry.id, target_lang)

    def _copy_original(self):
        entry = self._selected_entry()
        if entry and entry.original:
            QApplication.clipboard().setText(entry.original)

    def _copy_translate(self):
        entry = self._selected_entry()
        if entry and entry.translated:
            QApplication.clipboard().setText(entry.translated)

    def _do_resend_osc(self):
        entry = self._selected_entry()
        if entry:
            self.resend_osc_requested.emit(entry.id)

    def _do_delete(self):
        entry = self._selected_entry()
        if not entry:
            return
        self.entries = [e for e in self.entries if e.id != entry.id]
        self._remove_item_by_id(entry.id)
        self.delete_requested.emit(entry.id)
        if self.config.get("history_save_to_file", False):
            self._save_to_file()

    def _on_clear(self):
        self.clear_all()

    def _on_save_toggle(self, state):
        enabled = state == Qt.Checked
        self.config.set("history_save_to_file", enabled)
        if enabled:
            self._save_to_file()
        else:
            self._delete_file()

    # ---- 持久化 ----
    def _history_file_path(self):
        from config import get_config_dir
        return get_config_dir() / "history.jsonl"

    def _save_to_file(self):
        try:
            path = self._history_file_path()
            with open(path, "w", encoding="utf-8") as f:
                for entry in self.entries:
                    f.write(json.dumps({
                        "id": entry.id,
                        "timestamp": entry.timestamp,
                        "source": entry.source,
                        "original": entry.original,
                        "translated": entry.translated,
                        "original_lang": entry.original_lang,
                        "target_lang": entry.target_lang,
                    }, ensure_ascii=False) + "\n")
        except OSError as e:
            print(f"[History] 保存失败: {e}")

    def _load_from_file(self):
        try:
            path = self._history_file_path()
            if not path.exists():
                return
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entry = HistoryEntry(**data)
                        self.entries.append(entry)
                        if entry.id >= self._next_id:
                            self._next_id = entry.id + 1
                        self._append_item(entry)
                    except (json.JSONDecodeError, TypeError):
                        continue
            self._scroll_to_bottom()
        except OSError as e:
            print(f"[History] 加载失败: {e}")

    def _delete_file(self):
        try:
            path = self._history_file_path()
            if path.exists():
                path.unlink()
        except OSError:
            pass

    def eventFilter(self, obj, event):
        """事件过滤器：让标题栏可以拖动窗口"""
        if obj == self._drag_handle and not self.config.get("history_locked", False):
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._resize_mode = "move"
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                return True
            elif event.type() == QEvent.MouseMove and self._resize_mode == "move" and self._drag_pos:
                self.move(event.globalPos() - self._drag_pos)
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                self._resize_mode = None
                self._drag_pos = None
                return True
        return super().eventFilter(obj, event)

    # ---- 拖动 & 调整大小 ----
    def _hit_test(self, pos):
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        if x <= self._edge_margin:
            return "left"
        if x >= w - self._edge_margin:
            return "right"
        if y <= self._edge_margin:
            return "top"
        if y >= h - self._edge_margin:
            return "bottom"
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.config.get("history_locked", False):
            edge = self._hit_test(event.pos())
            if edge:
                self._resize_mode = edge
                self._drag_start_pos = event.globalPos()
                self._drag_start_geometry = self.geometry()
            else:
                self._resize_mode = "move"
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.config.get("history_locked", False):
            return
        if self._resize_mode == "move" and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        elif self._resize_mode and self._drag_start_pos:
            g = self._drag_start_geometry
            delta = event.globalPos() - self._drag_start_pos
            dx, dy = delta.x(), delta.y()
            new_x, new_y, new_w, new_h = g.x(), g.y(), g.width(), g.height()
            if self._resize_mode == "left":
                new_w = max(250, g.width() - dx)
                new_x = g.x() + (g.width() - new_w)
            elif self._resize_mode == "right":
                new_w = max(250, g.width() + dx)
            elif self._resize_mode == "top":
                new_h = max(150, g.height() - dy)
                new_y = g.y() + (g.height() - new_h)
            elif self._resize_mode == "bottom":
                new_h = max(150, g.height() + dy)
            self.setGeometry(new_x, new_y, new_w, new_h)
            event.accept()
        else:
            edge = self._hit_test(event.pos())
            cursors = {
                "left": Qt.SizeHorCursor, "right": Qt.SizeHorCursor,
                "top": Qt.SizeVerCursor, "bottom": Qt.SizeVerCursor,
            }
            self.setCursor(cursors.get(edge, Qt.ArrowCursor))

    def mouseReleaseEvent(self, event):
        if self._resize_mode:
            self.config.set("history_window_x", self.x())
            self.config.set("history_window_y", self.y())
            self.config.set("history_window_width", self.width())
            self.config.set("history_window_height", self.height())
        self._drag_pos = None
        self._resize_mode = None
        self._drag_start_pos = None
        self.setCursor(Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        """双击标题栏区域切换锁定"""
        if event.pos().y() < 30:
            locked = not self.config.get("history_locked", False)
            self.set_locked(locked)

    def closeEvent(self, event):
        self.config.set("history_visible", False)
        event.ignore()
        self.hide()
