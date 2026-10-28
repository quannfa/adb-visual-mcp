#!/usr/bin/env bash
# adb-visual-mcp launcher (Linux variant).
set -euo pipefail
BASE=/opt/adb-visual-mcp
ENV_FILE=/etc/adb-visual-mcp/env

if [ -r "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

: "${ADB_VISUAL_MCP_TRANSPORT:=streamable-http}"
: "${ADB_VISUAL_MCP_HOST:=127.0.0.1}"
: "${ADB_VISUAL_MCP_PORT:=8799}"
: "${ADB_VISUAL_MCP_PATH:=/mcp}"
export ADB_VISUAL_MCP_TRANSPORT ADB_VISUAL_MCP_HOST ADB_VISUAL_MCP_PORT ADB_VISUAL_MCP_PATH

if [ -z "${ADB_VISUAL_MCP_ADB:-}" ]; then
  if command -v adb >/dev/null 2>&1; then
    export ADB_VISUAL_MCP_ADB=$(command -v adb)
  else
    for p in /usr/lib/android-sdk/platform-tools/adb /opt/android-sdk/platform-tools/adb "$HOME/Android/Sdk/platform-tools/adb"; do
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
