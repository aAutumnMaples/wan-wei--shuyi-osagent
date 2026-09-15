#!/bin/bash
# Copyright (c) 2026 QianChang-official
#
# 宛委·枢忆 is licensed under Mulan PSL v2.
# You can use this software according to the terms of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
# http://license.coscl.org.cn/MulanPSL2
#
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

# build-ky10-rpm.sh — 在麒麟（V10 SP3 或 V11）上按《银河麒麟高级服务器操作系统
# RPM 包打包规范》V1.7 出 .ky10 RPM 包。
#
# 流程（复刻 desktop/scripts/build-linux.sh 的 staging 纪律，产物进 rpmbuild 树）：
#   1. 拒绝脏树（已跟踪文件未提交）——staging 从 HEAD 导出，脏树会静默丢改动
#   2. git archive 导出干净树 → 应用 release-clean.patch（剔除手机伴侣）
#   3. 前端 npm ci && build；desktop npm ci；electron-builder --dir 出 linux-unpacked
#   4. 组装 rpmbuild 输入：payload tarball（unpacked 树 + ky10 配套件 + 图标）
#   5. rpmbuild -bb SPEC → wanwei-shuyi-desktop-1.0.0-1.ky10.x86_64.rpm
#
# 环境要求：git、node >= 22.12、npm >= 10、rpm-build、tar、curl
# 用法：   bash desktop/scripts/build-ky10-rpm.sh [输出目录]
#          输出默认 desktop/release/ky10/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"          # → desktop/
REPO="$(git -C "$ROOT" rev-parse --show-toplevel)" # → 仓库根
VERSION="$(node -p 'require(process.argv[1]).version' "$ROOT/package.json")"
OUT="${1:-$ROOT/release/ky10}"
WORK="$(mktemp -d /tmp/ky10-build.XXXXXX)"
PAYLOAD_TAR="wanwei-shuyi-desktop-${VERSION}-payload.tar.gz"
SPEC_SRC="$ROOT/packaging/ky10/wanwei-shuyi-desktop.spec"

cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

echo "== [0] preflight =="
command -v node >/dev/null || { echo "FATAL: node not found (need 22.12+)" >&2; exit 1; }
command -v rpmbuild >/dev/null || { echo "FATAL: rpmbuild not found (dnf install rpm-build)" >&2; exit 1; }
[ -f "$SPEC_SRC" ] || { echo "FATAL: SPEC missing: $SPEC_SRC" >&2; exit 1; }
# electron 二进制在 npm ci 的 postinstall 就会下载，镜像变量必须先行导出
export ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
export ELECTRON_BUILDER_BINARIES_MIRROR="https://npmmirror.com/mirrors/electron-builder-binaries/"
export npm_config_registry="https://registry.npmmirror.com"

# 脏树拒绝：与 build-linux.sh 同一纪律
if git -C "$REPO" status --porcelain 2>/dev/null | grep -qv '^??'; then
  echo "ERROR: 已跟踪文件有未提交改动;staging 从 HEAD 导出,请先提交。" >&2
  git -C "$REPO" status --porcelain | grep -v '^??' | head -5 >&2
  exit 1
fi

# rpmbuild 树（TopDir 布局）
RPMBUILD="$WORK/rpmbuild"
mkdir -p "$RPMBUILD"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

echo "== [1] export clean tree from HEAD =="
STAGE="$WORK/stage"
mkdir -p "$STAGE"
git -C "$REPO" archive --output="$STAGE/source.tar" HEAD
tar -xf "$STAGE/source.tar" -C "$STAGE"
rm "$STAGE/source.tar"

echo "== [2] apply release-clean.patch =="
git -C "$STAGE" --git-dir="$REPO/.git" --work-tree="$STAGE" apply --check \
  "$STAGE/desktop/packaging/release-clean.patch"
git -C "$STAGE" --git-dir="$REPO/.git" --work-tree="$STAGE" apply \
  "$STAGE/desktop/packaging/release-clean.patch"

echo "== [3] build frontend =="
( cd "$STAGE/frontend/console-vue" && npm ci --silent && npm run build )

echo "== [4] electron-builder --dir =="
( cd "$STAGE/desktop" && npm ci --silent )
export ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
export ELECTRON_BUILDER_BINARIES_MIRROR="https://npmmirror.com/mirrors/electron-builder-binaries/"
( cd "$STAGE/desktop" && npx --no-install electron-builder --linux --x64 --dir )
UNPACKED="$STAGE/desktop/release/linux-unpacked"
[ -x "$UNPACKED/wanwei-shuyi-desktop" ] || { echo "FATAL: linux-unpacked missing" >&2; exit 1; }

echo "== [5] assemble payload tarball =="
PAYLOAD="$WORK/$PAYLOAD_TAR"
mkdir -p "$WORK/payload/app" "$WORK/payload/packaging/icons"
cp -a "$UNPACKED/." "$WORK/payload/app/"
cp "$ROOT/packaging/ky10/wanwei-shuyi-desktop.desktop" "$WORK/payload/packaging/"
cp "$ROOT/packaging/ky10/wanwei-shuyi-desktop.service" "$WORK/payload/packaging/"
cp "$ROOT"/build/icons/{16x16,24x24,32x32,48x48,64x64,128x128,256x256,512x512}.png \
   "$WORK/payload/packaging/icons/"
# 归档顶层目录为 payload/（与 SPEC %setup -n payload 对齐）
tar -czf "$PAYLOAD" -C "$WORK" payload

echo "== [6] rpmbuild =="
cp "$PAYLOAD" "$RPMBUILD/SOURCES/"
cp "$SPEC_SRC" "$RPMBUILD/SPECS/"
mkdir -p "$OUT.tmp"
rpmbuild -bb \
  --define "_topdir $RPMBUILD" \
  --define "_rpmdir $OUT.tmp" \
  "$RPMBUILD/SPECS/wanwei-shuyi-desktop.spec"

echo "== [7] collect =="
mkdir -p "$OUT"
mv "$OUT.tmp"/*/*.rpm "$OUT/" 2>/dev/null || mv "$OUT.tmp"/*.rpm "$OUT/"
rm -rf "$OUT.tmp"
ls -la "$OUT/"
echo "KY10_RPM_DONE"
