"""Settings window for EyeCare."""

import ctypes
import math
import sys
import tkinter as tk
from tkinter import ttk
from typing import Callable

from PIL import Image, ImageTk

from ..config.settings import NUMERIC_LIMITS
from ..paths import resource_path
from .icons import ico_path

_FONT = "Microsoft YaHei"

_REWARD_CODE_PATH = resource_path("eye_care", "assets", "reward_code.png")
_USAGE_TEXT_PATH = resource_path("eye_care", "assets", "usage.txt")


def _apply_window_icon(window: tk.Misc) -> None:
    """统一设置窗口图标（ico 缺失时跳过，不影响窗口创建）。"""
    path = ico_path()
    if not path:
        return
    try:
        window.iconbitmap(path)
    except tk.TclError:
        pass


class MessageDialog:
    def __init__(self, parent, title, message, msg_type="info"):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        _apply_window_icon(self.dialog)

        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        heading = "输入有误" if msg_type == "error" else "设置已保存"
        ttk.Label(frame, text=heading, font=(_FONT, 14, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text=message, font=(_FONT, 10), wraplength=300).pack(pady=(0, 15))
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


class UsageDialog:
    """A concise usage guide with an optional reward-code reveal."""

    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("护眼程序 - 使用说明")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        _apply_window_icon(self.dialog)

        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="护眼程序", font=(_FONT, 15, "bold")).pack()
        ttk.Label(frame, text="程序说明", font=(_FONT, 10)).pack(pady=(4, 12))
        self._add_program_description(frame)
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(16, 12))

        reward_area = ttk.Frame(frame)
        reward_area.pack(fill=tk.X)
        # 左侧：提示文案 + 赞赏码（点击按钮显示/收起）
        reward_text = ttk.Frame(reward_area)
        reward_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(
            reward_text,
            text="如有帮助到你，请我喝一杯咖啡，",
            font=(_FONT, 10),
            foreground="#374151",
        ).pack(anchor=tk.W)
        ttk.Label(
            reward_text,
            text="支持我更好的创作",
            font=(_FONT, 10),
            foreground="#374151",
        ).pack(anchor=tk.W, pady=(2, 10))
        self._qr_label = ttk.Label(reward_text)
        self._qr_label.pack(anchor=tk.W)

        right_area = ttk.Frame(reward_area)
        right_area.pack(side=tk.RIGHT, anchor=tk.N)
        ttk.Label(right_area, text="开发者：龙华", font=(_FONT, 9)).pack(anchor=tk.E, pady=(2, 16))
        self._reward_button = ttk.Button(right_area, text="赞赏作者", width=14, command=self._show_reward_code)
        self._reward_button.pack(anchor=tk.E)

        self.dialog.bind("<Escape>", lambda event: self.dialog.destroy())
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        self.dialog.lift()
        self.dialog.focus_force()
        self._reward_photo = None

    @staticmethod
    def _add_program_description(parent):
        """Render the independently maintained plain-text program description."""
        try:
            with open(_USAGE_TEXT_PATH, "r", encoding="utf-8") as source:
                content = source.read()
        except OSError:
            content = "程序说明文件暂时不可用。"
        description = tk.Text(
            parent,
            width=50,
            height=15,
            wrap=tk.CHAR,
            relief=tk.FLAT,
            borderwidth=0,
            background="#F5F7FB",
            foreground="#1F2937",
            font=(_FONT, 10),
            padx=2,
            pady=2,
        )
        description.insert("1.0", content)
        description.configure(state=tk.DISABLED)
        description.yview_moveto(0)
        description.pack(fill=tk.X, expand=False)

    def _show_reward_code(self):
        if self._reward_photo is not None:
            self._qr_label.configure(image="")
            self._reward_photo = None
            self._reward_button.configure(text="赞赏作者")
            return
        try:
            with Image.open(_REWARD_CODE_PATH) as source:
                image = source.convert("RGBA")
                image.thumbnail((220, 220), Image.LANCZOS)
                self._reward_photo = ImageTk.PhotoImage(image)
            self._qr_label.configure(image=self._reward_photo)
            self._reward_button.configure(text="收起")
            self.dialog.update_idletasks()
        except OSError:
            self._reward_button.configure(text="赞赏码不可用", state=tk.DISABLED)

    def show(self):
        self.dialog.wait_window()


