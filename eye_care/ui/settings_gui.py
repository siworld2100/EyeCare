"""设置界面 - 配置休息/眨眼参数和系统选项"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

logger = logging.getLogger(__name__)


class SettingsGUI:
    """设置界面"""

    def __init__(self, on_save: Callable = None):
        """
        初始化设置界面
        Args:
            on_save: 保存配置的回调，接收 settings 字典
        """
        self._on_save = on_save
        self._root: tk.Toplevel = None

        # 输入框引用
        self._entries = {}

    def show(self, settings: dict, master: tk.Tk = None):
        """显示设置窗口"""
        if self._root and self._root.winfo_exists():
            self._root.lift()
            self._root.focus_force()
            return

        # 使用 Toplevel 而不是 Tk
        if master:
            self._root = tk.Toplevel(master)
        else:
            self._root = tk.Toplevel()

        self._root.title("护眼程序 - 设置")
        self._root.resizable(False, False)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 窗口居中
        w, h = 420, 520
        x = (self._root.winfo_screenwidth() - w) // 2
        y = (self._root.winfo_screenheight() - h) // 2
        self._root.geometry(f"{w}x{h}+{x}+{y}")

        # 设置窗口属性
        self._root.attributes("-topmost", True)

        main_frame = ttk.Frame(self._root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ---- 休息设置 ----
        rest_frame = ttk.LabelFrame(main_frame, text="休息设置", padding=10)
        rest_frame.pack(fill=tk.X, pady=(0, 10))

        self._add_field(rest_frame, "休息间隔（分钟）", "rest_interval", settings.get("rest_interval", 20), 0)
        self._add_field(rest_frame, "休息时长（秒）", "rest_duration", settings.get("rest_duration", 20), 1)
        self._add_slider(rest_frame, "蒙版透明度（%）", "rest_opacity", settings.get("rest_opacity", 70), 2)

        # ---- 眨眼设置 ----
        blink_frame = ttk.LabelFrame(main_frame, text="眨眼设置", padding=10)
        blink_frame.pack(fill=tk.X, pady=(0, 10))

        self._add_field(blink_frame, "提醒间隔（秒）", "blink_interval", settings.get("blink_interval", 45), 0)
        self._add_field(blink_frame, "显示时长（秒）", "blink_duration", settings.get("blink_duration", 1.5), 1)
        self._add_slider(blink_frame, "蒙版透明度（%）", "blink_opacity", settings.get("blink_opacity", 30), 2)

        # ---- 系统设置 ----
        sys_frame = ttk.LabelFrame(main_frame, text="系统设置", padding=10)
        sys_frame.pack(fill=tk.X, pady=(0, 10))

        self._autostart_var = tk.BooleanVar(value=settings.get("autostart", False))
        autostart_check = ttk.Checkbutton(
            sys_frame, text="开机自启动",
            variable=self._autostart_var
        )
        autostart_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)

        # ---- 按钮 ----
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        cancel_btn = ttk.Button(btn_frame, text="取消", command=self._on_close)
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))

        save_btn = ttk.Button(btn_frame, text="保存", command=self._on_save_click)
        save_btn.pack(side=tk.RIGHT)

        # 强制刷新界面
        self._root.update_idletasks()
        self._root.update()

    def _add_field(self, parent, label: str, key: str, default, row: int):
        """添加输入字段"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)
        entry = ttk.Entry(parent, width=15)
        entry.insert(0, str(default))
        entry.grid(row=row, column=1, sticky=tk.E, pady=4, padx=(10, 0))
        self._entries[key] = entry

    def _add_slider(self, parent, label: str, key: str, default: int, row: int):
        """添加滑块"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)
        value_var = tk.IntVar(value=default)
        slider = ttk.Scale(
            parent, from_=0, to=100, variable=value_var,
            orient=tk.HORIZONTAL, length=120
        )
        slider.grid(row=row, column=1, sticky=tk.E, pady=4, padx=(10, 0))
        self._entries[key] = value_var

    def _get_value(self, key: str, is_float: bool = False):
        """获取字段值"""
        widget = self._entries.get(key)
        if widget is None:
            return None
        if isinstance(widget, tk.IntVar):
            return widget.get()
        text = widget.get().strip()
        if is_float:
            return float(text)
        return int(text)

    def _on_save_click(self):
        """保存按钮点击"""
        try:
            settings = {
                "rest_interval": self._get_value("rest_interval"),
                "rest_duration": self._get_value("rest_duration"),
                "rest_opacity": self._get_value("rest_opacity"),
                "blink_interval": self._get_value("blink_interval"),
                "blink_duration": self._get_value("blink_duration", is_float=True),
                "blink_opacity": self._get_value("blink_opacity"),
                "autostart": self._autostart_var.get(),
            }
            # 基本验证
            if settings["rest_interval"] < 1:
                settings["rest_interval"] = 1
            if settings["rest_duration"] < 5:
                settings["rest_duration"] = 5
            if settings["blink_interval"] < 10:
                settings["blink_interval"] = 10
            if settings["blink_duration"] < 0.5:
                settings["blink_duration"] = 0.5

            if self._on_save:
                self._on_save(settings)
            logger.info("设置已保存: %s", settings)
            messagebox.showinfo("成功", "设置已保存")
            self._on_close()
        except (ValueError, TypeError) as e:
            logger.error("输入验证失败: %s", e)
            messagebox.showerror("输入错误", f"请输入有效的数字：\n{e}")

    def _on_close(self):
        """关闭窗口"""
        if self._root:
            self._root.destroy()
            self._root = None

    def destroy(self):
        """销毁窗口"""
        self._on_close()
