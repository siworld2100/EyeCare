"""蒙版界面 - 全屏半透明遮罩层（休息和眨眼共用）

关键约束（均为重构中修复的实际缺陷）：
1. 多显示器：每个屏幕各建一个无边框窗口，避免只黑主屏。
2. 无闪屏：窗口先以 ``-alpha 0`` 创建，首帧绘制完成后才提到目标透明度。
3. 不抢输入：眨眼蒙版不获取焦点，也不响应 ESC，避免打断用户输入。
4. 跳过信号唯一：仅休息蒙版的上「跳过」按钮 / ESC 触发 ``on_skip``。
"""

import logging
import math
import tkinter as tk
from typing import Callable

from ..system.monitors import MonitorRect, get_monitors

logger = logging.getLogger(__name__)

_FONT_FAMILY = "Microsoft YaHei"
_FADE_STEP = 3          # 每步透明度增量
_FADE_MAX_MS = 300      # 单段渐变最长时长
_FRAME_MS = 20          # 渐变帧间隔


class Overlay:
    """全屏蒙版界面，支持透明度调节与多显示器覆盖"""

    def __init__(self, on_skip: Callable[[], None] | None = None):
        """
        Args:
            on_skip: 用户跳过休息的回调
        """
        self._on_skip = on_skip
        self._windows: list[tk.Toplevel] = []
        self._canvas: tk.Canvas | None = None
        self._skip_button: tk.Button | None = None
        self._countdown_label: tk.Label | None = None
        self._countdown = 0
        self._countdown_id: str | None = None
        self._fade_id: str | None = None
        self._is_showing = False
        self._phase = "idle"  # idle / fadeIn / hold / fadeOut

        # 眨眼渐变动画参数
        self._target_opacity = 0
        self._current_alpha = 0
        self._fade_delay_ms = _FRAME_MS
        self._hold_ms = 0

    @property
    def is_showing(self) -> bool:
        """蒙版是否正在显示"""
        return self._is_showing

    # ---- 对外接口 ----

    def show_rest(self, duration: int, opacity: int):
        """显示休息蒙版（带倒计时与跳过按钮）"""
        if self._is_showing:
            return
        self._is_showing = True
        self._countdown = max(0, int(duration))
        self._create_windows(opacity, show_controls=True, interactive=True)
        self._start_countdown()

    def show_blink(self, duration: float, opacity: int):
        """显示眨眼蒙版（渐变呼吸效果，不抢占输入）"""
        if self._is_showing:
            return
        self._is_showing = True
        self._target_opacity = max(0, min(100, int(opacity)))

        total_ms = max(1, int(duration * 1000))
        fade_ms = min(_FADE_MAX_MS, total_ms // 2)
        steps = max(1, math.ceil(max(self._target_opacity, 1) / _FADE_STEP))
        self._fade_delay_ms = max(1, fade_ms // steps)
        self._hold_ms = max(0, total_ms - 2 * fade_ms)

        self._create_windows(0, show_controls=False, interactive=False)
        self._phase = "fadeIn"
        self._current_alpha = 0
        self._animate_fade_in()

    def hide(self):
        """隐藏蒙版并复位动画状态"""
        self._is_showing = False
        self._phase = "idle"
        self._cancel_after()
        for window in self._windows:
            try:
                window.destroy()
            except tk.TclError:
                pass
        self._windows.clear()
        self._canvas = None
        self._skip_button = None
        self._countdown_label = None

    # ---- 窗口创建 ----

    def _create_windows(self, opacity: int, show_controls: bool, interactive: bool):
        owner = tk._default_root  # 与主事件循环共用解释器
        monitors = get_monitors(owner)
        if not monitors:
            monitors = [MonitorRect(0, 0, 1, 1)]

        for index, monitor in enumerate(monitors):
            window = tk.Toplevel(owner) if owner else tk.Toplevel()
            window.title("EyeCare_Overlay")
            window.overrideredirect(True)
            window.attributes("-topmost", True)
            # 先完全透明再显示，首帧就不会闪出纯黑
            window.attributes("-alpha", 0.0)
            window.configure(bg="black")
            window.geometry(monitor.geometry)

            canvas = tk.Canvas(
                window,
                width=monitor.width,
                height=monitor.height,
                bg="black",
                highlightthickness=0,
            )
            canvas.pack(fill=tk.BOTH, expand=True)

            # 控制元素只挂在主屏（第一块）上
            self._canvas = canvas if index == 0 else self._canvas
            if show_controls and index == 0:
                self._create_controls(canvas, monitor.width, monitor.height)

            if interactive:
                window.bind("<Escape>", lambda _event: self._on_skip_click())
                window.protocol("WM_DELETE_WINDOW", lambda: None)
            else:
                # 眨眼蒙版：不抢焦点、不接受交互
                window.attributes("-disabled", True)

            self._windows.append(window)

        self._present(opacity, interactive)

    def _present(self, opacity: int, interactive: bool):
        """首帧绘制完成后再提升透明度并置顶，避免黑屏闪烁。"""
        if not self._windows:
            return
        primary = self._windows[0]
        try:
            primary.update_idletasks()
            self._apply_alpha(opacity)
            if interactive:
                primary.focus_force()
        except tk.TclError as exc:
            logger.debug("蒙版窗口初始化异常: %s", exc)

    def _create_controls(self, canvas: tk.Canvas, screen_w: int, screen_h: int):
        """创建休息模式的控制元素（右下角倒计时和跳过按钮）"""
        container = tk.Frame(canvas, bg="black")
        canvas.create_window(screen_w - 20, screen_h - 20, anchor=tk.SE, window=container)

        self._countdown_label = tk.Label(
            container,
            text=str(self._countdown),
            font=(_FONT_FAMILY, 24, "bold"),
            fg="white",
            bg="black",
        )
        self._countdown_label.pack(pady=(0, 10))

        self._skip_button = tk.Button(
            container,
            text="跳过",
            font=(_FONT_FAMILY, 12),
            fg="white",
            bg="#444444",
            activeforeground="white",
            activebackground="#666666",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=self._on_skip_click,
        )
        self._skip_button.pack()

    # ---- 透明度与动画 ----

    def _apply_alpha(self, alpha_percent: float):
        alpha = max(0.0, min(1.0, alpha_percent / 100.0))
        for window in self._windows:
            try:
                window.attributes("-alpha", alpha)
            except tk.TclError as exc:
                logger.debug("设置透明度失败: %s", exc)

    def _animate_fade_in(self):
        if self._phase != "fadeIn":
            return
        self._current_alpha = min(self._target_opacity, self._current_alpha + _FADE_STEP)
        self._apply_alpha(self._current_alpha)
        if self._current_alpha >= self._target_opacity:
            self._phase = "hold"
            self._fade_id = self._after(self._hold_ms, self._start_fade_out)
        else:
            self._fade_id = self._after(self._fade_delay_ms, self._animate_fade_in)

    def _start_fade_out(self):
        if self._phase != "hold":
            return
        self._phase = "fadeOut"
        self._animate_fade_out()

    def _animate_fade_out(self):
        if self._phase != "fadeOut":
            return
        self._current_alpha -= _FADE_STEP
        if self._current_alpha <= 0:
            self.hide()
            return
        self._apply_alpha(self._current_alpha)
        self._fade_id = self._after(self._fade_delay_ms, self._animate_fade_out)

    # ---- 定时器辅助 ----

    def _after(self, ms: int, func: Callable) -> str | None:
        """在任意一个存活窗口上排定时器（窗口销毁后定时器随之失效）。"""
        if not self._windows:
            return None
        try:
            return self._windows[0].after(max(0, int(ms)), func)
        except tk.TclError:
            return None

    def _cancel_after(self):
        for attr in ("_countdown_id", "_fade_id"):
            timer_id = getattr(self, attr)
            if timer_id is None:
                continue
            for window in self._windows:
                try:
                    window.after_cancel(timer_id)
                    break
                except tk.TclError:
                    continue
            setattr(self, attr, None)

    # ---- 休息倒计时 ----

    def _start_countdown(self):
        if not self._windows:
            return
        if self._countdown <= 0:
            self._on_skip_click()
            return

        if self._countdown_label and self._countdown_label.winfo_exists():
            self._countdown_label.config(text=str(self._countdown))
        self._countdown -= 1
        self._countdown_id = self._after(1000, self._start_countdown)

    def _on_skip_click(self):
        """跳过休息：清理定时器 -> 通知上层 -> 关闭窗口"""
        self._cancel_after()
        if self._on_skip:
            self._on_skip()
        self.hide()
