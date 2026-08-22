"""
SteamVR 覆盖显示接口（预留）
- 在 VR 头显内叠加显示字幕
- 需要集成 OpenVR SDK (openvr Python 绑定)
- 当前版本为接口预留，实际功能需要安装 openvr 并实现 Overlay 渲染

依赖安装：
    pip install openvr

使用方式：
    from steamvr_overlay import SteamVROverlay
    overlay = SteamVROverlay()
    overlay.show()
    overlay.set_text("你好", "こんにちは")

注意事项：
    1. 需要 SteamVR 运行中
    2. 需要在 SteamVR 设置中允许第三方覆盖
    3. 覆盖层位置和大小可通过 set_anchor 调整
    4. 当前版本为基础框架，实际渲染需要根据 openvr API 实现
"""
import time
import threading

try:
    import openvr
    _OPENVR_AVAILABLE = True
except ImportError:
    _OPENVR_AVAILABLE = False


class SteamVROverlay:
    """
    SteamVR 覆盖层（预留接口）
    在 VR 头显内显示悬浮字幕
    """

    def __init__(self):
        self._overlay = None
        self._texture = None
        self._running = False
        self._thread = None
        self._original_text = ""
        self._translated_text = ""
        self._visible = False
        self._anchor_x = 0.0
        self._anchor_y = -0.5  # 默认在视野下方
        self._anchor_z = -1.0
        self._width = 1.5
        self._height = 0.3

    def is_available(self) -> bool:
        """检查 SteamVR 覆盖是否可用"""
        if not _OPENVR_AVAILABLE:
            return False
        try:
            # 检查 SteamVR 是否运行
            openvr.init(openvr.VRApplication_Overlay)
            openvr.shutdown()
            return True
        except Exception:
            return False

    def show(self) -> bool:
        """显示覆盖层"""
        if not self.is_available():
            print("[SteamVR] SteamVR 不可用，请确保 SteamVR 正在运行并安装 openvr 库")
            return False

        try:
            if self._overlay is None:
                # 初始化 OpenVR 覆盖应用
                openvr.init(openvr.VRApplication_Overlay)
                # 创建覆盖层
                self._overlay = openvr.IVROverlay()
                error = self._overlay.CreateOverlay("vrc_trans_subtitle", "VRChat 翻译字幕")
                if error != openvr.VROverlayError_None:
                    print(f"[SteamVR] 创建覆盖层失败: {error}")
                    return False

            # 设置覆盖层位置和大小
            self._update_anchor()
            self._overlay.ShowOverlay("vrc_trans_subtitle")
            self._visible = True

            # 启动渲染线程
            if not self._running:
                self._running = True
                self._thread = threading.Thread(target=self._render_loop, daemon=True)
                self._thread.start()

            print("[SteamVR] 覆盖层已显示")
            return True
        except Exception as e:
            print(f"[SteamVR] 显示覆盖层失败: {e}")
            return False

    def hide(self):
        """隐藏覆盖层"""
        try:
            if self._overlay is not None:
                self._overlay.HideOverlay("vrc_trans_subtitle")
            self._visible = False
            self._running = False
            print("[SteamVR] 覆盖层已隐藏")
        except Exception as e:
            print(f"[SteamVR] 隐藏覆盖层失败: {e}")

    def set_text(self, original: str = "", translated: str = ""):
        """设置字幕文本"""
        self._original_text = original
        self._translated_text = translated

    def set_anchor(self, x: float, y: float, z: float):
        """设置覆盖层锚点位置（相对于头显）"""
        self._anchor_x = x
        self._anchor_y = y
        self._anchor_z = z
        self._update_anchor()

    def set_size(self, width: float, height: float):
        """设置覆盖层大小（米）"""
        self._width = width
        self._height = height
        self._update_anchor()

    def _update_anchor(self):
        """更新覆盖层锚点"""
        if self._overlay is None:
            return
        try:
            # 设置覆盖层相对于头显的位置
            transform = openvr.HmdMatrix34_t()
            transform.m[0][0] = 1.0
            transform.m[1][1] = 1.0
            transform.m[2][2] = 1.0
            transform.m[0][3] = self._anchor_x
            transform.m[1][3] = self._anchor_y
            transform.m[2][3] = self._anchor_z

            self._overlay.SetOverlayTransformTrackedDeviceRelative(
                "vrc_trans_subtitle",
                openvr.k_unTrackedDeviceIndex_Hmd,
                transform
            )
            self._overlay.SetOverlayWidthInMeters("vrc_trans_subtitle", self._width)
        except Exception as e:
            print(f"[SteamVR] 更新锚点失败: {e}")

    def _render_loop(self):
        """渲染循环（需要根据 openvr API 实现实际的纹理渲染）"""
        while self._running:
            try:
                if self._visible and self._overlay is not None:
                    # TODO: 实现实际的纹理渲染
                    # 需要创建 OpenGL/DX 纹理，将字幕文本渲染到纹理上
                    # 然后调用 self._overlay.SetOverlayTexture(...)
                    # 当前为预留接口，实际渲染需要图形库支持
                    pass
                time.sleep(0.033)  # ~30 FPS
            except Exception as e:
                print(f"[SteamVR] 渲染循环错误: {e}")
                time.sleep(0.1)

    def shutdown(self):
        """关闭覆盖层并释放资源"""
        self.hide()
        try:
            if self._overlay is not None:
                self._overlay.DestroyOverlay("vrc_trans_subtitle")
                self._overlay = None
            openvr.shutdown()
        except Exception:
            pass


# 便捷全局实例
_overlay_instance = None


def get_overlay() -> SteamVROverlay:
    """获取全局覆盖层实例"""
    global _overlay_instance
    if _overlay_instance is None:
        _overlay_instance = SteamVROverlay()
    return _overlay_instance


if __name__ == "__main__":
    # 测试 SteamVR 覆盖可用性
    overlay = SteamVROverlay()
    if overlay.is_available():
        print("SteamVR 覆盖可用")
        overlay.show()
        overlay.set_text("测试原文", "测试翻译")
        print("按 Ctrl+C 退出...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            overlay.shutdown()
    else:
        print("SteamVR 覆盖不可用")
        print("请确保：")
        print("  1. 已安装 openvr: pip install openvr")
        print("  2. SteamVR 正在运行")
        print("  3. SteamVR 设置中允许第三方覆盖")
