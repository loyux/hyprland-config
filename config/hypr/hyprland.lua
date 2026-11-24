-- Hyprland 0.57+ Lua 配置：从 hyprland.conf 迁移。旧配置保存在 backups/。
-- 双屏均为 4K、2 倍缩放。修改后 Super+Shift+C 重载。
local dsp = hl.dsp

hl.config({ general = { col = { active_border = {colors={"rgba(33ccffee)","rgba(00ff99ee)"}, angle=45} } } })
hl.bind("SUPER + W", dsp.exec_cmd("alacritty"))
hl.bind("SUPER + C", dsp.window.close())
hl.bind("SUPER + M", dsp.exit())
hl.bind("SUPER + E", dsp.exec_cmd("nautilus"))
hl.bind("SUPER + V", dsp.window.float({action="toggle"}))
hl.bind("SUPER + R", dsp.exec_cmd("rofi -show drun -show-icons -font \"JetBrains Mono 14\""))
hl.bind("SUPER + J", dsp.layout("togglesplit"))
hl.bind("SUPER + SHIFT + P", dsp.exec_cmd("grim -g \"$(slurp -d)\" - | wl-copy"))
hl.bind("SUPER + L", dsp.exec_cmd("/home/loyu/.local/bin/desktop-lock"))
hl.bind("SUPER + B", dsp.exec_cmd("pkill -SIGUSR1 waybar"))
hl.bind("SUPER + SHIFT + B", dsp.exec_cmd("pkill -SIGUSR2 waybar"))
hl.bind("SUPER + SHIFT + V", dsp.exec_cmd("/home/loyu/.local/bin/clipboard-menu"))
hl.bind("SUPER + N", dsp.exec_cmd("makoctl dismiss"))
hl.bind("SUPER + SHIFT + N", dsp.exec_cmd("makoctl mode -t do-not-disturb"))
hl.bind("SUPER + left", dsp.focus({direction="left"}))
hl.bind("SUPER + right", dsp.focus({direction="right"}))
hl.bind("SUPER + up", dsp.focus({direction="up"}))
hl.bind("SUPER + down", dsp.focus({direction="down"}))
hl.bind("SUPER + 1", dsp.focus({workspace="1"}))
hl.bind("SUPER + 2", dsp.focus({workspace="2"}))
hl.bind("SUPER + 3", dsp.focus({workspace="3"}))
hl.bind("SUPER + 4", dsp.focus({workspace="4"}))
hl.bind("SUPER + 5", dsp.focus({workspace="5"}))
hl.bind("SUPER + 6", dsp.focus({workspace="6"}))
hl.bind("SUPER + TAB", dsp.focus({workspace="previous"}))
hl.bind("SUPER + 8", dsp.focus({workspace="8"}))
hl.bind("SUPER + 9", dsp.focus({workspace="9"}))
hl.bind("SUPER + 0", dsp.focus({workspace="10"}))
-- 送窗口去工作区并跟过去（follow=true = 自己也切过去）
hl.bind("SUPER + SHIFT + 1", dsp.window.move({workspace="1",follow=true}))
hl.bind("SUPER + SHIFT + 2", dsp.window.move({workspace="2",follow=true}))
hl.bind("SUPER + SHIFT + 3", dsp.window.move({workspace="3",follow=true}))
hl.bind("SUPER + SHIFT + 4", dsp.window.move({workspace="4",follow=true}))
hl.bind("SUPER + SHIFT + 5", dsp.window.move({workspace="5",follow=true}))
hl.bind("SUPER + SHIFT + 6", dsp.window.move({workspace="6",follow=true}))
hl.bind("SUPER + SHIFT + 8", dsp.window.move({workspace="8",follow=true}))
hl.bind("SUPER + SHIFT + 9", dsp.window.move({workspace="9",follow=true}))
hl.bind("SUPER + SHIFT + 0", dsp.window.move({workspace="10",follow=true}))
hl.bind("SUPER + S", dsp.workspace.toggle_special("magic"))
hl.bind("SUPER + SHIFT + S", dsp.window.move({workspace="special:magic",follow=true}))
hl.bind("SUPER + mouse_down", dsp.focus({workspace="m:e+1"}))
hl.bind("SUPER + mouse_up", dsp.focus({workspace="m:e-1"}))
hl.bind("SUPER + mouse:272", dsp.window.drag(), {mouse=true})
hl.bind("SUPER + mouse:273", dsp.window.resize(), {mouse=true})
hl.bind("XF86AudioRaiseVolume", dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), {repeating=true, locked=true})
hl.bind("XF86AudioLowerVolume", dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), {repeating=true, locked=true})
hl.bind("XF86AudioMute", dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), {repeating=true, locked=true})
hl.bind("XF86AudioMicMute", dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), {repeating=true, locked=true})
hl.bind("XF86MonBrightnessUp", dsp.exec_cmd("brightnessctl s 10%+"), {repeating=true, locked=true})
hl.bind("XF86MonBrightnessDown", dsp.exec_cmd("brightnessctl s 10%-"), {repeating=true, locked=true})
hl.bind("SHIFT + XF86AudioRaiseVolume", dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SOURCE@ 5%+"), {repeating=true, locked=true})
hl.bind("SHIFT + XF86AudioLowerVolume", dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SOURCE@ 5%-"), {repeating=true, locked=true})
hl.bind("XF86AudioNext", dsp.exec_cmd("playerctl next"), {locked=true})
hl.bind("XF86AudioPause", dsp.exec_cmd("playerctl play-pause"), {locked=true})
hl.bind("XF86AudioPlay", dsp.exec_cmd("playerctl play-pause"), {locked=true})
hl.bind("XF86AudioPrev", dsp.exec_cmd("playerctl previous"), {locked=true})
hl.bind("SUPER + U", dsp.exec_cmd("google-chrome-stable"))
hl.bind("SUPER + P", dsp.exec_cmd("grim -g \"$(slurp)\" ~/Pictures/Screenshots/$(date +'%Y-%m-%d_%H-%M-%S').png"))
hl.bind("SUPER + SHIFT + R", dsp.exec_cmd("/home/loyu/.local/bin/screenrecord toggle"))
hl.bind("SUPER + ALT + R", dsp.exec_cmd("/home/loyu/.local/bin/screenrecord region"))
hl.bind("SUPER + SHIFT + SPACE", dsp.window.float({action="toggle"}))
hl.bind("SUPER + SHIFT + C", dsp.exec_cmd("hyprctl reload"))
hl.bind("SUPER + ALT + V", dsp.exec_cmd("echo start | socat - UNIX-CONNECT:/tmp/stt.sock"), {locked=true})
hl.bind("SUPER + ALT + V", dsp.exec_cmd("echo stop  | socat - UNIX-CONNECT:/tmp/stt.sock"), {release=true, transparent=true})

local doubaoVoice = os.getenv("HOME") .. "/.local/bin/doubao-voice"
hl.bind("F8", dsp.exec_cmd(doubaoVoice .. " --start"))
hl.bind("F8", dsp.exec_cmd(doubaoVoice .. " --stop"), {release=true})
hl.bind("SHIFT + F8", dsp.exec_cmd(doubaoVoice .. " --cancel"))
hl.bind("SUPER + CTRL + left", dsp.focus({monitor="l"}))
hl.bind("SUPER + CTRL + right", dsp.focus({monitor="r"}))
hl.bind("SUPER + SHIFT + left", dsp.window.move({direction="left"}))
hl.bind("SUPER + SHIFT + right", dsp.window.move({direction="right"}))
hl.bind("SUPER + CTRL + SHIFT + 1", dsp.window.move({workspace="4",follow=true}))
hl.bind("SUPER + CTRL + SHIFT + 2", dsp.window.move({workspace="5",follow=true}))
hl.bind("SUPER + CTRL + SHIFT + 3", dsp.window.move({workspace="6",follow=true}))
hl.bind("SUPER + CTRL + SHIFT + 4", dsp.window.move({workspace="1",follow=true}))
hl.bind("SUPER + CTRL + SHIFT + 5", dsp.window.move({workspace="2",follow=true}))
hl.bind("SUPER + CTRL + SHIFT + 6", dsp.window.move({workspace="3",follow=true}))
hl.bind("PRINT", dsp.exec_cmd("for m in $(hyprctl monitors -j | jq -r '.[].name'); do grim -o $m ~/Pictures/Screenshots/$(date +%Y-%m-%d_%H-%M-%S)_$m.png; done"))
hl.bind("SUPER + F", dsp.window.fullscreen())

-- 外观、输入、缩放
hl.config({
    general = {
        gaps_in = 5,
        gaps_out = 20,
        border_size = 2,
        col = {
            inactive_border = "rgba(595959aa)",
        },
        resize_on_border = false,
        allow_tearing = false,
        layout = "dwindle",
    },
    decoration = {
        rounding = 10,
        rounding_power = 2,
        active_opacity = 1.0,
        inactive_opacity = 1.0,
        shadow = {
            enabled = true,
            range = 4,
            render_power = 3,
            color = "rgba(1a1a1aee)",
        },
        blur = {
            enabled = false, -- 双 4K 核显：关闭背景模糊，减少合成开销
            size = 3,
            passes = 1,
            new_optimizations = true,
            xray = true,
            vibrancy = 0.1696,
        },
    },
    animations = {
        enabled = true,
    },
    dwindle = {
        preserve_split = true,
    },
    master = {
        new_status = "master",
    },
    misc = {
        force_default_wallpaper = 0,
        disable_hyprland_logo = true,
    },
    debug = { vfr = true }, -- 新版的按需重绘选项位于 debug
    input = {
        kb_layout = "us",
        kb_variant = "",
        kb_model = "",
        kb_options = "",
        kb_rules = "",
        follow_mouse = 1,
        sensitivity = 0,
        touchpad = {
            natural_scroll = false,
        },
    },
    xwayland = {
        force_zero_scaling = true,
    },
})
hl.monitor({output="HDMI-A-1",mode="3840x2160@60",position="0x0",scale=2})
hl.monitor({output="HDMI-A-2",mode="3840x2160@60",position="1920x0",scale=2})
hl.monitor({output="",mode="preferred",position="auto",scale=1.5})
hl.workspace_rule({workspace="1",monitor="HDMI-A-1",default=true})
hl.workspace_rule({workspace="2",monitor="HDMI-A-1"})
hl.workspace_rule({workspace="3",monitor="HDMI-A-1"})
hl.workspace_rule({workspace="4",monitor="HDMI-A-2",default=true})
hl.workspace_rule({workspace="5",monitor="HDMI-A-2"})
hl.workspace_rule({workspace="6",monitor="HDMI-A-2"})
hl.device({name="epic-mouse-v1",sensitivity=-0.5})
hl.env("XCURSOR_THEME","Adwaita")
hl.env("XCURSOR_SIZE","32")
hl.env("HYPRCURSOR_SIZE","32")
hl.env("MOZ_ENABLE_WAYLAND","1")
hl.env("QT_QPA_PLATFORM","wayland")
hl.env("XIM","fcitx")
hl.env("XIM_PROGRAM","fcitx")
hl.env("INPUT_METHOD","fcitx")
hl.env("GTK_IM_MODULE","fcitx")
hl.env("QT_IM_MODULE","fcitx")
hl.env("XMODIFIERS","@im=fcitx")
hl.env("GDK_SCALE","1")
hl.curve("easeOutQuint", {type="bezier",points={{0.23,1},{0.32,1}}})
hl.curve("easeInOutCubic", {type="bezier",points={{0.65,0.05},{0.36,1}}})
hl.curve("linear", {type="bezier",points={{0,0},{1,1}}})
hl.curve("almostLinear", {type="bezier",points={{0.5,0.5},{0.75,1.0}}})
hl.curve("quick", {type="bezier",points={{0.15,0},{0.1,1}}})
hl.animation({leaf="global",enabled=true,speed=10,bezier="default"})
hl.animation({leaf="border",enabled=false,speed=5.39,bezier="easeOutQuint"})
hl.animation({leaf="windows",enabled=true,speed=4.79,bezier="easeOutQuint"})
hl.animation({leaf="windowsIn",enabled=true,speed=4.1,bezier="easeOutQuint",style="popin 87%"})
hl.animation({leaf="windowsOut",enabled=true,speed=1.49,bezier="linear",style="popin 87%"})
hl.animation({leaf="fadeIn",enabled=true,speed=1.73,bezier="almostLinear"})
hl.animation({leaf="fadeOut",enabled=true,speed=1.46,bezier="almostLinear"})
hl.animation({leaf="fade",enabled=true,speed=3.03,bezier="quick"})
hl.animation({leaf="layers",enabled=true,speed=3.81,bezier="easeOutQuint"})
hl.animation({leaf="layersIn",enabled=true,speed=4,bezier="easeOutQuint",style="fade"})
hl.animation({leaf="layersOut",enabled=true,speed=1.5,bezier="linear",style="fade"})
hl.animation({leaf="fadeLayersIn",enabled=true,speed=1.79,bezier="almostLinear"})
hl.animation({leaf="fadeLayersOut",enabled=true,speed=1.39,bezier="almostLinear"})
hl.animation({leaf="workspaces",enabled=true,speed=1.94,bezier="almostLinear",style="fade"})
hl.animation({leaf="workspacesIn",enabled=true,speed=1.21,bezier="almostLinear",style="fade"})
hl.animation({leaf="workspacesOut",enabled=true,speed=1.94,bezier="almostLinear",style="fade"})

-- 只在真实会话启动时运行；验证实例可通过环境变量关闭自启。
if os.getenv("HYPRLAND_MIGRATION_TEST") ~= "1" then
    hl.on("hyprland.start", function()
        hl.exec_cmd("waybar")
        hl.exec_cmd("fcitx5 -d --replace")
        hl.exec_cmd("/home/loyu/.local/bin/hypr-desktop-start")
        hl.exec_cmd(doubaoVoice)
    end)
end
