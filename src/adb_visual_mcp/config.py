from __future__ import annotations

import os
import shutil
from dataclasses import dataclass


def _find_adb() -> str:
    explicit = os.environ.get("ADB_VISUAL_MCP_ADB")
    if explicit:
        return explicit
    found = shutil.which("adb")
    if found:
        return found
    for candidate in (
        os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
        "/data/zqf/android-sdk/platform-tools/adb",
        "/usr/lib/android-sdk/platform-tools/adb",
    ):
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return "adb"


@dataclass(frozen=True)
class Settings:
    adb: str = os.environ.get("ADB_VISUAL_MCP_ADB") or _find_adb()
    device: str = os.environ.get("ADB_VISUAL_MCP_DEVICE", "")
    command_timeout: float = float(os.environ.get("ADB_VISUAL_MCP_TIMEOUT", "30"))
    screenshot_timeout: float = float(os.environ.get("ADB_VISUAL_MCP_SCREENSHOT_TIMEOUT", "45"))
