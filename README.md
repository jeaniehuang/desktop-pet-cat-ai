# 桌面萌宠 / Desktop Pet 🐱

A desktop companion cat that reacts to your AI agent's token consumption. Lives on your screen, always on top.

一只会对你 AI 助手 token 消耗做出反应的桌面陪伴猫。常驻屏幕，始终置顶。

---

## States / 状态

| State 状态 | Trigger 触发条件 | Animation 动画 |
|------------|-----------------|----------------|
| 💤 **Sleeping 睡觉** | Claude idle / no token consumption<br>Claude 空闲 / 无 token 消耗 | `waiting.gif` + Zzz floating up<br>`waiting.gif` + Zzz 飘字 |
| 🏃 **Working 工作中** | Claude consuming tokens<br>Claude 消耗 token 中 | Randomly picks `running.gif` / `running-left.gif` / `running-right.gif`<br>随机切换三个方向跑步 GIF |
| ⏸️ **Break 休息提醒** | Every 30 minutes (or manual trigger)<br>每 30 分钟（或手动触发） | `review.gif` + 💫⭐✨ spinning above head, slides from right to left along screen bottom in 20s<br>`review.gif` + 💫⭐✨ 头顶旋转，沿屏幕底部从右到左滑行 20 秒 |

## How It Works / 工作原理

Reads `/tmp/claude-status-light` (or `%TEMP%\claude-status-light` on Windows), which is written by Claude Code hooks:

读取 `/tmp/claude-status-light`（Windows 下为 `%TEMP%\claude-status-light`），由 Claude Code hooks 写入：

- 🟢 = tokens flowing / token 消耗中 → **Working 工作中**
- 🔴 = idle / 空闲 → **Sleeping 睡觉**

## Features / 功能

- Always-on-top, frameless, circular window / 置顶、无边框、圆形窗口
- Drag to reposition / 可拖拽移动
- System tray with right-click menu / 系统托盘右键菜单:
  - 🍽️ Force Working / 强制工作中
  - 😴 Force Sleeping / 强制睡觉
  - 🏃 Trigger Break / 立即休息提醒
  - ❌ Quit / 退出
- 30-minute break reminder with screen-bottom patrol / 30 分钟休息提醒，屏幕底部巡逻

## Run / 运行

### From source / 源码运行
```bash
pip install PySide6
python pet.py
```

### Standalone exe / 独立 exe
Double-click `dist/DesktopPet.exe` or use the desktop shortcut.

双击 `dist/DesktopPet.exe` 或桌面快捷方式。

## GIF Credits / GIF 来源

Cat animations from [YueXinMiao (月薪喵)](https://github.com/Lumi-arta/desktop_cat) by Lumi-arta.
https://github.com/Tinsiag/YueXinMiaoPet

## License / 许可证

MIT
