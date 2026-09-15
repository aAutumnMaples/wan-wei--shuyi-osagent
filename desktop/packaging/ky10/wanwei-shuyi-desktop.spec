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

# ============================================================================
# wanwei-shuyi-desktop 麒麟 RPM 打包 SPEC
# 规范依据：《银河麒麟高级服务器操作系统 RPM 包打包规范》V1.7（2025-12-08）
#   4.1 命名: softname-version-release.ky10.arch.rpm（%{?dist} 在麒麟构建机
#            自动展开为 .ky10）
#   5.1  必填字段: Name/Version/Release/Summary/License/%description/%changelog
#   5.2  安装目录: 第三方自研软件 → /opt/公司域名/自研软件名/
#   5.3.1 desktop 文件 → /usr/share/applications，以 softname 命名
#   5.3.2 图标 → /usr/share/icons/hicolor/<尺寸>/apps/（PNG 全尺寸）
#   5.4  安装/卸载不改系统文件；包名与安装后软件名一致；不嵌套
# ============================================================================
# 构建输入：desktop/scripts/build-ky10-rpm.sh 产出的载荷 tarball
#   wanwei-shuyi-desktop-1.0.0-payload.tar.gz（linux-unpacked 全树 + 图标 + 脚本）
# 首次构建请先阅读 desktop/packaging/ky10/README.md。

Name:           wanwei-shuyi-desktop
Version:        1.0.0
Release:        1%{?dist}
Summary:        宛委·枢忆 OSAgent 秘府控制台（麒麟桌面客户端）

License:        Mulan-PSL-2.0
URL:            https://github.com/QianChang-official/wan-wei--shuyi-osagent
Packager:       aAutumnMaples <2739823745@qq.com>
Vendor:         WanWei Shuyi Team
# electron-builder --dir 产出的应用树（chrome-sandbox 需 4755，在 %install 赋权）
Source0:        %{name}-%{version}-payload.tar.gz

# 已知在 Kylin V10 SP3 / V11 上可用；其他平台未验证
# （二进制载荷在 x86_64 构建机上默认出 x86_64 包，无需 BuildArch）
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root

# 后端依赖由应用首启自建 venv（系统 python3 + pip），SPEC 仅声明硬依赖。
# V10 SP3: python3 = 3.6（requirements 需 3.10+ → rpmbuild --without legacy-python
#          可放开 python3 >= 3.10 检查；--with legacy-python 则按提示装 uv 自管）
Requires:       python3
Requires:       python3-pip
Recommends:     xdg-utils
Recommends:     %{_bindir}/gtk-update-icon-cache
Recommends:     %{_bindir}/update-desktop-database
Recommends:     findutils
Obsoletes:      wanwei-shuyi-desktop < %{version}-%{release}
Provides:       wanwei-shuyi-desktop = %{version}-%{release}

%description
宛委·枢忆 MemoryOps Autopilot Platform 的麒麟桌面客户端。内嵌 FastAPI
后端与 Vue3 控制台，与 Web 端共享同一套业务代码；首次启动时自动以系统
python3 创建 venv 并安装后端依赖，之后常驻本地记忆库（SQLite）。

安装目录遵循麒麟打包规范 5.2：/opt/cn.wanwei/wanwei-shuyi-desktop/。
桌面集成遵循 5.3：desktop 文件安装到 /usr/share/applications，图标以
应用名安装到 /usr/share/icons/hicolor 全尺寸目录。

%prep
%setup -q -n payload

%build
# 载荷为预构建二进制树，无需编译
:

%install
rm -rf %{buildroot}
INSTALL_ROOT=%{buildroot}/opt/cn.wanwei/%{name}

# ---- 应用主体（electron-builder linux-unpacked 全树）----
install -d -m 0755 %{buildroot}/opt/cn.wanwei
cp -a app/. "$INSTALL_ROOT/"
# SPEC 直接声明 chrome-sandbox 的 SUID 位（规范 5.4：不改系统文件，属软件自身文件）
chmod 4755 "$INSTALL_ROOT/chrome-sandbox"

# ---- 命令行入口（规范 5.4.2：包名与安装后软件名一致）----
install -d -m 0755 %{buildroot}%{_bindir}
ln -s /opt/cn.wanwei/%{name}/%{name} %{buildroot}%{_bindir}/%{name}

# ---- desktop 文件（规范 5.3.1：以 softname 命名，装 applications 目录）----
install -d -m 0755 %{buildroot}%{_datadir}/applications
install -m 0644 packaging/wanwei-shuyi-desktop.desktop %{buildroot}%{_datadir}/applications/

# ---- 图标（规范 5.3.2：PNG 全尺寸 → hicolor/<尺寸>/apps/）----
for size in 16 24 32 48 64 128 256 512; do
  install -d -m 0755 "%{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps"
  install -m 0644 "packaging/icons/${size}x${size}.png" \
    "%{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{name}.png"
done

# ---- 可选 systemd 用户服务（高级用户用 systemctl --user 管理）----
install -d -m 0755 %{buildroot}%{_sysconfdir}/systemd/user
install -m 0644 packaging/wanwei-shuyi-desktop.service %{buildroot}%{_sysconfdir}/systemd/user/

%files
# 应用树（chrome-sandbox 的 4755 由 %install chmod + rpmbuild 载荷记录保留）
/opt/cn.wanwei/%{name}/
%attr(4755, root, root) /opt/cn.wanwei/%{name}/chrome-sandbox
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_sysconfdir}/systemd/user/%{name}.service

%post
if [ "$1" -eq 1 ]; then
  # 首次安装：刷新 desktop/icon 数据库（工具缺失时跳过，不失败）
  %{_bindir}/update-desktop-database %{_datadir}/applications >/dev/null 2>&1 || :
  %{_bindir}/gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor >/dev/null 2>&1 || :
fi
# python3 < 3.10 时提示（不阻断安装；V10 SP3 服务器默认 3.6 需自备新解释器）
PYV=$(%{_bindir}/python3 -c 'import sys; print("%d%02d" % sys.version_info[:2])' 2>/dev/null || echo 0)
if [ "$PYV" -lt 310 ]; then
  echo "wanwei-shuyi-desktop: system python3 is older than 3.10;" \
       "backend venv will fail to resolve requirements. Install Python >= 3.10" \
       "(e.g. via uv) or set WANWEI_DESKTOP_PYTHON to a newer interpreter." >&2
fi

%postun
if [ "$1" -eq 0 ]; then
  # 完全卸载：刷新数据库；用户数据 ~/.config/wanwei-shuyi-desktop 保留
  %{_bindir}/update-desktop-database %{_datadir}/applications >/dev/null 2>&1 || :
  %{_bindir}/gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor >/dev/null 2>&1 || :
fi

%changelog
* Mon Sep 15 2026 aAutumnMaples <2739823745@qq.com> - 1.0.0-1
- Initial release for Kylin Linux Advanced Server V10 SP3 / V11
- 按麒麟 RPM 打包规范 V1.7 打包：/opt/cn.wanwei/ 域名式安装目录、
  /usr/share/applications desktop 文件、hicolor 全尺寸 PNG 图标、
  SPEC 必填字段（Name/Version/Release/Summary/License/description/changelog）齐全
- 载荷来自 electron-builder linux-unpacked（Electron 43），内嵌 FastAPI
  后端与 Vue3 控制台；首启以系统 python3 自建 venv 安装后端依赖
