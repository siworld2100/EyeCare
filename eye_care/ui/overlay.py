"""蒙版界面 - 全屏半透明遮罩层（休息和眨眼共用）"""

import logging
import threading
import tkinter as tk
from typing import Callable

logger = logging.getLogger(__name__)

# Windows API 常量
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
LWA_ALPHA = 0x2


class Overlay:
    """全屏蒙版界面，支持透明度调节"""

    def __init__(self, on_skip: Callable = None):
        """
        初始化蒙版
        Args:
            on_skip: 用户点击"跳过"按钮的回调
        """
        self._on_skip = on_skip
        self._root: tk.Tk = None
        self._canvas: tk.Canvas = None
        self._skip_button: tk.Button = None
        self._countdown_label: tk.Label = None
        self._countdown = 0
        self._countdown_id = None
        self._is_rest_mode = False
        self._lock = threading.Lock()

    def show_rest(self, duration: int, opacity: int):
        """显示休息蒙版"""
        with self._lock:
            if self._root and self._root.winfo_exists():
                return
        self._is_rest_mode = True
        self._countdown = duration
        self._create_window(opacity, show_controls=True)
        self._start_countdown()

    def show_blink(self, duration: float, opacity: int):
        """显示眨眼蒙版"""
        with self._lock:
            if self._root and self._root.winfo_exists():
                return
        self._is_rest_mode = False
        self._create_window(opacity, show_controls=False)
        # 定时自动关闭
        self._root.after(int(duration * 1000), self._force_hide)

    def hide(self, duration: int = 0, opacity: int = 0):
        """隐藏蒙版"""
        self._force_hide()

    def _create_window(self, opacity: int, show_controls: bool):
        """创建全屏蒙版窗口"""
        self._root = tk.Tk()
        self._root.title("EyeCare")
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

        # 设置窗口透明度（Windows）
        self._set_window_opacity(opacity)

        # 绑定 ESC 键跳过
        self._root.bind("<Escape>", lambda e: self._on_skip_click())
        # 禁止关闭窗口（防止 Alt+F4）
        self._root.protocol("WM_DELETE_WINDOW", lambda: None)

        self._root.update()

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
        """设置窗口透明度（Windows API）"""
        try:
            import ctypes
            from ctypes import windll

            # 等待窗口句柄可用
            self._root.update()
            hwnd = windll.user32.GetForegroundWindow()

            # 设置分层窗口样式
            ex_style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)

            # 映射 0-100 到 0-255
            alpha = int(opacity_percent * 255 / 100)
            alpha = max(0, min(255, alpha))
            windll.user32.SetLayeredWindowAttributes(hwnd, 0, alpha, LWA_ALPHA)
            logger.debug("窗口透明度设置为 %d%% (alpha=%d)", opacity_percent, alpha)
        except Exception as e:
            logger.warning("设置窗口透明度失败: %s", e)

    def _start_countdown(self):
        """启动倒计时"""
        if self._countdown > 0 and self._countdown_label and self._countdown_label.winfo_exists():
            self._countdown_label.config(text=f"{self._countdown}")
            self._countdown -= 1
            self._countdown_id = self._root.after(1000, self._start_countdown)
        else:
            # 倒计时结束，自动关闭（休息时间到）
            self._on_skip_click()

    def _on_skip_click(self):
        """跳过按钮点击"""
        if self._countdown_id and self._root:
            self._root.after_cancel(self._countdown_id)
            self._countdown_id = None
        if self._on_skip:
            self._on_skip()
        self._force_hide()

    def _force_hide(self):
        """强制隐藏蒙版"""
        try:
            if self._countdown_id and self._root:
                self._root.after_cancel(self._countdown_id)
                self._countdown_id = None
            if self._root:
                self._root.destroy()
                self._root = None
            self._canvas = None
            self._skip_button = None
            self._countdown_label = None
        except Exception as e:
            logger.debug("隐藏蒙版时出错: %s", e)
