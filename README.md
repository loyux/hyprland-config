# hyprland-config

我的 Hyprland 桌面配置，用于换机器后一键复现环境。

架构：Arch Linux（滚动车臂）+ Hyprland（Wayland）+ waybar + rofi + mako + hypridle/hyprpaper/hyprpolkitagent，输入法 fcitx5（拼音）。

## 目录结构

```
config/
├── hypr/           # hyprland.conf、hyprland.lua（0.57+ Lua 配置）、hypridle、hyprpaper、wofi.css
│   ├── MIGRATION.md / OPTIMIZATIONS.md   # 迁移与优化笔记
├── waybar/         # 状态栏 config.jsonc + style.css + scripts/（agents.py、token-usage.py）
├── mako/           # 通知守护进程
├── alacritty/      # 终端
├── fcitx5/         # 输入法 profile + 模块配置（不含 cached_layouts / 用户词库）
└── systemd/user/   # hypr-desktop.target、剪贴板历史、备份 timer，及 mako/hypridle/hyprpolkitagent/hyprpaper 的 drop-in
local/bin/          # desktop-lock、screenrecord、clipboard-menu/store、hscale、hypr-desktop-start 等脚本
install.sh          # 一键安装
```

## 在新机器上恢复

```bash
git clone git@github.com:loyux/hyprland-config.git
cd hyprland-config
./install.sh
```

`install.sh` 会：

1. 把已存在的旧配置备份到 `~/.local/state/hyprland-config-install-backup/<时间戳>/`；
2. 复制 `config/` 到 `~/.config/`、`local/bin/*` 到 `~/.local/bin/`（可执行权限）；
3. 把所有文件里的绝对路径 `/home/loyu` 重写为当前 `$HOME`；
4. `systemctl --user daemon-reload` 并启用 `desktop-config-backup.timer`；
5. 提示安装依赖包。

其余 unit 无需 enable：Hyprland 启动时 `exec-once = hypr-desktop-start` 会拉起 `hypr-desktop.target`，再牵动剪贴板历史、mako、hypridle、hyprpolkitagent。

## 依赖（Arch）

```bash
sudo pacman -S --needed \
  hyprland hypridle hyprpaper hyprpolkitagent waybar mako rofi \
  alacritty kitty nautilus \
  grim slurp wl-clipboard cliphist playerctl brightnessctl \
  wireplumber jq socat \
  fcitx5 fcitx5-gtk fcitx5-qt fcitx5-chinese-addons \
  ttf-jetbrains-mono
```

另需（AUR 或自行编译）：

- `wf-recorder` —— `screenrecord` 脚本默认调用 `~/.local/bin/wf-recorder`（本机是本地编译的二进制，未入库）。可用环境变量 `WF_RECORDER` 指向系统路径，或 `pacman -S wf-recorder`（AUR）后软链。

环境变量（fcitx5，写入 `/etc/environment` 或 shell profile）：

```
GTK_IM_MODULE=fcitx
QT_IM_MODULE=fcitx
XMODIFIERS=@im=fcitx
SDL_IM_MODULE=fcitx
```

## 换机器时大概率要改的地方

- **显示器布局**：`config/hypr/hyprland.conf` / `hyprland.lua` 顶部写死了双 4K 屏（HDMI-A-1 左、HDMI-A-2 右，3840x2160@60，scale 1.5）。新机器用 `hyprctl monitors` 查看实际名称后修改，或先删掉 monitor 行让 Hyprland 自动探测。
- **壁纸**：`hyprpaper.conf` 指向 `~/20261122-093823.jpg`（个人图片，未入库），且 hyprpaper 目前处于停用状态（见 `hypr-desktop.target` 注释）。
- **GPU/缩放**：`hscale` 脚本用于分数缩放修复，视显卡情况调整。
- **fcitx5 用户词库**不在仓库里（隐私），在旧机导出：`~/.local/share/fcitx5/pinyin/`。

## 安全说明

入库前已扫描并排除：所有 `*.bak*` 备份文件、二进制程序（`rc`、本地 `wf-recorder`）、`__pycache__`、壁纸图片、与桌面无关的 systemd 服务（okx-*、wherdr、paseo 等）。仓库中不含任何 token/密码。
