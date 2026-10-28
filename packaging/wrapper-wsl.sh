#!/usr/bin/env bash
# adb-visual-mcp launcher (WSL2 bridge variant).
# Reuses the Windows-side adb server, so a USB-attached phone is visible
# inside WSL without usbipd. See /usr/share/doc/adb-visual-mcp-wsl/INSTALL.md.
set -euo pipefail
BASE=/opt/adb-visual-mcp
ENV_FILE=/etc/adb-visual-mcp/env

if [ -r "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

: "${ADB_SERVER_SOCKET:=tcp:127.0.0.1:5037}"
: "${ADB_VISUAL_MCP_TRANSPORT:=streamable-http}"
: "${ADB_VISUAL_MCP_HOST:=0.0.0.0}"
: "${ADB_VISUAL_MCP_PORT:=8799}"
: "${ADB_VISUAL_MCP_PATH:=/mcp}"
export ADB_SERVER_SOCKET ADB_VISUAL_MCP_TRANSPORT ADB_VISUAL_MCP_HOST ADB_VISUAL_MCP_PORT ADB_VISUAL_MCP_PATH

if [ -z "${ADB_VISUAL_MCP_ADB:-}" ]; then
  if [ -x /usr/bin/adb ]; then
    export ADB_VISUAL_MCP_ADB=/usr/bin/adb
  else
    for p in /mnt/c/Users/*/pt-win/platform-tools/adb.exe /mnt/c/Users/*/AppData/Local/Android/Sdk/platform-tools/adb.exe /mnt/c/platform-tools/adb.exe; do
      if [ -x "$p" ]; then export ADB_VISUAL_MCP_ADB=$p; break; fi
    done
  fi
fi

PY=$BASE/.venv/bin/python
if [ ! -x "$PY" ]; then
  echo "adb-visual-mcp: venv python missing at $PY" >&2
  exit 1
fi

exec "$PY" -m adb_visual_mcp.server \
  --transport "$ADB_VISUAL_MCP_TRANSPORT" \
  --host "$ADB_VISUAL_MCP_HOST" \
  --port "$ADB_VISUAL_MCP_PORT" \
  --path "$ADB_VISUAL_MCP_PATH" "$@"
