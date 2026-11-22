#!/usr/bin/env bash
# 一键恢复 Hyprland 桌面配置。可重复执行（幂等）。
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TS="$(date +%Y%m%d-%H%M%S)"
BK="$HOME/.local/state/hyprland-config-install-backup/$TS"

echo "== hyprland-config install =="
echo "repo: $REPO"

# 1. 备份已有配置
items=(config/hypr config/waybar config/mako config/alacritty config/fcitx5 local/bin)
for it in "${items[@]}"; do
  src="$HOME/.$it"
  [[ -e "$src" ]] || continue
  mkdir -p "$BK"
  cp -a "$src" "$BK/"
  echo "backed up: $src -> $BK/${it##*/}"
done

# 2. 复制配置（不整体覆盖 ~/.config、~/.local/bin，只覆盖仓库内的文件）
mkdir -p "$HOME/.config" "$HOME/.local/bin"
cp -a "$REPO/config/." "$HOME/.config/"
install -m 0755 "$REPO/local/bin/"* "$HOME/.local/bin/"
echo "copied config/ and local/bin/"

# 3. 重写绝对路径 /home/loyu -> $HOME（仅文本文件）
if [[ "$HOME" != "/home/loyu" ]]; then
  while IFS= read -r -d '' f; do
    sed -i "s|/home/loyu|$HOME|g" "$f"
  done < <(grep -rlZ '/home/loyu' \
      "$HOME/.config/hypr" "$HOME/.config/waybar" "$HOME/.config/systemd/user" "$HOME/.local/bin" 2>/dev/null || true)
  echo "rewrote /home/loyu -> $HOME"
fi

# 4. systemd user units
systemctl --user daemon-reload
systemctl --user enable desktop-config-backup.timer 2>/dev/null || true
echo "systemd: daemon-reload done; desktop-config-backup.timer enabled"
echo "提示：其余 unit（hypr-desktop.target 等）由 Hyprland 启动时的 hypr-desktop-start 自动拉起，无需 enable。"

# 5. 依赖提示
if command -v pacman >/dev/null; then
  read -rp "现在安装依赖包？[y/N] " ans
  if [[ "${ans,,}" == y ]]; then
    sudo pacman -S --needed \
      hyprland hypridle hyprpaper hyprpolkitagent waybar mako rofi \
      alacritty kitty nautilus \
      grim slurp wl-clipboard cliphist playerctl brightnessctl \
      wireplumber jq socat \
      fcitx5 fcitx5-gtk fcitx5-qt fcitx5-chinese-addons \
      ttf-jetbrains-mono
  fi
fi

echo
echo "完成。记得："
echo "  1) 按新机器实际情况修改 monitor= 行（hyprland.conf / hyprland.lua 顶部）"
echo "  2) 屏幕截图/录屏需要 wf-recorder（screenrecord 脚本默认找 ~/.local/bin/wf-recorder）"
echo "  3) fcitx5 环境变量见 README.md"
