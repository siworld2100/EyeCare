"""设置界面 - 配置休息/眨眼参数和系统选项"""

import os
import sys
import logging
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
        """
        初始化对话框
        Args:
            parent: 父窗口
            title: 标题
            message: 消息内容
            msg_type: 类型 - "info" 或 "error"
        """
        self.result = None

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)  # 关联父窗口
        self.dialog.grab_set()  # 模态

        # 设置图标
        if os.path.exists(_ICON_PATH):
            self.dialog.iconbitmap(_ICON_PATH)

        # 对话框内容
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # 图标和消息
        if msg_type == "error":
            icon_text = "错误"
        else:
            icon_text = "成功"

        ttk.Label(frame, text=icon_text, font=("Microsoft YaHei", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text=message, font=("Microsoft YaHei", 10), wraplength=300).pack(pady=(0, 15))

        # 确定按钮
        ttk.Button(frame, text="确定", command=self._on_ok, width=10).pack()

        # 键盘绑定
        self.dialog.bind("<Return>", lambda e: self._on_ok())
        self.dialog.bind("<Escape>", lambda e: self._on_ok())

        # 计算位置：显示在父窗口中心
        self.dialog.update_idletasks()
        dialog_w = self.dialog.winfo_width()
        dialog_h = self.dialog.winfo_height()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - dialog_w) // 2
        y = parent_y + (parent_h - dialog_h) // 2
        self.dialog.geometry(f"+{x}+{y}")

        # 确保在父窗口前面
        self.dialog.lift()
        self.dialog.focus_force()

    def _on_ok(self):
        """点击确定"""
        self.result = "ok"
        self.dialog.destroy()

    def show(self):
        """显示对话框并等待关闭"""
        self.dialog.wait_window()
        return self.result


def show_info(parent, title, message):
    """显示信息对话框"""
    dialog = MessageDialog(parent, title, message, "info")
    return dialog.show()


def show_error(parent, title, message):
    """显示错误对话框"""
    dialog = MessageDialog(parent, title, message, "error")
    return dialog.show()


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

        # 设置窗口图标
        if os.path.exists(_ICON_PATH):
            self._root.iconbitmap(_ICON_PATH)

        # 设置窗口属性
        self._root.attributes("-topmost", True)

        # 先显示窗口以获取正确的屏幕尺寸
        self._root.update_idletasks()

        # 窗口居中
        w, h = 420, 520
        x = (self._root.winfo_screenwidth() - w) // 2
        y = (self._root.winfo_screenheight() - h) // 2
        self._root.geometry(f"{w}x{h}+{x}+{y}")

        main_frame = ttk.Frame(self._root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ---- 休息设置 ----
        rest_frame = ttk.LabelFrame(main_frame, text="休息设置", padding=10)
        rest_frame.pack(fill=tk.X, pady=(0, 10))

        self._add_field(rest_frame, "休息间隔（分钟）", "rest_interval", settings.get("rest_interval", 20), 0)
        self._add_field(rest_frame, "休息时长（秒）", "rest_duration", settings.get("rest_duration", 20), 1)
        self._add_slider(rest_frame, "透明度", "rest_opacity", settings.get("rest_opacity", 70), 2)

        # ---- 眨眼设置 ----
        blink_frame = ttk.LabelFrame(main_frame, text="眨眼设置", padding=10)
        blink_frame.pack(fill=tk.X, pady=(0, 10))

        self._add_field(blink_frame, "提醒间隔（秒）", "blink_interval", settings.get("blink_interval", 45), 0)
        self._add_field(blink_frame, "显示时长（秒）", "blink_duration", settings.get("blink_duration", 1.5), 1)
        self._add_slider(blink_frame, "透明度", "blink_opacity", settings.get("blink_opacity", 30), 2)

        # ---- 系统设置 ----
        sys_frame = ttk.LabelFrame(main_frame, text="系统设置", padding=10)
        sys_frame.pack(fill=tk.X, pady=(0, 10))

        self._paused_var = tk.BooleanVar(value=settings.get("paused", False))
        paused_check = ttk.Checkbutton(
            sys_frame, text="暂停所有提醒（开会时使用）",
            variable=self._paused_var
        )
        paused_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)

        self._autostart_var = tk.BooleanVar(value=settings.get("autostart", False))
        autostart_check = ttk.Checkbutton(
            sys_frame, text="开机自启动",
            variable=self._autostart_var
        )
        autostart_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)

        # ---- 按钮 ----
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        cancel_btn = ttk.Button(btn_frame, text="取消", command=self._on_close)
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))

        save_btn = ttk.Button(btn_frame, text="保存", command=self._on_save_click)
        save_btn.pack(side=tk.RIGHT)

    def _add_field(self, parent, label: str, key: str, default, row: int):
        """添加输入字段"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)
        entry = ttk.Entry(parent, width=15)
        entry.insert(0, str(default))
        entry.grid(row=row, column=1, sticky=tk.E, pady=4, padx=(10, 0))
        self._entries[key] = entry

    def _add_slider(self, parent, label: str, key: str, default: int, row: int):
        """添加滑块，带渐变色块预览"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)

        # 右侧容器
        slider_frame = tk.Frame(parent)
        slider_frame.grid(row=row, column=1, sticky=tk.E, pady=4, padx=(10, 0))

        # 数值显示
        value_var = tk.IntVar(value=default)
        value_label = ttk.Label(slider_frame, textvariable=value_var, width=4)
        value_label.pack(side=tk.RIGHT, padx=(5, 0))

        # 滑块
        slider = ttk.Scale(
            slider_frame, from_=0, to=100, variable=value_var,
            orient=tk.HORIZONTAL, width=100, length=100
        )
        slider.pack(side=tk.RIGHT)

        # 渐变色块（从白到黑）
        gradient = tk.Canvas(slider_frame, width=120, height=16, highlightthickness=0)
        gradient.pack(side=tk.LEFT, padx=(0, 5))

        # 绘制渐变：0=白色（透明），100=黑色（不透明）
        for i in range(120):
            # 从白色(255)到黑色(0)
            gray = int(255 - (i / 119) * 255)
            color = f"#{gray:02x}{gray:02x}{gray:02x}"
            gradient.create_line(i, 0, i, 15, fill=color)

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
                "paused": self._paused_var.get(),
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
            show_info(self._root, "成功", "设置已保存")
            self._on_close()
        except (ValueError, TypeError) as e:
            logger.error("输入验证失败: %s", e)
            show_error(self._root, "输入错误", f"请输入有效的数字：\n{e}")

    def _on_close(self):
        """关闭窗口"""
        if self._root:
            self._root.destroy()
            self._root = None

    def destroy(self):
        """销毁窗口"""
        self._on_close()
