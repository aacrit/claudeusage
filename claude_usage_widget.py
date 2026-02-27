"""
Claude Usage Monitor — Always-on-top Windows widget
Shows weekly Claude usage limit percentage as a colored progress bar.

Usage:
    python claude_usage_widget.py

Controls:
    - Drag anywhere to reposition
    - Scroll wheel to adjust usage +/- 1%
    - Right-click for menu (set %, quick bumps, reset, exit)
    - Double-click the bar to type a specific %
    - Hover to show full opacity
"""

import json
import tkinter as tk
from tkinter import simpledialog
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
APP_DIR = Path.home() / ".claude_usage"
CONFIG_FILE = APP_DIR / "config.json"
STATE_FILE = APP_DIR / "state.json"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "reset_day": "Monday",
    "opacity": 0.85,
    "width": 230,
    "height": 52,
    "position_x": None,
    "position_y": None,
}

DEFAULT_STATE = {
    "usage_percent": 0,
    "week_start": None,
    "last_updated": None,
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ---------------------------------------------------------------------------
# Color theme
# ---------------------------------------------------------------------------
BG = "#1a1a2e"
BG_DARK = "#0d0d1a"
BORDER = "#333355"
TITLE_FG = "#8888aa"
TEXT_FONT = ("Segoe UI", 8)
PCT_FONT = ("Segoe UI Semibold", 11)


def lerp_color(pct: int) -> str:
    """Return a hex color on a green → yellow → red gradient."""
    pct = max(0, min(100, pct))
    if pct < 50:
        ratio = pct / 50
        r = int(40 + ratio * 215)
        g = 200
        b = 80
    elif pct < 80:
        ratio = (pct - 50) / 30
        r = 255
        g = int(200 - ratio * 130)
        b = int(80 - ratio * 50)
    else:
        ratio = (pct - 80) / 20
        r = 255
        g = int(70 - ratio * 50)
        b = int(30 + ratio * 30)
    return f"#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}"


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------
def _load_json(path: Path, defaults: dict) -> dict:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            with open(path) as f:
                data = json.load(f)
            return {**defaults, **data}
        except (json.JSONDecodeError, OSError):
            pass
    return defaults.copy()


def _save_json(path: Path, data: dict) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------
class UsageWidget:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.config = _load_json(CONFIG_FILE, DEFAULT_CONFIG)
        self.state = _load_json(STATE_FILE, DEFAULT_STATE)

        self._ensure_week_start()
        self._check_weekly_reset()
        self._setup_window()
        self._build_ui()
        self._bind_events()

    # -- lifecycle ----------------------------------------------------------

    def run(self) -> None:
        self._tick()
        self.root.mainloop()

    def _tick(self) -> None:
        """Periodic refresh: update bar and check for weekly reset."""
        self._check_weekly_reset()
        self._render_bar()
        self.root.after(5000, self._tick)

    # -- persistence --------------------------------------------------------

    def _save_state(self) -> None:
        self.state["last_updated"] = datetime.now().isoformat()
        _save_json(STATE_FILE, self.state)

    def _save_config(self) -> None:
        _save_json(CONFIG_FILE, self.config)

    # -- weekly reset -------------------------------------------------------

    def _ensure_week_start(self) -> None:
        if not self.state.get("week_start"):
            self.state["week_start"] = self._current_week_start().isoformat()
            self._save_state()

    def _current_week_start(self) -> datetime:
        reset_idx = DAYS.index(self.config["reset_day"])
        now = datetime.now()
        days_since = (now.weekday() - reset_idx) % 7
        return (now - timedelta(days=days_since)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def _check_weekly_reset(self) -> None:
        current_ws = self._current_week_start()
        stored = self.state.get("week_start")
        if stored:
            try:
                last_ws = datetime.fromisoformat(stored)
                if current_ws > last_ws:
                    self.state["usage_percent"] = 0
                    self.state["week_start"] = current_ws.isoformat()
                    self._save_state()
            except ValueError:
                self.state["week_start"] = current_ws.isoformat()
                self._save_state()

    # -- window setup -------------------------------------------------------

    def _setup_window(self) -> None:
        self.root.title("Claude Usage")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", self.config["opacity"])
        self.root.configure(bg=BG)

        w = self.config["width"]
        h = self.config["height"]
        if self.config["position_x"] is not None:
            x, y = self.config["position_x"], self.config["position_y"]
        else:
            x = self.root.winfo_screenwidth() - w - 20
            y = 20
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self._drag = {"x": 0, "y": 0}

    # -- UI -----------------------------------------------------------------

    def _build_ui(self) -> None:
        self.frame = tk.Frame(
            self.root, bg=BG, highlightbackground=BORDER, highlightthickness=1
        )
        self.frame.pack(fill="both", expand=True)

        # Header row
        header = tk.Frame(self.frame, bg=BG)
        header.pack(fill="x", padx=8, pady=(5, 0))

        self.title_lbl = tk.Label(
            header, text="Claude Usage", font=TEXT_FONT, fg=TITLE_FG, bg=BG, anchor="w"
        )
        self.title_lbl.pack(side="left")

        self.reset_lbl = tk.Label(
            header, text="", font=("Segoe UI", 7), fg="#666680", bg=BG, anchor="e"
        )
        self.reset_lbl.pack(side="right")
        self._update_reset_label()

        # Bar + percentage row
        bar_row = tk.Frame(self.frame, bg=BG)
        bar_row.pack(fill="x", padx=8, pady=(2, 6))

        self.canvas = tk.Canvas(bar_row, height=16, bg=BG_DARK, highlightthickness=0, bd=0)
        self.canvas.pack(fill="x", side="left", expand=True)

        self.pct_lbl = tk.Label(
            bar_row, text="0%", font=PCT_FONT, fg="white", bg=BG, width=5, anchor="e"
        )
        self.pct_lbl.pack(side="right", padx=(6, 0))

    def _render_bar(self) -> None:
        pct = self.state["usage_percent"]
        color = lerp_color(pct)

        self.canvas.delete("all")
        self.canvas.update_idletasks()
        total_w = self.canvas.winfo_width()
        fill_w = max(0, int((pct / 100) * total_w))

        # Bar background
        self.canvas.create_rectangle(0, 0, total_w, 16, fill=BG_DARK, outline="")
        # Rounded-ish fill (small radius via overlapping rects is fine at this scale)
        if fill_w > 0:
            self.canvas.create_rectangle(0, 0, fill_w, 16, fill=color, outline="")

        self.pct_lbl.configure(text=f"{pct}%", fg=color)

    def _update_reset_label(self) -> None:
        ws = self._current_week_start()
        reset = ws + timedelta(days=7)
        days_left = (reset - datetime.now()).days
        self.reset_lbl.configure(text=f"resets in {days_left}d")

    # -- event bindings -----------------------------------------------------

    def _bind_events(self) -> None:
        # Drag
        drag_widgets = [self.frame, self.title_lbl, self.pct_lbl, self.reset_lbl]
        for w in drag_widgets:
            w.bind("<Button-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)

        # Right-click context menu
        self.ctx_menu = tk.Menu(
            self.root, tearoff=0, bg=BG, fg="white",
            activebackground="#333355", activeforeground="white",
            font=("Segoe UI", 9),
        )
        self.ctx_menu.add_command(label="Set Usage %...", command=self._prompt_set)
        self.ctx_menu.add_separator()
        self.ctx_menu.add_command(label="+5 %", command=lambda: self._adjust(5))
        self.ctx_menu.add_command(label="+10 %", command=lambda: self._adjust(10))
        self.ctx_menu.add_command(label="+25 %", command=lambda: self._adjust(25))
        self.ctx_menu.add_separator()
        self.ctx_menu.add_command(label="Reset to 0 %", command=self._reset)
        self.ctx_menu.add_separator()
        self.ctx_menu.add_command(label="Exit", command=self._exit)

        for w in [self.root, self.frame, self.title_lbl, self.canvas,
                  self.pct_lbl, self.reset_lbl]:
            w.bind("<Button-3>", self._show_ctx)

        # Scroll-wheel
        self.root.bind("<MouseWheel>", self._on_scroll)
        # Linux scroll events
        self.root.bind("<Button-4>", lambda e: self._adjust(1))
        self.root.bind("<Button-5>", lambda e: self._adjust(-1))

        # Double-click bar to type a value
        self.canvas.bind("<Double-Button-1>", lambda e: self._prompt_set())

        # Hover opacity
        self.root.bind("<Enter>", lambda e: self.root.attributes("-alpha", 1.0))
        self.root.bind("<Leave>", lambda e: self.root.attributes("-alpha", self.config["opacity"]))

    # -- drag ---------------------------------------------------------------

    def _drag_start(self, event) -> None:
        self._drag["x"] = event.x
        self._drag["y"] = event.y

    def _drag_move(self, event) -> None:
        x = self.root.winfo_x() + event.x - self._drag["x"]
        y = self.root.winfo_y() + event.y - self._drag["y"]
        self.root.geometry(f"+{x}+{y}")
        self.config["position_x"] = x
        self.config["position_y"] = y
        self._save_config()

    # -- context menu -------------------------------------------------------

    def _show_ctx(self, event) -> None:
        self.ctx_menu.tk_popup(event.x_root, event.y_root)

    # -- usage manipulation -------------------------------------------------

    def _set_usage(self, pct: int) -> None:
        self.state["usage_percent"] = max(0, min(100, pct))
        self._save_state()
        self._render_bar()

    def _adjust(self, delta: int) -> None:
        self._set_usage(self.state["usage_percent"] + delta)

    def _prompt_set(self) -> None:
        val = simpledialog.askinteger(
            "Set Usage",
            "Enter usage percentage (0–100):",
            initialvalue=self.state["usage_percent"],
            minvalue=0,
            maxvalue=100,
            parent=self.root,
        )
        if val is not None:
            self._set_usage(val)

    def _reset(self) -> None:
        self._set_usage(0)

    def _on_scroll(self, event) -> None:
        delta = 1 if event.delta > 0 else -1
        self._adjust(delta)

    # -- exit ---------------------------------------------------------------

    def _exit(self) -> None:
        self._save_state()
        self._save_config()
        self.root.destroy()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    widget = UsageWidget()
    widget.run()
