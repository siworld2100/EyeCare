"""GUI 冒烟测试 - 真实创建 tkinter 窗口验证蒙版行为

与单元测试分离：需要可用的图形环境，运行方式：
    python -m tests.smoke_overlay
"""

import sys
import tkinter as tk

from eye_care.system.monitors import get_monitors
from eye_care.ui.overlay import Overlay


def run_with_loop(root: tk.Tk, duration_ms: int, stop_when):
    """用真实事件循环等待 duration_ms 或 stop_when 为真。"""
    result = {"done": False}

    def tick():
        if stop_when():
            result["done"] = True
            root.quit()
        else:
            root.after(50, tick)

    def timeout():
        root.quit()

    root.after(50, tick)
    root.after(duration_ms, timeout)
    root.mainloop()
    return result["done"]


def main() -> int:
    root = tk.Tk()
    root.withdraw()

    monitors = get_monitors(root)
    print(f"检测到 {len(monitors)} 个显示器:")
    for index, monitor in enumerate(monitors):
        print(f"  [{index}] {monitor.geometry}")

    skipped = []
    overlay = Overlay(on_skip=lambda: skipped.append(1))

    # 1) 休息蒙版：窗口数量 / 透明度 / 几何位置
    overlay.show_rest(duration=1, opacity=70)
    root.update()
    print(f"休息蒙版: windows={len(overlay._windows)}, is_showing={overlay.is_showing}")
    for window in overlay._windows:
        alpha = float(window.attributes("-alpha"))
        print(f"  geometry={window.geometry()} alpha={alpha:.2f}")
        assert alpha <= 0.71, "休息蒙版透明度未按配置应用"
    assert len(overlay._windows) == len(monitors), "蒙版窗口数量应与显示器数量一致"

    closed = run_with_loop(root, 4000, lambda: not overlay.is_showing)
    print(f"倒计时结束: closed={closed}, skip 回调次数={len(skipped)}")
    assert closed, "休息蒙版应在倒计时结束后自动关闭"
    assert len(skipped) == 1, "休息结束应触发 on_skip 回调"

    # 2) 眨眼蒙版：渐变后自动关闭，且不触发 on_skip
    overlay.show_blink(duration=0.8, opacity=80)
    root.update()
    print(f"眨眼蒙版: windows={len(overlay._windows)}, 无控制元素={overlay._skip_button is None}")
    closed = run_with_loop(root, 5000, lambda: not overlay.is_showing)
    print(f"眨眼结束: closed={closed}, skip 回调次数={len(skipped)}")
    assert closed, "眨眼蒙版应在渐出后关闭"
    assert len(skipped) == 1, "眨眼蒙版不应触发 on_skip"

    # 3) 重复显示不应叠加窗口
    overlay.show_blink(duration=0.4, opacity=50)
    overlay.show_rest(duration=5, opacity=50)  # 眨眼进行中，休息请求应被忽略
    root.update()
    assert len(overlay._windows) == len(monitors), "重复显示不应叠加窗口"
    assert overlay._skip_button is None, "眨眼进行中的休息请求应被忽略"
    overlay.hide()
    root.update()

    root.destroy()
    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
