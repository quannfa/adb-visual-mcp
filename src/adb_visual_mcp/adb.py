from __future__ import annotations

import re
import shlex
import subprocess
from dataclasses import dataclass

from .config import Settings


class AdbError(RuntimeError):
    pass


@dataclass(frozen=True)
class Device:
    serial: str
    state: str
    model: str | None = None
    product: str | None = None
    transport_id: str | None = None


def _parse_devices(output: str) -> list[Device]:
    devices: list[Device] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices") or line.startswith("*"):
            continue
        fields = line.split()
        if len(fields) < 2:
            continue
        serial, state = fields[0], fields[1]
        attrs = dict(f.split(":", 1) for f in fields[2:] if ":" in f)
        devices.append(
            Device(
                serial=serial,
                state=state,
                model=attrs.get("model"),
                product=attrs.get("product"),
                transport_id=attrs.get("transport_id"),
            )
        )
    return devices


def parse_size(dump: str) -> tuple[int, int]:
    physical = re.search(r"Physical size:\s*(\d+)x(\d+)", dump)
    override = re.search(r"Override size:\s*(\d+)x(\d+)", dump)
    match = override or physical
    if not match:
        raise AdbError("could not parse display size from adb output")
    return int(match.group(1)), int(match.group(2))


def parse_density(dump: str) -> int | None:
    override = re.search(r"Override density:\s*(\d+)", dump)
    physical = re.search(r"Physical density:\s*(\d+)", dump)
    match = override or physical
    return int(match.group(1)) if match else None


class Adb:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    @property
    def adb(self) -> str:
        return self.settings.adb

    def _cmd(self, args: list[str], serial: str | None = None) -> list[str]:
        target = serial if serial is not None else self.settings.device
        if target:
            return [self.adb, "-s", target, *args]
        return [self.adb, *args]

    def run(
        self,
        args: list[str],
        serial: str | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[bytes]:
        cmd = self._cmd(args, serial)
        try:
            cp = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout or self.settings.command_timeout,
            )
        except FileNotFoundError as exc:
            raise AdbError(f"adb executable not found: {self.adb}") from exc
        except subprocess.TimeoutExpired as exc:
            raise AdbError(f"adb command timed out after {timeout or self.settings.command_timeout}s") from exc
        if check and cp.returncode != 0:
            err = cp.stderr.decode("utf-8", "replace").strip()
            raise AdbError(err or f"adb exited with {cp.returncode}")
        return cp

    def text(
        self,
        args: list[str],
        serial: str | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> str:
        cp = self.run(args, serial=serial, timeout=timeout, check=check)
        return cp.stdout.decode("utf-8", "replace").strip()

    def shell(
        self,
        command: str,
        serial: str | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> str:
        return self.text(["shell", command], serial=serial, timeout=timeout, check=check)

    def devices(self) -> list[Device]:
        return _parse_devices(self.text(["devices", "-l"]))

    def resolve(self, requested: str | None = None) -> Device:
        devices = self.devices()
        ready = [d for d in devices if d.state == "device"]
        if requested:
            for d in devices:
                if d.serial == requested:
                    if d.state != "device":
                        raise AdbError(f"device {requested} is {d.state}, not ready")
                    return d
            raise AdbError(f"device not found: {requested}")
        if len(ready) == 1:
            return ready[0]
        if not ready:
            unauthorized = [d.serial for d in devices if d.state == "unauthorized"]
            hint = f" (unauthorized: {', '.join(unauthorized)})" if unauthorized else ""
            raise AdbError(f"no ready Android device{hint}; start an emulator or connect over adb")
        names = ", ".join(d.serial for d in ready)
        raise AdbError(f"multiple ready devices ({names}); set ADB_VISUAL_MCP_DEVICE")

    def capture_png(self, serial: str) -> bytes:
        cp = self.run(
            ["exec-out", "screencap", "-p"],
            serial=serial,
            timeout=self.settings.screenshot_timeout,
        )
        data = cp.stdout
        if not data.startswith(b"\x89PNG"):
            err = cp.stderr.decode("utf-8", "replace").strip()
            raise AdbError(f"screencap did not return PNG data: {err or data[:80]!r}")
        return data

    def screen_size(self, serial: str) -> tuple[int, int]:
        return parse_size(self.shell("wm size", serial=serial))

    def density(self, serial: str) -> int | None:
        return parse_density(self.shell("wm density", serial=serial))

    @staticmethod
    def quote(text: str) -> str:
        return shlex.quote(text)
