#!/usr/bin/env python3
"""16+8 间歇性禁食闹钟 — tkinter 桌面版

运行: python3 gui.py
"""
import json
import subprocess
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "fasting-16-8.json"
DEFAULT_START = "12:00"
DEFAULT_END = "20:00"

BG        = "#1a1d24"
CARD      = "#252934"
CARD_IN   = "#2e3340"
TEXT      = "#f1f3f7"
MUTED     = "#8b93a3"
TRACK     = "#3a4050"
EAT       = "#7dd886"
EAT_SOFT  = "#2c4030"
FAST      = "#e9b878"
FAST_SOFT = "#3f3424"


def load_config():
    try:
        return json.loads(CONFIG_PATH.read_text())
    except Exception:
        return {}


def save_config(cfg):
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
    except Exception:
        pass


def parse_hhmm(s):
    h, m = s.split(":")
    h, m = int(h), int(m)
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError
    return h, m


def next_occurrence(hhmm, now):
    h, m = parse_hhmm(hhmm)
    d = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if d <= now:
        d += timedelta(days=1)
    return d


def window_minutes(start, end):
    sh, sm = parse_hhmm(start)
    eh, em = parse_hhmm(end)
    diff = (eh * 60 + em) - (sh * 60 + sm)
    if diff <= 0:
        diff += 24 * 60
    return diff


