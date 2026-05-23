#!/usr/bin/env python3
"""16+8 间歇性禁食闹钟 — 命令行版

用法:
    python3 cli.py
    python3 cli.py --start 12:00 --end 20:00
    python3 cli.py --no-sound
"""
import argparse
import json
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "fasting-16-8.json"
DEFAULT_START = "12:00"
DEFAULT_END = "20:00"

RESET = "\033[0m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
GREEN = "\033[38;5;114m"
AMBER = "\033[38;5;215m"
GRAY  = "\033[38;5;245m"
CLEAR = "\033[2J\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"


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
        raise ValueError(f"invalid time: {s}")
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


def progress_bar(progress, width=40, color=GREEN):
    filled = int(progress * width)
    return f"{color}{'█' * filled}{GRAY}{'░' * (width - filled)}{RESET}"


def render(now, start, end, is_eating, remaining, next_switch,
           progress, eat_min, fast_min, sound):
    color = GREEN if is_eating else AMBER
    label = "进食窗口中 🍽️" if is_eating else "禁食中 ⏳"
    phase = "距停嘴还有" if is_eating else "距开吃还有"
    next_label = "结束进食" if is_eating else "开始进食"
    pct = int(progress * 100)

    lines = [
        "",
        f"  {BOLD}16 + 8  间歇性禁食{RESET}    "
        f"{DIM}{now.strftime('%Y-%m-%d %H:%M:%S')}{RESET}",
        "",
        f"  {color}{BOLD}● {label}{RESET}",
        "",
        f"  {GRAY}{phase}{RESET}",
        f"  {BOLD}{color}{fmt_duration(remaining)}{RESET}    "
        f"{DIM}{next_switch.strftime('%H:%M')} {next_label}{RESET}",
        "",
        f"  {progress_bar(progress, 42, color)}  "
        f"{DIM}{pct:>3d}%{RESET}",
        "",
        f"  {DIM}窗口 {start} – {end}  ·  "
        f"进食 {eat_min // 60}h · 禁食 {fast_min // 60}h{RESET}",
        f"  {DIM}提示音 {'on' if sound else 'off'}  ·  Ctrl+C 退出{RESET}",
        "",
    ]
    sys.stdout.write(CLEAR + "\n".join(lines))
    sys.stdout.flush()


def main():
    p = argparse.ArgumentParser(
        description="16+8 间歇性禁食闹钟（终端版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--start", help="进食开始时间 HH:MM")
    p.add_argument("--end", help="进食结束时间 HH:MM")
    p.add_argument("--no-sound", action="store_true", help="关闭提示音")
    args = p.parse_args()

    cfg = load_config()
    start = args.start or cfg.get("start", DEFAULT_START)
    end = args.end or cfg.get("end", DEFAULT_END)
    sound = cfg.get("sound", True)
    if args.no_sound:
        sound = False

    try:
        parse_hhmm(start)
        parse_hhmm(end)
    except Exception:
        print(f"错误: 时间格式应为 HH:MM，得到 start={start!r} end={end!r}",
              file=sys.stderr)
        sys.exit(1)

    save_config({"start": start, "end": end, "sound": sound})

    def restore(*_):
        sys.stdout.write(SHOW_CURSOR + RESET + "\n")
        sys.stdout.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, restore)
    signal.signal(signal.SIGTERM, restore)

    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.flush()

    prev_state = None
    eat_min = window_minutes(start, end)
    fast_min = 24 * 60 - eat_min

    try:
        while True:
            now = datetime.now()
            ns = next_occurrence(start, now)
            ne = next_occurrence(end, now)
            is_eating = ne < ns

            next_switch = ne if is_eating else ns
            remaining = (next_switch - now).total_seconds()
            phase_total = (eat_min if is_eating else fast_min) * 60
            progress = (
                max(0.0, min(1.0, (phase_total - remaining) / phase_total))
                if phase_total else 0
            )

            render(now, start, end, is_eating, remaining, next_switch,
                   progress, eat_min, fast_min, sound)

            state = "eating" if is_eating else "fasting"
            if prev_state and prev_state != state:
                if state == "eating":
                    notify("可以开吃了 🍽️",
                           f"进食窗口 {start} – {end}", sound)
                else:
                    notify("该停嘴了 🛑",
                           f"进入 {fast_min // 60} 小时禁食", sound)
            prev_state = state

            time.sleep(1)
    finally:
        sys.stdout.write(SHOW_CURSOR + RESET + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
