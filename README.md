# adb-visual-mcp

A small, stateless, pure-visual MCP server for Android devices. It exposes only the I/O needed to operate an emulator or phone: screen capture, taps, swipes, and keyboard input. Visual reasoning stays in the calling agent.

The server talks to Android through `adb shell` and `adb exec-out`; it does not use the accessibility tree, OCR, Appium, or a cached UI model.

## Tools

- `devices()` lists devices and readiness.
- `screenshot(device?, grid_rows?, grid_cols?)` returns JSON geometry plus a PNG. The optional grid is only a visual reference overlay.
- `click(x, y, device?, button?, count?)` taps absolute screen coordinates. Right and middle map to a long press.
- `mouse(action, device?, ...)` supports `scroll` and `drag` (swipe).
- `keyboard(action, device?, text?, keys?)` types text or sends Android key events.

Every tool accepts an optional `device` serial. With no argument, exactly one ready device must be present. The server never caches the selected device or current screen.

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
uv run python tests/smoke.py "uv run adb-visual-mcp"
```