def fmt_duration(seconds):
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def notify(title, message, sound=True):
    safe_title = title.replace('"', '\\"')
    safe_msg = message.replace('"', '\\"')
    try:
        subprocess.Popen(
            ["osascript", "-e",
             f'display notification "{safe_msg}" with title "{safe_title}"'],
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    if sound:
        try:
            subprocess.Popen(
                ["afplay", "/System/Library/Sounds/Glass.aiff"],
                stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            )
        except Exception:
            pass


class App:
    def __init__(self, root):
        self.root = root
        cfg = load_config()
        self.start = tk.StringVar(value=cfg.get("start", DEFAULT_START))
        self.end = tk.StringVar(value=cfg.get("end", DEFAULT_END))
        self.sound = tk.BooleanVar(value=cfg.get("sound", True))
        self.prev_state = None
        self._build()
        self._tick()

    def _build(self):
        root = self.root
        root.title("16 + 8 间歇性禁食")
        root.configure(bg=BG)
        root.geometry("420x600")
        root.minsize(380, 560)

        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(header, text="16 + 8  间歇性禁食",
                 bg=BG, fg=TEXT,
                 font=("SF Pro Text", 14, "bold")).pack(side="left")
        self.now_lbl = tk.Label(header, text="--:--:--",
                                bg=BG, fg=MUTED,
                                font=("Menlo", 11))
        self.now_lbl.pack(side="right")

        card = tk.Frame(root, bg=CARD)
        card.pack(fill="both", expand=True, padx=20, pady=(8, 16))

        self.badge = tk.Label(card, text="载入中…",
                              bg=CARD, fg=MUTED,
                              font=("SF Pro Text", 12, "bold"),
                              pady=6, padx=14)
        self.badge.pack(pady=(22, 0))

        self.canvas_size = 240
        self.canvas = tk.Canvas(card,
                                width=self.canvas_size,
                                height=self.canvas_size,
                                bg=CARD, highlightthickness=0, bd=0)
        self.canvas.pack(pady=(14, 8))

        inputs = tk.Frame(card, bg=CARD)
        inputs.pack(fill="x", padx=28, pady=(18, 8))
        self._make_input(inputs, "开始进食", self.start, 0)
        self._make_input(inputs, "结束进食", self.end, 1)
        inputs.columnconfigure(0, weight=1)
        inputs.columnconfigure(1, weight=1)

        bar = tk.Frame(card, bg=CARD)
        bar.pack(fill="x", padx=28, pady=(8, 22))
        self.summary = tk.Label(bar, text="",
                                bg=CARD, fg=MUTED,
                                font=("SF Pro Text", 11))
        self.summary.pack(side="left")
        cb = tk.Checkbutton(bar, text="提示音", variable=self.sound,
                            bg=CARD, fg=MUTED, selectcolor=CARD,
                            activebackground=CARD, activeforeground=TEXT,
                            borderwidth=0, highlightthickness=0,
                            font=("SF Pro Text", 11),
                            command=self._save)
        cb.pack(side="right")

        self.start.trace_add("write", lambda *_: self._on_change())
        self.end.trace_add("write", lambda *_: self._on_change())

    def _make_input(self, parent, label, var, col):
        padx = (0, 0) if col == 0 else (10, 0)
        tk.Label(parent, text=label, bg=CARD, fg=MUTED,
                 font=("SF Pro Text", 9, "bold")).grid(
                     row=0, column=col, sticky="w", padx=padx)
        e = tk.Entry(parent, textvariable=var,
                     bg=CARD_IN, fg=TEXT,
                     insertbackground=TEXT,
                     relief="flat", bd=0,
                     font=("Menlo", 16), justify="center",
                     highlightthickness=1,
                     highlightbackground=TRACK,
                     highlightcolor="#5a6478")
        e.grid(row=1, column=col, sticky="ew", padx=padx, pady=(6, 0), ipady=9)

    def _on_change(self):
        try:
            parse_hhmm(self.start.get())
            parse_hhmm(self.end.get())
        except Exception:
            return
        self.prev_state = None
        self._save()

    def _save(self):
        save_config({
            "start": self.start.get(),
            "end": self.end.get(),
            "sound": self.sound.get(),
        })

    def _draw(self, progress, color, is_eating, remaining, next_switch):
        c = self.canvas
        c.delete("all")
        pad = 18
        size = self.canvas_size
        x0, y0, x1, y1 = pad, pad, size - pad, size - pad

        c.create_arc(x0, y0, x1, y1, start=0, extent=359.999,
                     style="arc", outline=TRACK, width=10)
        if progress > 0:
            extent = -360 * progress
            c.create_arc(x0, y0, x1, y1, start=90, extent=extent,
                         style="arc", outline=color, width=10)

        cx = cy = size // 2
        c.create_text(cx, cy - 32,
                      text=("距停嘴" if is_eating else "距开吃"),
                      fill=MUTED,
                      font=("SF Pro Text", 9, "bold"))
        c.create_text(cx, cy + 2,
                      text=fmt_duration(remaining),
                      fill=TEXT,
                      font=("Menlo", 28, "bold"))
        c.create_text(cx, cy + 36,
                      text=next_switch.strftime(
                          "%H:%M " + ("结束进食" if is_eating else "开始进食")),
                      fill=MUTED,
                      font=("SF Pro Text", 10))

    def _tick(self):
        try:
            start = self.start.get()
            end = self.end.get()
            parse_hhmm(start)
            parse_hhmm(end)
        except Exception:
            self.root.after(1000, self._tick)
            return

        now = datetime.now()
        self.now_lbl.config(text=now.strftime("%H:%M:%S"))

        ns = next_occurrence(start, now)
        ne = next_occurrence(end, now)
        is_eating = ne < ns

        eat_min = window_minutes(start, end)
        fast_min = 24 * 60 - eat_min

        next_switch = ne if is_eating else ns
        remaining = (next_switch - now).total_seconds()
        phase_total = (eat_min if is_eating else fast_min) * 60
        progress = (
            max(0.0, min(1.0, (phase_total - remaining) / phase_total))
            if phase_total else 0
        )

        state = "eating" if is_eating else "fasting"
        color = EAT if is_eating else FAST
        soft = EAT_SOFT if is_eating else FAST_SOFT

        self.badge.config(
            text=("● 进食窗口中" if is_eating else "● 禁食中"),
            bg=soft, fg=color,
        )
        self._draw(progress, color, is_eating, remaining, next_switch)
        self.summary.config(
            text=f"进食 {eat_min // 60}h · 禁食 {fast_min // 60}h"
        )

        if self.prev_state and self.prev_state != state:
            if state == "eating":
                notify("可以开吃了 🍽️",
                       f"进食窗口 {start} – {end}",
                       self.sound.get())
            else:
                notify("该停嘴了 🛑",
                       f"进入 {fast_min // 60} 小时禁食",
                       self.sound.get())
        self.prev_state = state

        self.root.after(1000, self._tick)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
