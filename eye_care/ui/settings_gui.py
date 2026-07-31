"""Settings window for EyeCare."""

import math
import os
import sys
import tkinter as tk
from tkinter import ttk
from typing import Callable


def _get_base_path():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


_ICON_PATH = os.path.join(_get_base_path(), "eye_care.ico")


class MessageDialog:
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
        heading = "输入有误" if msg_type == "error" else "设置已保存"
        ttk.Label(frame, text=heading, font=("Microsoft YaHei", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text=message, font=("Microsoft YaHei", 10), wraplength=300).pack(pady=(0, 15))
        ttk.Button(frame, text="确定", command=self._on_ok, width=10).pack()
        self.dialog.bind("<Return>", lambda event: self._on_ok())
        self.dialog.bind("<Escape>", lambda event: self._on_ok())
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
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
    """Settings UI retaining the original four-section layout."""

    def __init__(self, on_save: Callable = None):
        self._on_save = on_save
        self._root: tk.Toplevel | None = None
        self._entries = {}
        self._color_previews = {}

    def show(self, settings: dict, master: tk.Tk = None):
        if self._root and self._root.winfo_exists():
            self._root.lift()
            self._root.focus_force()
            return

        self._root = tk.Toplevel(master) if master else tk.Toplevel()
        self._root.title("护眼程序 - 设置")
        self._root.configure(bg="#F5F7FB")
        self._root.resizable(True, False)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)
        if os.path.exists(_ICON_PATH):
            self._root.iconbitmap(_ICON_PATH)
        self._root.attributes("-topmost", True)
        self._configure_styles()

        # Original structure: rest settings, blink settings, system settings, then actions.
        rest_frame = ttk.LabelFrame(self._root, text="休息设置", style="Settings.TLabelframe", padding=12)
        rest_frame.pack(fill=tk.X, padx=16, pady=(16, 6))
        rest_left = ttk.Frame(rest_frame, style="Page.TFrame")
        rest_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._add_field(rest_left, "休息间隔（分钟）", "rest_interval", settings.get("rest_interval", 20), 0)
        self._add_field(rest_left, "休息时长（秒）", "rest_duration", settings.get("rest_duration", 20), 1)
        self._add_slider(rest_left, "不透明度（%）", "rest_opacity", settings.get("rest_opacity", 70), 2)
        self._add_preview(rest_frame, "rest_opacity", settings.get("rest_opacity", 70))

        blink_frame = ttk.LabelFrame(self._root, text="眨眼设置", style="Settings.TLabelframe", padding=12)
        blink_frame.pack(fill=tk.X, padx=16, pady=6)
        blink_left = ttk.Frame(blink_frame, style="Page.TFrame")
        blink_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._add_field(blink_left, "提醒间隔（秒）", "blink_interval", settings.get("blink_interval", 45), 0)
        self._add_field(blink_left, "显示时长（秒）", "blink_duration", settings.get("blink_duration", 2.0), 1)
        self._add_slider(blink_left, "不透明度（%）", "blink_opacity", settings.get("blink_opacity", 100), 2)
        self._add_preview(blink_frame, "blink_opacity", settings.get("blink_opacity", 100))

        sys_frame = ttk.LabelFrame(self._root, text="系统设置", style="Settings.TLabelframe", padding=10)
        sys_frame.pack(fill=tk.X, padx=16, pady=(6, 10))
        self._paused_var = tk.BooleanVar(value=settings.get("paused", False))
        ttk.Checkbutton(sys_frame, text="暂停所有提醒（开会时使用）", variable=self._paused_var).pack(anchor=tk.W, pady=2)
        self._autostart_var = tk.BooleanVar(value=settings.get("autostart", False))
        ttk.Checkbutton(sys_frame, text="开机自动启动", variable=self._autostart_var).pack(anchor=tk.W, pady=2)

        # Pack the footer at the bottom so it remains available on smaller screens.
        btn_frame = ttk.Frame(self._root, style="Page.TFrame", padding=(16, 4, 16, 14))
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btn_frame, text="取消", command=self._on_close, width=10).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btn_frame, text="保存", command=self._on_save_click, width=10).pack(side=tk.RIGHT)

        self._fit_to_screen()

    def _configure_styles(self):
        style = ttk.Style(self._root)
        style.configure("Page.TFrame", background="#F5F7FB")
        style.configure("Settings.TLabelframe", background="#F5F7FB")
        style.configure("Settings.TLabelframe.Label", background="#F5F7FB", foreground="#1D3557", font=("Microsoft YaHei", 10, "bold"))

    def _fit_to_screen(self):
        self._root.update_idletasks()
        screen_w, screen_h = self._root.winfo_screenwidth(), self._root.winfo_screenheight()
        width = min(max(520, self._root.winfo_reqwidth()), max(360, screen_w - 80))
        height = min(max(450, self._root.winfo_reqheight()), max(300, screen_h - 80))
        self._root.minsize(min(440, width), min(300, height))
        x = (screen_w - width) // 2
        y = max(20, (screen_h - height) // 2)
        self._root.geometry(f"{width}x{height}+{x}+{y}")

    def _add_preview(self, parent, key: str, value: int):
        preview = tk.Canvas(parent, width=100, height=80, highlightthickness=1, highlightbackground="#D8E1EE", bg="#FFFFFF")
        preview.pack(side=tk.RIGHT, padx=(12, 0))
        self._color_previews[key] = preview
        self._update_color_preview(key, value)

    def _add_field(self, parent, label: str, key: str, default, row: int):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=5)
        entry = ttk.Entry(parent, width=15)
        entry.insert(0, str(default))
        entry.grid(row=row, column=1, sticky=tk.E, pady=5, padx=(12, 0))
        self._entries[key] = entry

    def _add_slider(self, parent, label: str, key: str, default: int, row: int):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=5)
        value_var = tk.IntVar(value=default)
        slider = ttk.Scale(parent, from_=0, to=100, variable=value_var, orient=tk.HORIZONTAL, length=110)
        slider.grid(row=row, column=1, sticky=tk.E, pady=5, padx=(12, 0))
        ttk.Label(parent, textvariable=value_var, width=4).grid(row=row, column=2, padx=(8, 0), pady=5)
        value_var.trace_add("write", lambda *_: self._update_color_preview(key, value_var.get()))
        self._entries[key] = value_var

    def _update_color_preview(self, key: str, value: int):
        canvas = self._color_previews.get(key)
        if not canvas:
            return
        gray = int(255 - (value / 100) * 255)
        color = f"#{gray:02x}{gray:02x}{gray:02x}"
        canvas.delete("all")
        canvas.create_rectangle(0, 0, 100, 80, fill=color, outline="")
        canvas.create_text(50, 40, text=f"{value}%", fill="#FFFFFF" if value > 55 else "#334155", font=("Microsoft YaHei", 10, "bold"))

    def _get_value(self, key: str, is_float: bool = False):
        widget = self._entries.get(key)
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
            settings["rest_interval"] = max(1, settings["rest_interval"])
            settings["rest_duration"] = max(5, settings["rest_duration"])
            settings["blink_interval"] = max(10, settings["blink_interval"])
            settings["blink_duration"] = max(0.5, settings["blink_duration"])
            if not math.isfinite(settings["blink_duration"]):
                raise ValueError("显示时长必须是有限数字")
            if self._on_save:
                self._on_save(settings)
            show_info(self._root, "设置已保存", "新的提醒设置已立即生效。")
            self._on_close()
        except (ValueError, TypeError) as error:
            show_error(self._root, "输入有误", f"请输入有效的数字。\n{error}")

    def _on_close(self):
        if self._root:
            self._root.destroy()
            self._root = None

    def destroy(self):
        self._on_close()
