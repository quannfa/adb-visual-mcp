from __future__ import annotations

import json
import math
from dataclasses import dataclass

from .adb import Adb


@dataclass(frozen=True)
class Size:
    width: int
    height: int


def _bounded_int(value: int, low: int, high: int, label: str) -> int:
    value = int(value)
    if not low <= value <= high:
        raise ValueError(f"{label} must be between {low} and {high}")
    return value


def _tap(adb: Adb, serial: str, x: int, y: int) -> None:
    adb.shell(f"input tap {int(x)} {int(y)}", serial=serial)


def _keyevent(adb: Adb, serial: str, code: str) -> None:
    adb.shell(f"input keyevent {code}", serial=serial)


def _swipe(adb: Adb, serial: str, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None:
    duration_ms = _bounded_int(duration_ms, 0, 10000, "duration_ms")
    adb.shell(f"input swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {duration_ms}", serial=serial)


KEY_ALIASES = {
    "enter": "KEYCODE_ENTER",
    "return": "KEYCODE_ENTER",
    "tab": "KEYCODE_TAB",
    "esc": "KEYCODE_ESCAPE",
    "escape": "KEYCODE_ESCAPE",
    "backspace": "KEYCODE_DEL",
    "delete": "KEYCODE_FORWARD_DEL",
    "home": "KEYCODE_HOME",
    "end": "KEYCODE_MOVE_END",
    "back": "KEYCODE_BACK",
    "menu": "KEYCODE_MENU",
    "power": "KEYCODE_POWER",
    "volume_up": "KEYCODE_VOLUME_UP",
    "volume_down": "KEYCODE_VOLUME_DOWN",
    "volume_mute": "KEYCODE_VOLUME_MUTE",
    "wakeup": "KEYCODE_WAKEUP",
    "sleep": "KEYCODE_SLEEP",
    "space": "KEYCODE_SPACE",
    "left": "KEYCODE_DPAD_LEFT",
    "right": "KEYCODE_DPAD_RIGHT",
    "up": "KEYCODE_DPAD_UP",
    "down": "KEYCODE_DPAD_DOWN",
    "pageup": "KEYCODE_PAGE_UP",
    "pagedown": "KEYCODE_PAGE_DOWN",
    "app_switch": "KEYCODE_APP_SWITCH",
    "recents": "KEYCODE_APP_SWITCH",
    "search": "KEYCODE_SEARCH",
    "camera": "KEYCODE_CAMERA",
    "play_pause": "KEYCODE_MEDIA_PLAY_PAUSE",
    "next": "KEYCODE_MEDIA_NEXT",
    "previous": "KEYCODE_MEDIA_PREVIOUS",
}


def normalize_key(key: str) -> str:
    raw = str(key).strip()
    lower = raw.lower()
    if lower in KEY_ALIASES:
        return KEY_ALIASES[lower]
    if re_fullmatch_keycode(raw):
        return raw.upper()
    if len(raw) == 1 and raw.isdigit():
        return f"KEYCODE_{raw}"
    if len(raw) == 1 and raw.isalpha():
        return f"KEYCODE_{raw.upper()}"
    if lower.startswith("keycode_"):
        return lower.upper()
    raise ValueError(f"unsupported Android key: {key}")


def re_fullmatch_keycode(text: str) -> bool:
    import re

    return re.fullmatch(r"(?i)keycode_[a-z0-9_]+", text) is not None


def type_text(adb: Adb, serial: str, text: str) -> None:
    if text == "":
        return
    escaped = text.replace(" ", "%s")
    adb.shell(f"input text {adb.quote(escaped)}", serial=serial)


def key(adb: Adb, serial: str, names: str | list[str]) -> None:
    if isinstance(names, str):
        names = [names]
    if not names:
        raise ValueError("keys must contain at least one key")
    codes = [normalize_key(n) for n in names]
    adb.shell("input keyevent " + " ".join(codes), serial=serial)


def long_press(adb: Adb, serial: str, x: int, y: int, duration_ms: int = 800) -> None:
    _swipe(adb, serial, x, y, x, y, _bounded_int(duration_ms, 1, 10000, "duration_ms"))


def click(adb: Adb, serial: str, x: int, y: int, count: int = 1) -> dict:
    count = _bounded_int(count, 1, 10, "count")
    for _ in range(count):
        _tap(adb, serial, x, y)
    return {"ok": True, "x": int(x), "y": int(y), "count": count}


def mouse(adb: Adb, serial: str, action: str, **kw) -> dict:
    action = str(action).lower()
    if action == "move":
        raise ValueError("Android has no pointer hover; use click, swipe, or drag")
    if action == "scroll":
        delta = int(kw.get("delta") or 0)
        if delta == 0:
            return {"ok": True, "action": "scroll", "delta": 0}
        width, height = adb.screen_size(serial)
        cx = width // 2
        span = max(200, height // 4)
        if delta < 0:
            x1, y1, x2, y2 = cx, int(height * 0.30), cx, int(height * 0.30) + span
        else:
            x1, y1, x2, y2 = cx, int(height * 0.70), cx, int(height * 0.70) - span
        steps = max(1, min(20, math.ceil(abs(delta) / 120)))
        for _ in range(steps):
            _swipe(adb, serial, x1, y1, x2, y2, 250)
        return {"ok": True, "action": "scroll", "delta": delta, "steps": steps}
    if action == "drag":
        x, y = int(kw["x"]), int(kw["y"])
        to_x, to_y = int(kw["to_x"]), int(kw["to_y"])
        duration_ms = int(kw.get("duration_ms") or 300)
        _swipe(adb, serial, x, y, to_x, to_y, duration_ms)
        return {"ok": True, "action": "drag", "x": x, "y": y, "to_x": to_x, "to_y": to_y}
    raise ValueError("action must be scroll or drag")


def keyboard(adb: Adb, serial: str, action: str, text: str | None = None, keys: str | list[str] | None = None) -> dict:
    action = str(action).lower()
    if action == "type":
        if text is None:
            raise ValueError("text is required when action=type")
        type_text(adb, serial, text)
        return {"ok": True, "action": "type", "chars": len(text)}
    if action in ("press", "hotkey"):
        if keys is None:
            raise ValueError("keys is required when action=press|hotkey")
        key(adb, serial, keys)
        return {"ok": True, "action": action, "keys": keys}
    raise ValueError("action must be type, press, or hotkey")


def to_json(value) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
