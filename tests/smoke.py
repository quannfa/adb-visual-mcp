#!/usr/bin/env python3
import argparse
import json
import shlex
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("command", nargs="?", default="uv run adb-visual-mcp")
ap.add_argument("args", nargs="*")
ns = ap.parse_args()
p = subprocess.Popen(shlex.split(ns.command) + ns.args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)


def rpc(i, method, params=None):
    p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": params or {}}) + "\n")
    p.stdin.flush()
    return json.loads(p.stdout.readline())


r = rpc(1, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "smoke", "version": "1"}})
assert r["result"]["serverInfo"]["name"] == "adb-visual-mcp", r
p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}) + "\n")
p.stdin.flush()
r = rpc(2, "tools/list")
assert [t["name"] for t in r["result"]["tools"]] == [
    "devices", "adb_command", "screenshot", "click", "mouse", "keyboard"
], r
print("OK tools/list")
p.terminate()
