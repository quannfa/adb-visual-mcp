#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd $(dirname $0)/.. && pwd)
VERSION=${VERSION:-$(grep -m1 '^version = ' $ROOT/pyproject.toml | sed -E 's/.*"([^"]+)".*/\1/')}
ARCH=amd64
DIST=$ROOT/dist
BUILD=$ROOT/.build
VENV=$BUILD/venv
UV=${UV:-uv}
PYTHON=${PYTHON:-/usr/bin/python3}

if [ -z "$VERSION" ]; then echo 'cannot read version from pyproject.toml' >&2; exit 1; fi
echo "==> version $VERSION"

mkdir -p $DIST $BUILD

if [ ! -x $VENV/bin/python ] || [ "${REBUILD_VENV:-0}" = 1 ]; then
  echo '==> creating venv'
  rm -rf $VENV
  $UV venv --python $PYTHON $VENV >/dev/null
  UV_INDEX_URL=${UV_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple} $UV pip install --python $VENV/bin/python $ROOT >/dev/null
fi

build_variant() {
  pkg=$1
  variant=$2
  desc=$3
  debroot=$BUILD/debroot-$variant
  echo "==> building $pkg ($variant)"
  rm -rf $debroot
  install -d $debroot/DEBIAN $debroot/opt/adb-visual-mcp $debroot/usr/bin $debroot/lib/systemd/system $debroot/etc/adb-visual-mcp $debroot/usr/share/doc/$pkg

  cp -a $VENV $debroot/opt/adb-visual-mcp/.venv
  cp -a $ROOT/src $debroot/opt/adb-visual-mcp/src
  cp -a $ROOT/skill $debroot/opt/adb-visual-mcp/skill
  cp $ROOT/README.md $ROOT/LICENSE $debroot/opt/adb-visual-mcp/

  if [ -f $debroot/opt/adb-visual-mcp/.venv/bin/adb-visual-mcp ]; then
    sed -i '1s|.*|#!/opt/adb-visual-mcp/.venv/bin/python|' $debroot/opt/adb-visual-mcp/.venv/bin/adb-visual-mcp
  fi

  find $debroot/opt/adb-visual-mcp -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
  find $debroot/opt/adb-visual-mcp -name '*.pyc' -delete 2>/dev/null || true

  if [ $variant = linux ]; then
    install -m 0755 $ROOT/packaging/wrapper-linux.sh $debroot/usr/bin/adb-visual-mcp
    install -m 0644 $ROOT/packaging/adb-visual-mcp.service $debroot/lib/systemd/system/adb-visual-mcp.service
    install -m 0644 $ROOT/packaging/env-linux $debroot/etc/adb-visual-mcp/env
  else
    install -m 0755 $ROOT/packaging/wrapper-wsl.sh $debroot/usr/bin/adb-visual-mcp
    install -m 0755 $ROOT/packaging/wsl-check.sh $debroot/usr/bin/adb-visual-mcp-wsl-check
    install -m 0644 $ROOT/packaging/adb-visual-mcp.service $debroot/lib/systemd/system/adb-visual-mcp.service
    install -m 0644 $ROOT/packaging/env-wsl $debroot/etc/adb-visual-mcp/env
  fi

  install -m 0755 $ROOT/packaging/postinst $debroot/DEBIAN/postinst
  install -m 0755 $ROOT/packaging/prerm $debroot/DEBIAN/prerm
  install -m 0755 $ROOT/packaging/postrm $debroot/DEBIAN/postrm
  install -m 0644 $ROOT/packaging/conffiles $debroot/DEBIAN/conffiles
  install -m 0644 $ROOT/docs/INSTALL.md $debroot/usr/share/doc/$pkg/INSTALL.md
  install -m 0644 $ROOT/README.md $debroot/usr/share/doc/$pkg/README.md

  cat > $debroot/DEBIAN/control <<CTRL
Package: $pkg
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Depends: python3 (>= 3.10), python3 (<< 3.11), adb | android-tools-adb
Maintainer: quannfa <quannfa@users.noreply.github.com>
Description: $desc
 A small stateless MCP server that exposes screen capture, taps, swipes,
 and keyboard input for Android devices through adb. Visual reasoning
 stays in the calling agent.
CTRL

  dpkg-deb --build --root-owner-group $debroot $DIST/${pkg}_${VERSION}_${ARCH}.deb
}

build_variant adb-visual-mcp linux 'Stateless pure-visual Android control MCP server over adb'
build_variant adb-visual-mcp-wsl wsl 'WSL2 bridge variant of adb-visual-mcp that reuses the Windows adb server'

echo '==> done'
ls -lh $DIST/*.deb
