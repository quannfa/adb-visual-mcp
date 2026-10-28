from __future__ import annotations

import shlex
import subprocess
import time

from .adb import Adb


def split_args(raw: str | list[str]) -> list[str]:
    if isinstance(raw, str):
        try:
            args = shlex.split(raw)
        except ValueError as exc:
            raise ValueError(f"cannot parse adb arguments: {exc}") from exc
    else:
        args = [str(x) for x in raw]
    if not args:
        raise ValueError("args must contain at least one adb argument")
    return args


def clip(text: str, limit: int) -> tuple[str, bool, int]:
    total = len(text)
    if limit <= 0 or total <= limit:
        return text, False, total
    head = limit // 2
    tail = limit - head
    omitted = total - limit
    clipped = f"{text[:head]}\n...<truncated {omitted} chars>...\n{text[-tail:]}"
    return clipped, True, total


def run_adb_command(
    adb: Adb,
    args: str | list[str],
    device: str | None = None,
    timeout_s: float = 30.0,
    max_output_chars: int = 20000,
) -> dict:
    argv = split_args(args)
    serial = (device or "").strip() or None
    timeout_s = float(timeout_s)
    if not 1 <= timeout_s <= 300:
        raise ValueError("timeout_s must be between 1 and 300")
    max_output_chars = int(max_output_chars)
    if not 100 <= max_output_chars <= 200000:
        raise ValueError("max_output_chars must be between 100 and 200000")

    started = time.monotonic()
    try:
        cp = adb.run_raw(argv, serial=serial, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "timed_out": True,
            "device": serial,
            "args": argv,
            "timeout_s": timeout_s,
            "duration_ms": round((time.monotonic() - started) * 1000),
            "stdout": "",
            "stderr": f"adb command timed out after {timeout_s:g}s",
        }

    duration_ms = round((time.monotonic() - started) * 1000)
    stdout, out_truncated, out_chars = clip(cp.stdout.decode("utf-8", "replace"), max_output_chars)
    stderr, err_truncated, err_chars = clip(cp.stderr.decode("utf-8", "replace"), max_output_chars)
    return {
        "ok": cp.returncode == 0,
        "timed_out": False,
        "device": serial,
        "args": argv,
        "exit_code": cp.returncode,
        "duration_ms": duration_ms,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_chars": out_chars,
        "stderr_chars": err_chars,
        "stdout_truncated": out_truncated,
        "stderr_truncated": err_truncated,
    }