class SettingsGUI:
    """Settings UI retaining the original four-section layout."""

    def __init__(self, on_save: Callable = None):
        self._on_save = on_save
        self._root: tk.Toplevel | None = None
        self._entries = {}
        self._color_previews = {}
        self._monitor_update_id = None

    def show(self, settings: dict, master: tk.Tk = None):
        if self._root and self._root.winfo_exists():
            self._root.lift()
            self._root.focus_force()
            return

        self._root = tk.Toplevel(master) if master else tk.Toplevel()
        self._root.title("护眼程序 - 设置")
        self._root.configure(bg="#F5F7FB")
        self._root.resizable(True, True)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)
        _apply_window_icon(self._root)
        self._root.attributes("-topmost", True)
        self._configure_styles()

        content = ttk.Frame(self._root, style="Page.TFrame")
        content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Original structure: rest settings, blink settings, system settings, then actions.
        rest_frame = ttk.LabelFrame(content, text="休息设置", style="Settings.TLabelframe", padding=12)
        rest_frame.pack(fill=tk.X, padx=16, pady=(16, 6))
        rest_left = ttk.Frame(rest_frame, style="Page.TFrame")
        rest_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._add_field(rest_left, "休息间隔（分钟）", "rest_interval", settings.get("rest_interval", 20), 0)
        self._add_field(rest_left, "休息时长（秒）", "rest_duration", settings.get("rest_duration", 20), 1)
        self._add_slider(rest_left, "不透明度（%）", "rest_opacity", settings.get("rest_opacity", 70), 2)
        self._add_preview(rest_frame, "rest_opacity", settings.get("rest_opacity", 70))

        blink_frame = ttk.LabelFrame(content, text="眨眼设置", style="Settings.TLabelframe", padding=12)
        blink_frame.pack(fill=tk.X, padx=16, pady=6)
        blink_left = ttk.Frame(blink_frame, style="Page.TFrame")
        blink_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._add_field(blink_left, "提醒间隔（秒）", "blink_interval", settings.get("blink_interval", 45), 0)
        self._add_field(blink_left, "显示时长（秒）", "blink_duration", settings.get("blink_duration", 2.0), 1)
        self._add_slider(blink_left, "不透明度（%）", "blink_opacity", settings.get("blink_opacity", 100), 2)
        self._add_preview(blink_frame, "blink_opacity", settings.get("blink_opacity", 100))

        sys_frame = ttk.LabelFrame(content, text="系统设置", style="Settings.TLabelframe", padding=10)
        sys_frame.pack(fill=tk.X, padx=16, pady=(6, 10))
        self._paused_var = tk.BooleanVar(value=settings.get("paused", False))
        ttk.Checkbutton(sys_frame, text="暂停所有提醒（开会时使用）", variable=self._paused_var).pack(anchor=tk.W, pady=2)
        self._autostart_var = tk.BooleanVar(value=settings.get("autostart", False))
        ttk.Checkbutton(sys_frame, text="开机自动启动", variable=self._autostart_var).pack(anchor=tk.W, pady=2)

        # Pack the footer at the bottom so it remains available on smaller screens.
        btn_frame = ttk.Frame(self._root, style="Page.TFrame", padding=(16, 4, 16, 14))
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btn_frame, text="使用说明", command=self._open_usage, width=10).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="取消", command=self._on_close, width=10).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btn_frame, text="保存", command=self._on_save_click, width=10).pack(side=tk.RIGHT)

        self._fit_to_screen()
        self._root.bind("<Configure>", self._schedule_monitor_update, add="+")

    def _open_usage(self):
        UsageDialog(self._root).show()

    def _configure_styles(self):
        style = ttk.Style(self._root)
        style.configure("Page.TFrame", background="#F5F7FB")
        style.configure("Settings.TLabelframe", background="#F5F7FB")
        style.configure("Settings.TLabelframe.Label", background="#F5F7FB", foreground="#1D3557", font=(_FONT, 10, "bold"))

    def _fit_to_screen(self):
        self._root.update_idletasks()
        work_left, work_top, work_right, work_bottom = self._get_monitor_work_area()
        work_w, work_h = work_right - work_left, work_bottom - work_top
        max_width = max(360, min(680, work_w - 48))
        max_height = max(300, work_h - 48)
        self._apply_dpi_scaling(max_width, max_height)
        self._root.update_idletasks()
        width = min(max(520, self._root.winfo_reqwidth()), max_width)
        height = min(max(450, self._root.winfo_reqheight()), max_height)
        self._root.minsize(min(440, width), min(300, height))
        self._root.maxsize(max_width, max_height)
        x = work_left + (work_w - width) // 2
        y = max(work_top + 20, work_top + (work_h - height) // 2)
        self._root.geometry(f"{width}x{height}+{x}+{y}")

    def _apply_dpi_scaling(self, available_width, available_height):
        """Use the active monitor DPI, then reduce proportionally only if needed."""
        dpi = self._get_window_dpi()
        base_scale = dpi / 72.0
        self._root.tk.call("tk", "scaling", base_scale)
        self._root.update_idletasks()
        required_width = self._root.winfo_reqwidth()
        required_height = self._root.winfo_reqheight()
        fit = min(1.0, available_width / required_width, available_height / required_height)
        if fit < 1.0:
            self._root.tk.call("tk", "scaling", base_scale * fit)

    def _get_window_dpi(self):
        if sys.platform == "win32":
            try:
                return ctypes.windll.user32.GetDpiForWindow(self._root.winfo_id())
            except Exception:
                pass
        return self._root.winfo_fpixels("1i")

    def _get_monitor_work_area(self):
        """Return the taskbar-excluded work area of the window's current monitor."""
        if sys.platform != "win32":
            return 0, 0, self._root.winfo_screenwidth(), self._root.winfo_screenheight()
        try:
            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

            class MONITORINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", RECT), ("rcWork", RECT), ("dwFlags", ctypes.c_ulong)]

            monitor = ctypes.windll.user32.MonitorFromWindow(self._root.winfo_id(), 2)
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            if ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                return info.rcWork.left, info.rcWork.top, info.rcWork.right, info.rcWork.bottom
        except Exception:
            pass
        return 0, 0, self._root.winfo_screenwidth(), self._root.winfo_screenheight()

    def _schedule_monitor_update(self, event):
        if event.widget is not self._root:
            return
        if self._monitor_update_id:
            self._root.after_cancel(self._monitor_update_id)
        self._monitor_update_id = self._root.after(150, self._update_monitor_limits)

    def _update_monitor_limits(self):
        self._monitor_update_id = None
        left, top, right, bottom = self._get_monitor_work_area()
        max_width = max(360, min(680, right - left - 48))
        max_height = max(300, bottom - top - 48)
        self._apply_dpi_scaling(max_width, max_height)
        self._root.maxsize(max_width, max_height)

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
        value_var = tk.DoubleVar(value=default)
        display_var = tk.StringVar(value=str(int(round(default))))
        slider = ttk.Scale(parent, from_=0, to=100, variable=value_var, orient=tk.HORIZONTAL, length=110)
        slider.grid(row=row, column=1, sticky=tk.E, pady=5, padx=(12, 0))
        ttk.Label(parent, textvariable=display_var, width=4).grid(row=row, column=2, padx=(8, 0), pady=5)

        def sync_opacity(*_):
            value = int(round(value_var.get()))
            display_var.set(str(value))
            self._update_color_preview(key, value)

        value_var.trace_add("write", sync_opacity)
        self._entries[key] = value_var

    def _update_color_preview(self, key: str, value: int):
        canvas = self._color_previews.get(key)
        if not canvas:
            return
        gray = int(255 - (value / 100) * 255)
        color = f"#{gray:02x}{gray:02x}{gray:02x}"
        canvas.delete("all")
        canvas.create_rectangle(0, 0, 100, 80, fill=color, outline="")
        canvas.create_text(50, 40, text=f"{value}%", fill="#FFFFFF" if value > 55 else "#334155", font=(_FONT, 10, "bold"))

    def _get_value(self, key: str, is_float: bool = False):
        widget = self._entries.get(key)
        if isinstance(widget, (tk.IntVar, tk.DoubleVar)):
            return int(round(widget.get()))
        text = widget.get().strip()
        return float(text) if is_float else int(text)

    def collect_settings(self) -> dict:
        """收集并校验界面输入，越界值按 NUMERIC_LIMITS 裁剪。

        Raises:
            ValueError: 输入非法（非数字 / 非有限值）。
        """
        raw = {key: self._get_value(key, is_float=is_float) for key, (_, _, is_float) in NUMERIC_LIMITS.items()}
        raw["autostart"] = self._autostart_var.get()
        raw["paused"] = self._paused_var.get()

        for key, (minimum, _, is_float) in NUMERIC_LIMITS.items():
            value = raw[key]
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"{key} 必须是有限数字")
            raw[key] = float(max(minimum, value)) if is_float else max(int(minimum), value)
        return raw

    def _on_save_click(self):
        try:
            settings = self.collect_settings()
        except (ValueError, TypeError) as error:
            show_error(self._root, "输入有误", f"请输入有效的数字。\n{error}")
            return

        if self._on_save:
            self._on_save(settings)
        show_info(self._root, "设置已保存", "新的提醒设置已立即生效。")
        self._on_close()

    def _on_close(self):
        if self._root:
            self._root.destroy()
            self._root = None

    def destroy(self):
        self._on_close()
