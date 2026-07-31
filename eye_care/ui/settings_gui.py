"""设置界面 - 配置休息/眨眼参数和系统选项"""

import os
import sys
import logging
import math
import tkinter as tk
from tkinter import ttk
from typing import Callable

logger = logging.getLogger(__name__)


def _get_base_path():
    """获取基础路径（兼容打包后）"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


_ICON_PATH = os.path.join(_get_base_path(), "eye_care.ico")


class MessageDialog:
    """自定义消息对话框，跟随父窗口显示"""

    def __init__(self, parent, title, message, msg_type="info"):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        if os.path.exists(_ICON_PATH):
            self.dialog.iconbitmap(_ICON_PATH)

        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        icon_text = "错误" if msg_type == "error" else "成功"
        ttk.Label(frame, text=icon_text, font=("Microsoft YaHei", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text=message, font=("Microsoft YaHei", 10), wraplength=300).pack(pady=(0, 15))
        ttk.Button(frame, text="确定", command=self._on_ok, width=10).pack()

        self.dialog.bind("<Return>", lambda e: self._on_ok())
        self.dialog.bind("<Escape>", lambda e: self._on_ok())

        self.dialog.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        dw = self.dialog.winfo_width()
        dh = self.dialog.winfo_height()
        self.dialog.geometry(f"+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")

        self.dialog.lift()
        self.dialog.focus_force()

    def _on_ok(self):
        self.result = "ok"
        self.dialog.destroy()

    def show(self):
        self.dialog.wait_window()
        return self.result


def show_info(parent, title, message):
    return MessageDialog(parent, title, message, "info").show()


def show_error(parent, title, message):
    return MessageDialog(parent, title, message, "error").show()


class SettingsGUI:
    """设置界面"""

    def __init__(self, on_save: Callable = None):
        self._on_save = on_save
        self._root: tk.Toplevel = None
        self._entries = {}
        self._color_previews = {}

    def show(self, settings: dict, master: tk.Tk = None):
        if self._root and self._root.winfo_exists():
            self._root.lift()
            self._root.focus_force()
            return

        self._root = tk.Toplevel(master) if master else tk.Toplevel()
        self._root.title("护眼程序 - 设置")
        self._root.resizable(False, False)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        if os.path.exists(_ICON_PATH):
            self._root.iconbitmap(_ICON_PATH)

        self._root.attributes("-topmost", True)
        self._root.update_idletasks()

        w, h = 520, 450
        x = (self._root.winfo_screenwidth() - w) // 2
        y = (self._root.winfo_screenheight() - h) // 2
        self._root.geometry(f"{w}x{h}+{x}+{y}")

        # ---- 休息设置 ----
        rest_frame = ttk.LabelFrame(self._root, text="休息设置", padding=10)
        rest_frame.pack(fill=tk.X, padx=15, pady=(15, 5))

        # 左侧：输入框和滑块
        rest_left = tk.Frame(rest_frame)
        rest_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._add_field(rest_left, "休息间隔（分钟）", "rest_interval", settings.get("rest_interval", 20), 0)
        self._add_field(rest_left, "休息时长（秒）", "rest_duration", settings.get("rest_duration", 20), 1)
        self._add_slider(rest_left, "不透明度（%）", "rest_opacity", settings.get("rest_opacity", 70), 2)

        # 右侧：颜色预览
        rest_preview = tk.Canvas(rest_frame, width=100, height=80, highlightthickness=1, highlightbackground="#cccccc")
        rest_preview.pack(side=tk.RIGHT, padx=(10, 0))
        self._color_previews["rest_opacity"] = rest_preview
        self._update_color_preview("rest_opacity", settings.get("rest_opacity", 70))

        # ---- 眨眼设置 ----
        blink_frame = ttk.LabelFrame(self._root, text="眨眼设置", padding=10)
        blink_frame.pack(fill=tk.X, padx=15, pady=5)

        # 左侧：输入框和滑块
        blink_left = tk.Frame(blink_frame)
        blink_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._add_field(blink_left, "提醒间隔（秒）", "blink_interval", settings.get("blink_interval", 45), 0)
        self._add_field(blink_left, "显示时长（秒）", "blink_duration", settings.get("blink_duration", 2.0), 1)
        self._add_slider(blink_left, "不透明度（%）", "blink_opacity", settings.get("blink_opacity", 100), 2)

        # 右侧：颜色预览
        blink_preview = tk.Canvas(blink_frame, width=100, height=80, highlightthickness=1, highlightbackground="#cccccc")
        blink_preview.pack(side=tk.RIGHT, padx=(10, 0))
        self._color_previews["blink_opacity"] = blink_preview
        self._update_color_preview("blink_opacity", settings.get("blink_opacity", 100))

        # ---- 系统设置 ----
        sys_frame = ttk.LabelFrame(self._root, text="系统设置", padding=10)
        sys_frame.pack(fill=tk.X, padx=15, pady=(5, 10))

        self._paused_var = tk.BooleanVar(value=settings.get("paused", False))
        ttk.Checkbutton(sys_frame, text="暂停所有提醒（开会时使用）", variable=self._paused_var).pack(anchor=tk.W, pady=2)

        self._autostart_var = tk.BooleanVar(value=settings.get("autostart", False))
        ttk.Checkbutton(sys_frame, text="开机自启动", variable=self._autostart_var).pack(anchor=tk.W, pady=2)

        # ---- 按钮 ----
        btn_frame = tk.Frame(self._root)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        ttk.Button(btn_frame, text="取消", command=self._on_close).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="保存", command=self._on_save_click).pack(side=tk.RIGHT)

    def _add_field(self, parent, label: str, key: str, default, row: int):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)
        entry = ttk.Entry(parent, width=15)
        entry.insert(0, str(default))
        entry.grid(row=row, column=1, sticky=tk.E, pady=4, padx=(10, 0))
        self._entries[key] = entry

    def _add_slider(self, parent, label: str, key: str, default: int, row: int):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)

        value_var = tk.IntVar(value=default)

        ttk.Label(parent, textvariable=value_var, width=4).grid(row=row, column=2, padx=(10, 0), pady=4)

        slider = ttk.Scale(parent, from_=0, to=100, variable=value_var, orient=tk.HORIZONTAL, length=100)
        slider.grid(row=row, column=1, sticky=tk.E, pady=4, padx=(10, 0))

        # 监听滑块值变化
        def on_value_change(*args):
            self._update_color_preview(key, value_var.get())

        value_var.trace_add("write", on_value_change)
        self._entries[key] = value_var

    def _update_color_preview(self, key: str, value: int):
        canvas = self._color_previews.get(key)
        if not canvas:
            return
        # 0=白色（透明），100=黑色（不透明）
        gray = int(255 - (value / 100) * 255)
        color = f"#{gray:02x}{gray:02x}{gray:02x}"
        canvas.delete("all")
        canvas.create_rectangle(0, 0, 100, 80, fill=color, outline="")

    def _get_value(self, key: str, is_float: bool = False):
        widget = self._entries.get(key)
        if widget is None:
            return None
        if isinstance(widget, tk.IntVar):
            return widget.get()
        text = widget.get().strip()
        return float(text) if is_float else int(text)

    def _on_save_click(self):
        try:
            settings = {
                "rest_interval": self._get_value("rest_interval"),
                "rest_duration": self._get_value("rest_duration"),
                "rest_opacity": self._get_value("rest_opacity"),
                "blink_interval": self._get_value("blink_interval"),
                "blink_duration": self._get_value("blink_duration", is_float=True),
                "blink_opacity": self._get_value("blink_opacity"),
                "autostart": self._autostart_var.get(),
                "paused": self._paused_var.get(),
            }
            if settings["rest_interval"] < 1:
                settings["rest_interval"] = 1
            if settings["rest_duration"] < 5:
                settings["rest_duration"] = 5
            if settings["blink_interval"] < 10:
                settings["blink_interval"] = 10
            if settings["blink_duration"] < 0.5:
                settings["blink_duration"] = 0.5
            if not math.isfinite(settings["blink_duration"]):
                raise ValueError("显示时长必须是有限数字")

            if self._on_save:
                self._on_save(settings)
            show_info(self._root, "成功", "设置已保存")
            self._on_close()
        except (ValueError, TypeError) as e:
            show_error(self._root, "输入错误", f"请输入有效的数字：\n{e}")

    def _on_close(self):
        if self._root:
            self._root.destroy()
            self._root = None

    def destroy(self):
        self._on_close()
