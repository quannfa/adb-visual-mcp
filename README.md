# adb-visual-mcp

A small, stateless, pure-visual MCP server for Android devices. It exposes only the I/O needed to operate an emulator or phone: screen capture, taps, swipes, and keyboard input. Visual reasoning stays in the calling agent.

The server talks to Android through `adb shell` and `adb exec-out`; it does not use the accessibility tree, OCR, Appium, or a cached UI model.

## Tools

- `devices()` lists devices and readiness.
- `adb_command(args, device?, timeout_s?, max_output_chars?)` runs any adb command and returns exit code, stdout, and stderr.
- `screenshot(device?, grid_rows?, grid_cols?)` returns JSON geometry plus a PNG. The optional grid is only a visual reference overlay.
- `click(x, y, device?, button?, count?)` taps absolute screen coordinates. Right and middle map to a long press.
- `mouse(action, device?, ...)` supports `scroll` and `drag` (swipe).
- `keyboard(action, device?, text?, keys?)` types text or sends Android key events.

The visual and input tools accept an optional `device` serial. With no argument, exactly one ready device must be present. The server never caches the selected device or current screen.

`adb_command` is the escape hatch for everything the typed tools do not cover (installing APKs, reading properties, package management). Its `args` is either an argument list or a single string that is split like a shell line. Without `device` it runs without `-s`, so global commands such as `devices` and `version` work. Output is capped per stream; long output keeps the head and tail and reports how many characters were dropped.

```json
{
  "args": ["shell", "pm", "list", "packages"],
  "device": "emulator-5554",
  "timeout_s": 30,
  "max_output_chars": 20000
}
```

## Install

Requires Python 3.10+, `adb`, and a running Android device or emulator.

```bash
uv sync
uv run adb-visual-mcp --version
```

Set the adb path when it is not on `PATH`:

```bash
export ADB_VISUAL_MCP_ADB=/data/zqf/android-sdk/platform-tools/adb
export ADB_VISUAL_MCP_DEVICE=emulator-5554
```

## Run

stdio, for an MCP client that launches the process:

```bash
uv run adb-visual-mcp
```

Streamable HTTP:

```bash
uv run adb-visual-mcp --transport streamable-http --host 127.0.0.1 --port 8000 --path /mcp
```

## Interaction model

```text
screenshot -> visual reasoning -> click/mouse/keyboard -> screenshot to verify
```

The server does not identify buttons or choose coordinates. Callers should use a grid overlay when fine positioning is needed and should not invent coordinates for visually uncertain targets.

## Notes

`keyboard type` uses `adb shell input text`; it is intended for ASCII text. For non-ASCII input, use the device's own IME or a dedicated helper app. `mouse move` is intentionally unsupported because Android touchscreens have no hover pointer.

## Development

```bash
uv run pytest
uv run python tests/smoke.py
```

## Install from .deb

Release packages are attached to GitHub releases:

- `adb-visual-mcp_<version>_amd64.deb` for a normal Linux host
- `adb-visual-mcp-wsl_<version>_amd64.deb` for WSL2, reusing the Windows adb server

```bash
sudo apt install ./adb-visual-mcp_<version>_amd64.deb
```

The package installs a `systemd` service and starts it on port `8799` at
`/mcp`. See [docs/INSTALL.md](docs/INSTALL.md) for the WSL2 bridge, the
configuration file at `/etc/adb-visual-mcp/env`, and how to disable or move
the service.

## WSL2 bridge (Windows USB device)

On WSL2 the reliable path is to let Windows own the USB device and reuse its
adb server from WSL, instead of attaching USB through `usbipd`:

```powershell
C:\Users\<you>\pt-win\platform-tools\adb.exe devices -l
```

Then install `adb-visual-mcp-wsl` in WSL and run:

```bash
adb-visual-mcp-wsl-check
sudo systemctl enable --now adb-visual-mcp
```

The launcher sets `ADB_SERVER_SOCKET=tcp:127.0.0.1:5037`, so `127.0.0.1`
inside WSL must reach the Windows loopback (mirrored networking). Override
`ADB_SERVER_SOCKET` or `ADB_VISUAL_MCP_ADB` in `/etc/adb-visual-mcp/env` if
needed.

## Build the packages

```bash
./packaging/build-deb.sh
ls dist/*.deb
```

The script creates a self-contained venv with `uv` and packs it into the
`.deb`, so installation does not need network access. Use
`REBUILD_VENV=1` to rebuild the venv and `VERSION=x.y.z` to override the
version.
