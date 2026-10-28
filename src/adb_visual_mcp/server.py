from __future__ import annotations

import argparse
import os
from typing import Annotated, Literal

from mcp.server import MCPServer
from mcp.types import CallToolResult, ImageContent, TextContent
from pydantic import Field

from . import __version__
from .actions import click as do_click
from .actions import keyboard as do_keyboard
from .actions import mouse as do_mouse
from .actions import to_json
from .adb import Adb, AdbError
from .config import Settings
from .imaging import overlay_grid, png_b64
from .runner import run_adb_command

VERSION = __version__
GridSize = Annotated[int, Field(ge=0, le=200)]
ClickCount = Annotated[int, Field(ge=1, le=10)]
DragDuration = Annotated[int, Field(ge=0, le=10000)]
CommandTimeout = Annotated[float, Field(ge=1, le=300)]
OutputLimit = Annotated[int, Field(ge=100, le=200000)]

mcp = MCPServer(
    name="adb-visual-mcp",
    version=VERSION,
    instructions=(
        "Stateless pure-visual Android control over adb shell. Observe with "
        "screenshot, interact with click/mouse/keyboard, then screenshot again "
        "to verify. No UI tree, OCR, or element cache is used."
    ),
)


def _adb(device: str | None) -> tuple[Adb, str]:
    adb = Adb(Settings())
    selected = adb.resolve(device or None)
    return adb, selected.serial


def _text(value) -> TextContent:
    return TextContent(type="text", text=to_json(value))


def _result(blocks: list[TextContent | ImageContent]) -> CallToolResult:
    return CallToolResult(content=blocks)


@mcp.tool(structured_output=False)
def devices() -> CallToolResult:
    """List Android devices known to adb, including readiness and model."""
    adb = Adb(Settings())
    rows = [
        {
            "serial": d.serial,
            "state": d.state,
            "model": d.model,
            "product": d.product,
            "transport_id": d.transport_id,
        }
        for d in adb.devices()
    ]
    return _result([_text({"ok": True, "devices": rows})])


@mcp.tool(structured_output=False)
def adb_command(
    args: str | list[str],
    device: str | None = None,
    timeout_s: CommandTimeout = 30,
    max_output_chars: OutputLimit = 20000,
) -> CallToolResult:
    """Run an arbitrary adb command and return exit code, stdout, and stderr.

    `args` is the adb argument list, for example ["shell", "getprop",
    "ro.product.model"] or "shell pm list packages". Without `device` the
    command runs without `-s`, so global commands such as `devices` or
    `version` work; pass a serial for device-scoped commands.
    """
    adb = Adb(Settings())
    return _result([
        _text(
            run_adb_command(
                adb,
                args,
                device=device,
                timeout_s=timeout_s,
                max_output_chars=max_output_chars,
            )
        )
    ])


@mcp.tool(structured_output=False)
def screenshot(
    device: str | None = None,
    grid_rows: GridSize = 0,
    grid_cols: GridSize = 0,
) -> CallToolResult:
    """Capture the full Android screen, optionally with a uniform visual grid."""
    adb, serial = _adb(device)
    png = adb.capture_png(serial)
    png, width, height = overlay_grid(png, grid_rows, grid_cols)
    density = adb.density(serial)
    meta = {
        "ok": True,
        "device": serial,
        "width": width,
        "height": height,
        "density": density,
        "grid_rows": grid_rows,
        "grid_cols": grid_cols,
    }
    return _result([
        _text(meta),
        ImageContent(type="image", data=png_b64(png), mime_type="image/png"),
    ])


@mcp.tool(structured_output=False)
def click(
    x: int,
    y: int,
    device: str | None = None,
    button: Literal["left", "right", "middle"] = "left",
    count: ClickCount = 1,
) -> CallToolResult:
    """Tap an absolute screen coordinate. Right/middle map to a long press."""
    adb, serial = _adb(device)
    if button == "left":
        result = do_click(adb, serial, x, y, count)
    else:
        from .actions import long_press

        long_press(adb, serial, x, y, 800)
        result = {"ok": True, "x": x, "y": y, "button": button, "long_press": True}
    result["device"] = serial
    return _result([_text(result)])


@mcp.tool(structured_output=False)
def mouse(
    action: Literal["scroll", "drag"],
    device: str | None = None,
    x: int | None = None,
    y: int | None = None,
    to_x: int | None = None,
    to_y: int | None = None,
    delta: int | None = None,
    duration_ms: DragDuration = 300,
) -> CallToolResult:
    """Scroll the screen or drag between absolute coordinates."""
    adb, serial = _adb(device)
    if action == "drag":
        if None in (x, y, to_x, to_y):
            raise ValueError("drag requires x, y, to_x, and to_y")
        result = do_mouse(adb, serial, action, x=x, y=y, to_x=to_x, to_y=to_y, duration_ms=duration_ms)
    else:
        result = do_mouse(adb, serial, action, delta=delta or 0)
    result["device"] = serial
    return _result([_text(result)])


@mcp.tool(structured_output=False)
def keyboard(
    action: Literal["type", "press", "hotkey"],
    device: str | None = None,
    text: str | None = None,
    keys: str | list[str] | None = None,
) -> CallToolResult:
    """Type text, press one key, or send a key sequence to the focused app."""
    adb, serial = _adb(device)
    result = do_keyboard(adb, serial, action, text=text, keys=keys)
    result["device"] = serial
    return _result([_text(result)])


def main() -> None:
    ap = argparse.ArgumentParser(description="Stateless pure-visual Android MCP over adb")
    ap.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "http"],
        default=os.environ.get("ADB_VISUAL_MCP_TRANSPORT", "stdio"),
    )
    ap.add_argument("--host", default=os.environ.get("ADB_VISUAL_MCP_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("ADB_VISUAL_MCP_PORT", "8000")))
    ap.add_argument("--path", default=os.environ.get("ADB_VISUAL_MCP_PATH", "/mcp"))
    ap.add_argument("--version", action="store_true")
    ns = ap.parse_args()
    if ns.version:
        print(VERSION)
        return
    transport = "streamable-http" if ns.transport == "http" else ns.transport
    if transport == "stdio":
        mcp.run(transport="stdio")
        return
    mcp.run(
        transport="streamable-http",
        host=ns.host,
        port=ns.port,
        streamable_http_path=ns.path,
        stateless_http=True,
        json_response=True,
    )


if __name__ == "__main__":
    main()
