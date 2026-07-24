"""蒙版界面 - 全屏半透明遮罩层（休息和眨眼共用）

所有操作在主线程中执行，与 tkinter 事件循环集成。
"""

import logging
import tkinter as tk
from typing import Callable

logger = logging.getLogger(__name__)


class Overlay:
    """全屏蒙版界面，支持透明度调节"""

    def __init__(self, on_skip: Callable = None):
        """
        初始化蒙版
        Args:
            on_skip: 用户点击"跳过"按钮的回调
        """
        self._on_skip = on_skip
        self._root: tk.Toplevel = None
        self._canvas: tk.Canvas = None
        self._skip_button: tk.Button = None
        self._countdown_label: tk.Label = None
        self._countdown = 0
        self._countdown_id = None
        self._is_showing = False
        self._fade_id = None  # 渐变动画 ID
        self._blink_phase = "idle"  # idle, fadeIn, hold, fadeOut

    @property
    def is_showing(self) -> bool:
        """蒙版是否正在显示"""
        return self._is_showing

    def show_rest(self, duration: int, opacity: int):
        """显示休息蒙版"""
        if self._is_showing:
            return
        self._is_showing = True
        self._countdown = duration
        self._create_window(opacity, show_controls=True)
        self._start_countdown()

    def show_blink(self, duration: float, opacity: int):
        """显示眨眼蒙版（渐变呼吸灯效果）"""
        if self._is_showing:
            return
        self._is_showing = True
        self._blink_target_opacity = opacity
        self._blink_duration = duration
        # 创建窗口，初始透明度为0
        self._create_window(0, show_controls=False)
        # 开始渐入动画
        self._blink_phase = "fadeIn"
        self._blink_current_alpha = 0
        self._blink_fade_step = 3  # 每步增加的透明度
        self._blink_fade_delay = 20  # 每步间隔（毫秒）
        self._animate_fade_in()

    def _animate_fade_in(self):
        """渐入动画"""
        if self._blink_phase != "fadeIn":
            return

        self._blink_current_alpha += self._blink_fade_step
        if self._blink_current_alpha >= self._blink_target_opacity:
            # 渐入完成，进入保持阶段
            self._blink_current_alpha = self._blink_target_opacity
            self._set_alpha(self._blink_current_alpha)
            self._blink_phase = "hold"
            # 保持一段时间后渐出
            hold_time = int(self._blink_duration * 1000)
            self._fade_id = self._root.after(hold_time, self._start_fade_out)
        else:
            self._set_alpha(self._blink_current_alpha)
            self._fade_id = self._root.after(self._blink_fade_delay, self._animate_fade_in)

    def _start_fade_out(self):
        """开始渐出动画"""
        if self._blink_phase != "hold":
            return
        self._blink_phase = "fadeOut"
        self._animate_fade_out()

    def _animate_fade_out(self):
        """渐出动画"""
        if self._blink_phase != "fadeOut":
            return

        self._blink_current_alpha -= self._blink_fade_step
        if self._blink_current_alpha <= 0:
            # 渐出完成，隐藏蒙版
            self._blink_current_alpha = 0
            self.hide()
        else:
            self._set_alpha(self._blink_current_alpha)
            self._fade_id = self._root.after(self._blink_fade_delay, self._animate_fade_out)

    def _set_alpha(self, alpha_percent: int):
        """设置窗口透明度"""
        try:
            if self._root:
                alpha = alpha_percent / 100.0
                alpha = max(0.0, min(1.0, alpha))
                self._root.attributes("-alpha", alpha)
        except Exception as e:
            logger.debug("设置透明度失败: %s", e)

    def hide(self):
        """隐藏蒙版"""
        self._is_showing = False
        self._blink_phase = "idle"
        self._force_hide()

    def _create_window(self, opacity: int, show_controls: bool):
        """创建全屏蒙版窗口"""
        self._root = tk.Toplevel()
        self._root.title("EyeCare_Overlay")
        self._root.overrideredirect(True)          # 无标题栏
        self._root.attributes("-topmost", True)    # 始终置顶

        # 全屏
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        self._root.geometry(f"{screen_w}x{screen_h}+0+0")

        # 黑色背景
        self._root.configure(bg="black")

        # 创建画布
        self._canvas = tk.Canvas(
            self._root, width=screen_w, height=screen_h,
            bg="black", highlightthickness=0
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        if show_controls:
            self._create_controls(screen_w, screen_h)

        # 强制更新窗口
        self._root.update_idletasks()
        self._root.update()

        # 设置窗口透明度
        self._set_window_opacity(opacity)

        # 绑定 ESC 键跳过
        self._root.bind("<Escape>", lambda e: self._on_skip_click())
        # 禁止关闭窗口（防止 Alt+F4）
        self._root.protocol("WM_DELETE_WINDOW", lambda: None)

    def _create_controls(self, screen_w: int, screen_h: int):
        """创建休息模式的控制元素（右下角倒计时和跳过按钮）"""
        # 控制容器 - 右下角
        ctrl_frame = tk.Frame(self._canvas, bg="black")
        self._canvas.create_window(
            screen_w - 20, screen_h - 20,
            anchor=tk.SE, window=ctrl_frame
        )

        # 倒计时文字
        self._countdown_label = tk.Label(
            ctrl_frame, text=f"{self._countdown}",
            font=("Microsoft YaHei", 24, "bold"),
            fg="white", bg="black"
        )
        self._countdown_label.pack(pady=(0, 10))

        # 跳过按钮
        self._skip_button = tk.Button(
            ctrl_frame, text="跳过",
            font=("Microsoft YaHei", 12),
            fg="white", bg="#444444",
            activeforeground="white", activebackground="#666666",
            relief=tk.FLAT, padx=20, pady=8,
            command=self._on_skip_click
        )
        self._skip_button.pack()

    def _set_window_opacity(self, opacity_percent: int):
        """设置窗口透明度"""
        try:
            # 使用 tkinter 内置的 -alpha 属性
            # 0 = 完全透明, 1 = 完全不透明
            alpha = opacity_percent / 100.0
            alpha = max(0.0, min(1.0, alpha))
            self._root.attributes("-alpha", alpha)
            logger.debug("窗口透明度设置为 %d%% (alpha=%.2f)", opacity_percent, alpha)
        except Exception as e:
            logger.warning("设置窗口透明度失败: %s", e)

    def _start_countdown(self):
        """启动倒计时"""
        if self._countdown > 0 and self._countdown_label and self._countdown_label.winfo_exists():
            self._countdown_label.config(text=f"{self._countdown}")
            self._countdown -= 1
            self._countdown_id = self._root.after(1000, self._start_countdown)
        else:
            # 倒计时结束，自动关闭
            self._on_skip_click()

    def _on_skip_click(self):
        """跳过按钮点击"""
        if self._countdown_id and self._root:
            self._root.after_cancel(self._countdown_id)
            self._countdown_id = None
        if self._on_skip:
            self._on_skip()
        self.hide()

    def _force_hide(self):
        """强制隐藏蒙版"""
        try:
            if self._countdown_id and self._root:
                self._root.after_cancel(self._countdown_id)
                self._countdown_id = None
            if self._fade_id and self._root:
                self._root.after_cancel(self._fade_id)
                self._fade_id = None
            if self._root:
                self._root.destroy()
                self._root = None
            self._canvas = None
            self._skip_button = None
            self._countdown_label = None
        except Exception as e:
            logger.debug("隐藏蒙版时出错: %s", e)
