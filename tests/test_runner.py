import subprocess

import pytest

from adb_visual_mcp.runner import clip, run_adb_command, split_args


class FakeAdb:
    def __init__(self, stdout=b"hello\n", stderr=b"", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.calls = []

    def run_raw(self, args, serial=None, timeout=None):
        self.calls.append({"args": args, "serial": serial, "timeout": timeout})
        if isinstance(self.stdout, Exception):
            raise self.stdout
        return subprocess.CompletedProcess(args, self.returncode, self.stdout, self.stderr)


def test_split_args_accepts_string_and_list():
    assert split_args("shell getprop ro.product.model") == ["shell", "getprop", "ro.product.model"]
    assert split_args(["shell", "wm", "size"]) == ["shell", "wm", "size"]
    with pytest.raises(ValueError):
        split_args([])
    with pytest.raises(ValueError):
        split_args("shell 'unterminated")


def test_clip_keeps_head_and_tail():
    text = "a" * 500
    clipped, truncated, total = clip(text, 100)
    assert truncated and total == 500
    assert clipped.startswith("a" * 50) and clipped.endswith("a" * 50)
    assert "truncated 400 chars" in clipped
    assert clip("short", 100) == ("short", False, 5)


def test_run_adb_command_reports_success_and_device():
    adb = FakeAdb(stdout=b"Pixel\n")
    result = run_adb_command(adb, ["shell", "getprop", "ro.product.model"], device="emulator-5554")
    assert result["ok"] and result["exit_code"] == 0
    assert result["stdout"] == "Pixel\n"
    assert result["device"] == "emulator-5554"
    assert adb.calls == [{
        "args": ["shell", "getprop", "ro.product.model"],
        "serial": "emulator-5554",
        "timeout": 30.0,
    }]


def test_run_adb_command_without_device_is_global():
    adb = FakeAdb(stdout=b"List of devices attached\n")
    result = run_adb_command(adb, "devices -l")
    assert result["ok"]
    assert result["device"] is None
    assert adb.calls[0]["serial"] is None


def test_run_adb_command_surfaces_failure_and_timeout():
    failed = FakeAdb(stderr=b"error: device offline\n", returncode=1)
    result = run_adb_command(failed, "shell true", device="x")
    assert not result["ok"] and result["exit_code"] == 1
    assert "device offline" in result["stderr"]

    slow = FakeAdb(stdout=subprocess.TimeoutExpired(["adb"], 1))
    result = run_adb_command(slow, "shell sleep 100", timeout_s=2)
    assert result["timed_out"] and not result["ok"]


def test_run_adb_command_validates_bounds():
    adb = FakeAdb()
    with pytest.raises(ValueError):
        run_adb_command(adb, "devices", timeout_s=0)
    with pytest.raises(ValueError):
        run_adb_command(adb, "devices", max_output_chars=10)
