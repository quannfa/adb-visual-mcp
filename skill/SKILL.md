# Android Visual Control

Use the adb-visual-mcp server as a stateless full-screen Android I/O device.

- Start with `screenshot` to inspect the current screen.
- Use `grid_rows` and `grid_cols` when positional reference helps.
- Never invent a tap coordinate when the target is visually uncertain.
- Use `click`, `mouse`, and `keyboard` only after the target is visually clear.
- After consequential actions, take another screenshot and verify the visible result.
- Pass `device` explicitly when more than one Android device is connected.
- Reach for `adb_command` when a task needs something the visual tools do not cover, such as `pm install`, `getprop`, or `dumpsys`. Prefer the typed tools for taps, swipes, typing, and screenshots.

The MCP does not crop, OCR, inspect the UI tree, or remember prior screens. Planning and visual localization belong to the calling agent.
