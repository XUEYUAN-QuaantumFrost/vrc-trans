"""
OSC 发送模块
通过 OSC 协议将文字发送到 VRChat 聊天框
支持超长文本自动分段发送（VRChat 限制 144 字符）
"""
import time
import threading
from pythonosc import udp_client

# VRChat 聊天框字符限制
VRC_CHATBOX_LIMIT = 144
# 分段发送间隔（秒），避免过快被丢弃
CHUNK_INTERVAL = 0.6


class OSCSender:
    def __init__(self, ip="127.0.0.1", port=9000):
        self.ip = ip
        self.port = port
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            self._client = udp_client.SimpleUDPClient(self.ip, self.port)

    def update_endpoint(self, ip, port):
        self.ip = ip
        self.port = port
        self._client = None  # 重建

    def send_chatbox(self, text: str, send_immediately: bool = True):
        """
        发送文字到 VRChat 聊天框
        VRChat OSC 地址: /chatbox/input
        参数: text(str), send_immediately(bool)
        超过 144 字符自动分段发送
        """
        if not text or not text.strip():
            return
        text = text.strip()
        # 超长自动分段
        if len(text) > VRC_CHATBOX_LIMIT:
            self._send_chunked(text)
            return
        self._ensure_client()
        try:
            self._client.send_message(
                "/chatbox/input",
                [text, send_immediately]
            )
            return True
        except Exception as e:
            print(f"[OSC] 发送失败: {e}")
            return False

    def _send_chunked(self, text: str):
        """
        超长文本分段发送（在子线程中依次发送，避免阻塞主线程）
        按标点优先切分，没有标点则按字数硬切
        """
        chunks = self._split_text(text, VRC_CHATBOX_LIMIT)
        if not chunks:
            return

        def _worker():
            self._ensure_client()
            for i, chunk in enumerate(chunks):
                try:
                    # 最后一段立即发送，前面的也立即发送（VRChat 会依次显示）
                    self._client.send_message(
                        "/chatbox/input",
                        [chunk, True]
                    )
                except Exception as e:
                    print(f"[OSC] 分段 {i+1}/{len(chunks)} 发送失败: {e}")
                    break
                if i < len(chunks) - 1:
                    time.sleep(CHUNK_INTERVAL)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    @staticmethod
    def _split_text(text: str, max_len: int) -> list:
        """
        将文本切分为不超过 max_len 的片段
        优先在标点符号处切分，保持语义完整
        """
        if len(text) <= max_len:
            return [text]

        chunks = []
        # 优先切分的标点（按优先级排序）
        break_chars = ['\n', '。', '！', '？', '；', '.', '!', '?', ';', '，', ',', '、', ' ']

        remaining = text
        while len(remaining) > max_len:
            # 在 max_len 范围内找最后一个标点
            cut_pos = max_len
            found = False
            for ch in break_chars:
                pos = remaining.rfind(ch, 0, max_len)
                if pos > max_len // 2:  # 至少切一半以上，避免切太短
                    cut_pos = pos + 1  # 包含标点
                    found = True
                    break
            if not found:
                # 没有合适标点，硬切
                cut_pos = max_len
            chunks.append(remaining[:cut_pos].strip())
            remaining = remaining[cut_pos:].strip()

        if remaining:
            chunks.append(remaining)
        return chunks

    def send_typing(self, is_typing: bool):
        """发送打字状态"""
        self._ensure_client()
        try:
            self._client.send_message("/chatbox/typing", is_typing)
        except Exception as e:
            print(f"[OSC] 打字状态失败: {e}")
