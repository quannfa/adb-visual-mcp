# adb-visual-mcp installation

Two Debian packages are published for each release:

| Package | Use it on | Notes |
| --- | --- | --- |
| `adb-visual-mcp` | a normal Linux host | the host owns the USB connection to the phone |
| `adb-visual-mcp-wsl` | WSL2 inside Windows | reuses the Windows `adb.exe` server, so a phone plugged into Windows is visible in WSL without `usbipd` |

Both packages install the same program to `/opt/adb-visual-mcp`, a launcher to
`/usr/bin/adb-visual-mcp`, a systemd unit `adb-visual-mcp.service`, and a
config file `/etc/adb-visual-mcp/env`. Only one of the two packages should be
installed on a given machine.

Install with apt so package dependencies are resolved:

```bash
sudo apt install ./adb-visual-mcp_<version>_amd64.deb
# or, on WSL2:
sudo apt install ./adb-visual-mcp-wsl_<version>_amd64.deb
```

`adb` must be available. The package depends on `adb` (or
`android-tools-adb`) and Python 3.10+. To check that the service works:

```bash
systemctl status adb-visual-mcp --no-pager
journalctl -u adb-visual-mcp -n 30 --no-pager
adb devices -l
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8799/mcp
```

The last check returns `406` on a plain GET, which means the MCP endpoint is
up and only rejects the missing MCP headers. A `000` means the service is not
listening.

## Linux host

The service starts automatically after install and listens on
`127.0.0.1:8799` at `/mcp`. It serves the streamable HTTP transport. To use
stdio instead, set `ADB_VISUAL_MCP_TRANSPORT=stdio` in
`/etc/adb-visual-mcp/env` and point your MCP client at the `adb-visual-mcp`
binary directly.

Connect the phone with USB debugging enabled and accept the RSA prompt. When
more than one device is attached, pin the serial:

```bash
sudoedit /etc/adb-visual-mcp/env
# ADB_VISUAL_MCP_DEVICE=emulator-5554
sudo systemctl restart adb-visual-mcp
```

If adb is not on `PATH`, set `ADB_VISUAL_MCP_ADB=/path/to/adb` in the same
file. The launcher falls back to `/usr/lib/android-sdk`, `/opt/android-sdk`,
and `~/Android/Sdk`.

## WSL2 bridge

This variant does not own USB devices itself. It talks to the adb server that
runs on Windows, which is the reliable path when `usbipd` and `vhci_hcd` hang
during device enumeration.

1. Put Windows platform-tools somewhere stable, for example
   `C:\Users\<you>\pt-win\platform-tools\adb.exe`.
2. Start the Windows adb server and authorize the phone:

   ```powershell
   C:\Users\<you>\pt-win\platform-tools\adb.exe devices -l
   C:\Users\<you>\pt-win\platform-tools\adb.exe -s <serial> shell getprop ro.product.model
   ```

   Accept the RSA prompt on the phone. `device` is the state you want;
   `unauthorized` means the prompt was not accepted.
3. Install the WSL package and check the bridge:

   ```bash
   adb-visual-mcp-wsl-check
   ```

   It prints the adb version and the device list as seen through
   `ADB_SERVER_SOCKET`.
4. Start the service:

   ```bash
   sudo systemctl enable --now adb-visual-mcp
   ```

The WSL package listens on `0.0.0.0:8799` so that other LAN hosts can reach
the endpoint. Change `ADB_VISUAL_MCP_HOST` to `127.0.0.1` in
`/etc/adb-visual-mcp/env` for local-only access.

WSL uses mirrored networking here, so `127.0.0.1:5037` inside WSL is the same
loopback as Windows. If your WSL uses NAT networking, point
`ADB_SERVER_SOCKET` at the Windows host address instead and make sure the
Windows firewall allows port 5037. The `/usr/bin/adb` client from Ubuntu works
against the Windows adb 37 server; any adb client 28+ is fine.

## Managing the service

```bash
sudo systemctl enable adb-visual-mcp     # start on boot
sudo systemctl start adb-visual-mcp
sudo systemctl restart adb-visual-mcp    # after editing the env file
sudo systemctl disable adb-visual-mcp
```

The unit runs as root because it may need to talk to adb and bind a port. Edit
`/etc/adb-visual-mcp/env` for settings; the file is registered as a conffile,
so package upgrades keep your changes and put new defaults in `.dpkg-dist`.

Environment variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `ADB_VISUAL_MCP_TRANSPORT` | `streamable-http` | `stdio` or `streamable-http` |
| `ADB_VISUAL_MCP_HOST` | `127.0.0.1` (Linux), `0.0.0.0` (WSL) | HTTP bind address |
| `ADB_VISUAL_MCP_PORT` | `8799` | HTTP port |
| `ADB_VISUAL_MCP_PATH` | `/mcp` | HTTP path |
| `ADB_VISUAL_MCP_ADB` | auto | adb executable |
| `ADB_VISUAL_MCP_DEVICE` | auto | default device serial |
| `ADB_SERVER_SOCKET` | `tcp:127.0.0.1:5037` (WSL only) | Windows adb server |

## Connecting an MCP client

For streamable HTTP, use `http://<host>:8799/mcp` as the server URL. For a
mcptun backend, point it at the same URL. A local client can also launch the
stdio transport directly:

```json
{
  "mcpServers": {
    "android": {
      "command": "/usr/bin/adb-visual-mcp",
      "env": { "ADB_VISUAL_MCP_TRANSPORT": "stdio" }
    }
  }
}
```

## Uninstall

```bash
sudo apt remove adb-visual-mcp        # keeps /etc/adb-visual-mcp
sudo apt purge adb-visual-mcp         # also removes /opt and /etc
```

## Building the packages

```bash
./packaging/build-deb.sh
ls dist/*.deb
```

The script builds a venv with `uv`, installs the project into it, and packs
the venv into the deb. Installation therefore does not need network access.
The build host must run Python 3.10+; the venv symlinks `/usr/bin/python3`, so
the target host must have a compatible `python3`. Set `REBUILD_VENV=1` to
force a fresh venv, and `VERSION=x.y.z` to override the version read from
`pyproject.toml`.
