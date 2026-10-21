# EyeCare 护眼程序

一款 Windows 桌面护眼程序：通过**定时休息**和**眨眼提醒**帮助长时间使用电脑的用户缓解眼部疲劳。

![Python](https://img.shields.io/badge/Python-3.11-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey) ![Tests](https://img.shields.io/badge/tests-28%20passed-brightgreen)

## 功能特性

| 功能 | 说明 |
|------|------|
| 定时休息提醒 | 每隔设定时间显示全屏半透明蒙版，引导远眺休息，支持 ESC / 按钮跳过 |
| 眨眼提醒 | 呼吸灯式渐变蒙版，柔和提醒完整眨眼，不抢占键盘鼠标焦点 |
| 多显示器支持 | 所有屏幕同时显示蒙版（EnumDisplayMonitors + DPI 感知） |
| 系统托盘 | 静默运行；托盘菜单一键暂停/恢复，无需打开设置 |
| 单实例保护 | 重复启动自动退出，不会出现双份托盘和双份提醒 |
| 个性化设置 | 休息间隔、时长、不透明度均可自定义，配置原子写入 |
| 开机自启 | 可选开机自动运行 |
| 首次运行引导 | 首次启动自动打开设置页，直接完成初始配置 |

## 运行效果

- 休息蒙版：全屏遮罩 + 右下角倒计时与跳过按钮
- 眨眼蒙版：0.3s 渐入 → 保持 → 0.3s 渐出，全程不抢焦点

## 快速开始

### 直接使用

从 [Releases](../../releases) 下载 `EyeCare.exe`（约 30MB，免安装）双击运行。

### 从源码运行

```bash
git clone https://github.com/siworld2100/EyeCare.git
cd EyeCare
pip install -r requirements.txt
python main.py
```

> 需要 Python 3.11+（含 tkinter），依赖仅 `pystray` 和 `Pillow`。

### 打包

```bash
pyinstaller --noconfirm --clean EyeCare.spec
# 产物：dist/EyeCare.exe
```

## 开发与测试

```bash
# 单元测试（无需图形界面，可进 CI）
python -m unittest discover -s tests -t . -v

# GUI 冒烟测试（需桌面环境，会短暂弹出蒙版）
python -m tests.smoke_overlay
```

## 架构一览

```
main.py                     # 入口：组件装配、跨线程调度、设置生效编排
eye_care/
  paths.py                  # 资源路径（开发 / PyInstaller 打包统一入口）
  config/                   # Settings 数据类 + 原子读写
  core/scheduler.py         # 休息/眨眼定时器状态机（不依赖 tkinter，可单测）
  system/                   # 开机自启、显示器枚举、单实例锁
  ui/                       # 蒙版、设置窗口、托盘、图标
tests/                      # 单元测试（假时钟）+ GUI 冒烟
```

设计约定：提醒节奏只由 `ReminderScheduler` 决定；数值边界只在 `NUMERIC_LIMITS` 声明一次；托盘线程回调经 `_post()` 投递回 Tk 主线程；配置损坏一律降级到默认值。

完整使用说明见 [使用文档.md](使用文档.md)。

## License

暂未指定开源许可证（默认保留所有权利）。如需二次分发请联系作者。
