# wanwei-shuyi-desktop · 麒麟 ky10 RPM 打包线

按《银河麒麟高级服务器操作系统 RPM 包打包规范》V1.7（2025-12-08）出包，
与 electron-builder 原生 deb/rpm 线（`scripts/build-linux.sh`）**并存且互不影响**。

## 与原生线的关系

| | 原生线（build-linux.sh） | ky10 线（本目录） |
|---|---|---|
| 工具 | electron-builder 自带 fpm | rpmbuild + SPEC |
| 包名 | wanwei-shuyi-desktop-1.0.0.x86_64.rpm | wanwei-shuyi-desktop-1.0.0-1.**ky10**.x86_64.rpm |
| 安装路径 | /opt/wanwei-shuyi-desktop | **/opt/cn.wanwei/wanwei-shuyi-desktop**（规范 5.2 域名式） |
| desktop/图标 | electron-builder 自动 | SPEC 显式装 /usr/share/applications + hicolor 全尺寸（规范 5.3） |
| 适用场景 | 通用 Linux | 麒麟 V10 SP3 / V11 服务器（信创交付） |

两条线共用 `release-clean.patch`、同一份 staging 纪律（脏树拒绝、HEAD 导出）
和同一份 electron-builder 载荷（linux-unpacked），仅封装层不同。

## 构建

环境：麒麟（V10 SP3 或 V11）+ node ≥ 22.12 + npm ≥ 10 + rpm-build。

```bash
bash desktop/scripts/build-ky10-rpm.sh
# 产物: desktop/release/ky10/wanwei-shuyi-desktop-1.0.0-1.ky10.x86_64.rpm
```

## 安装 / 卸载

```bash
sudo rpm -ivh wanwei-shuyi-desktop-1.0.0-1.ky10.x86_64.rpm
# 升级: sudo rpm -Uvh wanwei-shuyi-desktop-*.ky10.x86_64.rpm
sudo rpm -e wanwei-shuyi-desktop
```

首启时应用自动以系统 python3 建 venv 装后端依赖（需 ≥ 3.10；V11 桌面/服务器
自带 3.12 满足；老 V10 SP3 需自备新解释器并设 `WANWEI_DESKTOP_PYTHON`）。

## 规范符合性对照

- 4.1 命名：`%{?dist}` 在麒麟构建机展开为 `.ky10` → softname-version-release.ky10.x86_64.rpm
- 5.1 SPEC：Name/Version/Release/Summary/License/%description/%changelog 全部非空
- 5.2 目录：`/opt/cn.wanwei/<软件名>/`（第三方自研软件域名式）
- 5.3.1 desktop 文件：以 softname 命名，装 `/usr/share/applications`
- 5.3.2 图标：PNG 全尺寸 16–512 → `/usr/share/icons/hicolor/<尺寸>/apps/<softname>.png`
- 5.4 不动系统文件（%post 只刷新缓存数据库）；包名=安装后软件名；不嵌套

## 文件清单

- `wanwei-shuyi-desktop.spec` — rpmbuild SPEC（核心）
- `wanwei-shuyi-desktop.desktop` — desktop 启动器（Exec 指向新路径）
- `wanwei-shuyi-desktop.service` — systemd --user 单元（可选装）
- `../../scripts/build-ky10-rpm.sh` — 一键构建（staging → payload → rpmbuild）
