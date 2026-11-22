# 桌面优化与维护

新版本配置：`~/.config/hypr/hyprland.lua`。当前仍运行旧版本时，`hyprland.conf` 中也同步了适用的设置。

## 通知与权限

- mako 显示通知，默认 7 秒后消失；严重通知保留到关闭。
- Super+N 关闭通知；Super+Shift+N 切换免打扰。
- hyprpolkitagent 提供需要管理员权限时的图形认证窗口。
- 服务由 `hypr-desktop.target` 管理。会话启动时先导入 Wayland 环境，再启动服务；注销时会话监视器停止这些服务，避免用户 lingering 导致旧会话进程残留。

## 壁纸

- hyprpaper 由 `hyprpaper.service` 管理（已加入 `hypr-desktop.target`），不再用 `exec-once`，旧版 hyprland.conf 与新版 hyprland.lua 两套配置都能生效。
- 壁纸图片与缩放写在 `~/.config/hypr/hyprpaper.conf`（HDMI-A-1、HDMI-A-2 均 cover）；换图后执行 `systemctl --user restart hyprpaper`。
- `Restart=on-failure`：hyprpaper 异常退出（含跟随合成器一起崩溃）2 秒后自动重拉，壁纸不会一直空着。

## 锁屏和熄屏

- Super+L 手动锁屏。
- 空闲 600 秒锁屏、900 秒熄屏；键鼠活动唤醒显示器，仍需解锁。
- 系统休眠前先锁屏；恢复后打开显示器。
- 尊重应用的空闲抑制请求及 Waybar 防休眠开关。
- 没有设置自动系统挂起。
- 锁屏由 swaylock 和系统 PAM 认证提供。熄屏脚本先确认锁屏成功，兼容旧版及 Lua 版 Hyprland 的 DPMS 命令。

## 剪贴板和状态栏

- Super+Shift+V 打开文字/图片剪贴板历史，选择后复制回剪贴板。
- 历史最多 300 条。跳过明确标记为 sensitive、clear、nil 的内容；无法识别未被应用标记的密码。
- 历史文件在 `~/.cache/cliphist/`，目录权限 700。清空命令：`cliphist wipe`。
- 网络图标：左键切换速率格式，右键打开网络连接设置。
- 音量：左键静音，中键或右键打开 pavucontrol；滚轮每次 3%，上限 100%。

## 双 4K 性能

保留 4K、2 倍整数缩放、阴影、窗口动画。关闭背景模糊与边框动画；启用按需重绘（旧版 misc:vfr，新版 debug.vfr）。温度轮询改为每 10 秒，窗口标题最长 28 字符，减少双屏状态栏挤占。
这些调整减少合成及轮询开销；没有声称已测得固定的性能提升百分比。

## 升级和恢复点

- `/etc/pacman.d/hooks/00-desktop-upgrade-snapshot.hook` 在软件包升级前创建根 Btrfs 只读快照；失败时阻止此次升级，并给出错误。
- 根文件系统可用空间不足 10 GiB 时也会阻止升级，需先释放空间。
- `sudo snapper -c root list` 查看快照。快照存于 `/.snapshots/<编号>/snapshot`。
- `/boot` 是独立 FAT 分区，其对应副本、SHA256 校验及包清单位于 `/var/lib/desktop-upgrade-backups/<相同编号>/`，作为独立子卷避免递归备份。
- 根配置通常保留最近 3 个编号快照；新建不足 1 小时的快照暂不清理。按小时清理，关联的旧 boot 副本随后清理。不启用每小时自动创建快照。
- 系统快照在本机同一硬盘，主要用于升级恢复。恢复整个系统需同时考虑对应的 boot 副本及当前挂载布局；不要在此布局上直接套用通用 `snapper rollback` 教程。数据库和运行中的容器未暂停，快照不等同于应用级一致性备份。

## 每日配置备份

`desktop-config-backup.timer` 每日运行，错过的任务在下次用户服务启动后补跑。

- 文件：`~/.local/state/desktop-backups/desktop-时间.tar.gz`，权限仅本人可读。
- 保留最近 14 份。包含 Hyprland、Waybar、mako、此次配置的用户服务和辅助脚本；不包含剪贴板数据库。
- 手动备份：`~/.local/bin/desktop-config-backup`。
- 查看计划：`systemctl --user list-timers desktop-config-backup.timer`。
- 查看归档：`tar -tzf <归档>`。先解压到临时目录比较，再恢复所需文件。

优化前的原始配置归档在 `~/.local/state/hypr-optimization/before-*.tar.gz`。

已有 13 个 `.pacnew` 的差异记录在 `~/.local/state/hypr-optimization/pacnew-review.txt`（权限 600）。现有 SSH、sudo、initramfs 等定制配置保留，未自动覆盖。包签名策略保持 `Required DatabaseOptional`。

## 验证范围

通知发送、polkit agent 注册、服务运行、剪贴板存取和敏感标记过滤已检查。新版 Lua 在独立实例中加载无错误，75 条快捷键注册成功；独立实例中验证了 swaylock 锁屏握手和重复锁屏请求。真实桌面的密码解锁、10/15 分钟超时及休眠恢复仍需实际使用确认。
