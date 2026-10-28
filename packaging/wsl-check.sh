#!/usr/bin/env bash
# Diagnose the WSL -> Windows adb bridge.
set -euo pipefail
if [ -r /etc/adb-visual-mcp/env ]; then
  set -a
  . /etc/adb-visual-mcp/env
  set +a
fi
export ADB_SERVER_SOCKET=${ADB_SERVER_SOCKET:-tcp:127.0.0.1:5037}
ADB=${ADB_VISUAL_MCP_ADB:-/usr/bin/adb}

printf 'ADB_SERVER_SOCKET=%s\n' "$ADB_SERVER_SOCKET"
printf 'ADB=%s\n' "$ADB"
if [ ! -x "$ADB" ]; then
  echo "adb client not found: $ADB" >&2
  echo "Install the adb package or set ADB_VISUAL_MCP_ADB in /etc/adb-visual-mcp/env." >&2
  exit 1
fi
"$ADB" version | head -2
"$ADB" devices -l
