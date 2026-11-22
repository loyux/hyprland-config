# Hyprland 0.57 Lua 配置迁移

当前新版本默认配置：`~/.config/hypr/hyprland.lua`。
旧版当前会话仍使用 `hyprland.conf`；旧文件和 `backups/` 中的备份均保留。
注销后重新登录 Hyprland，或保存工作后重启，即启用新版本及 Lua 配置。

保留内容：双 4K 显示器布局（HDMI-A-1 左、HDMI-A-2 右，scale=2）、工作区 1–6 分屏、外观和动画、输入法环境变量、截图录屏、语音按住/释放快捷键、媒体键、Waybar 自启。

迁移调整：
- 删除重复的两条 Super+滚轮绑定，保留当前显示器内切换工作区的绑定。
- 新版本移除了 `dwindle.pseudotile` 全局开关，因此未复制该项。
- 静默移动窗口显式设置 `follow=false`；原先随窗口切换的绑定设置 `follow=true`。
- 自启改用 `hl.on("hyprland.start", ...)`。设置 `HYPRLAND_MIGRATION_TEST=1` 可在独立验证实例中禁用自启，避免重复启动输入法或导入测试环境。

验证结果：
- `Hyprland --verify-config`（默认配置路径）通过。
- 独立新版本实例中 `configerrors` 无错误。
- 72 条快捷键的组合键及 locked/release/repeating/mouse 标志与旧配置一致（旧配置 74 条，差异仅为两条重复滚轮绑定）。
- 6 条工作区规则加载成功，35 个迁移配置字段可查询。
- 当前桌面继续运行；未自动注销或重启。

常用快捷键：Super+B 显示/隐藏状态栏；Super+Shift+B 重载 Waybar；Super+Shift+C 重载 Hyprland。
