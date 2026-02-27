# Claude Usage Monitor

A tiny always-on-top Windows widget that shows your weekly Claude usage limit as a colored progress bar.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue) ![No Dependencies](https://img.shields.io/badge/dependencies-none-green)

## Features

- **Always-on-top** borderless widget (~230 x 52 px)
- **Color-coded** progress bar: green → yellow → red
- **Auto-resets** weekly (configurable reset day, default Monday)
- **Draggable** — click and drag anywhere to reposition
- **Scroll wheel** adjusts usage by 1%
- **Right-click menu** — set %, quick bumps (+5/+10/+25), reset, exit
- **Semi-transparent** when not hovered, full opacity on hover
- **Persists** position, config, and state across restarts

## Quick Start

```bash
python claude_usage_widget.py
```

**Windows:** Double-click `start.bat` (uses `pythonw` for no console window).

**Auto-start on login:** Copy `start.bat` into your Windows Startup folder.
Press `Win + R`, type `shell:startup`, press Enter, then paste the shortcut there.

## Requirements

- Python 3.10+ (tkinter is included with standard Windows Python installs)
- No pip packages needed

## Controls

| Action | Effect |
|---|---|
| **Right-click** | Open menu (set %, bump, reset, exit) |
| **Scroll wheel** | Adjust usage ±1% |
| **Double-click** bar | Type a specific % |
| **Drag** anywhere | Reposition the widget |
| **Hover** | Full opacity; move away to dim |

## Configuration

Settings are stored in `~/.claude_usage/config.json`:

```json
{
  "reset_day": "Monday",
  "opacity": 0.85,
  "width": 230,
  "height": 52
}
```

State (current %, week start) is in `~/.claude_usage/state.json`.
