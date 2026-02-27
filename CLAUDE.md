# CLAUDE.md

## Project: Claude Usage Monitor Widget

A lightweight always-on-top Windows desktop widget showing weekly Claude usage limit % as a colored progress bar.

## Tech Stack

- **Python 3.10+** with **tkinter** (stdlib, no GUI framework install needed)
- Single-file app: `claude_usage_widget.py`
- State persisted to `~/.claude_usage/` (JSON files)

## Quick Start

```bash
python claude_usage_widget.py
```

Or on Windows: double-click `start.bat`

## Architecture

- `claude_usage_widget.py` — Entire app in one file. Classes: `Config`, `State`, `UsageWidget`
- `~/.claude_usage/config.json` — User prefs (opacity, position, reset day)
- `~/.claude_usage/state.json` — Runtime state (current %, week start)

## Key Behaviors

- Borderless draggable window, always on top
- Color gradient: green (0-50%) → yellow (50-80%) → red (80-100%)
- Right-click menu: set %, quick increment, reset, exit
- Scroll wheel adjusts % by 1
- Auto-resets to 0% weekly (default: Monday)
- Semi-transparent when not hovered

## Conventions

- Keep it single-file — no unnecessary abstractions
- No external dependencies beyond Python stdlib
- All config/state in `~/.claude_usage/`
- Test manually on Windows; tkinter varies across OS
