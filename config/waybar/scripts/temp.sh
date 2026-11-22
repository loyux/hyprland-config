#!/usr/bin/env bash
# 输出 CPU 封装温度，例如 " 53℃"
# 优先 coretemp(Package id 0) → x86_pkg_temp/acpitz 热区 → sensors 命令
set -u

temp=""

# 1) coretemp：hwmon 里 name=coretemp 的 temp1_input 就是 Package 温度
for h in /sys/class/hwmon/hwmon*; do
  if [ "$(cat "$h/name" 2>/dev/null)" = "coretemp" ] && [ -r "$h/temp1_input" ]; then
    temp=$(( $(<"$h/temp1_input") / 1000 ))
    break
  fi
done

# 2) 退回 ACPI 热区（取封装/CPU 类，否则取最大值）
if [ -z "$temp" ] || [ "$temp" -le 0 ]; then
  max=0
  for z in /sys/class/thermal/thermal_zone*; do
    [ -r "$z/temp" ] || continue
    type=$(cat "$z/type" 2>/dev/null)
    v=$(( $(<"$z/temp") / 1000 ))
    case "$type" in
      x86_pkg_temp|acpitz|cpu_thermal|soc_thermal) temp=$v; break ;;
    esac
    [ "$v" -gt "$max" ] && [ "$v" -lt 120 ] && max=$v
  done
  { [ -z "$temp" ] || [ "$temp" -le 0 ]; } && [ "$max" -gt 0 ] && temp=$max
fi

# 3) 退回 sensors 命令（只取每行第一个温度，忽略 high/crit 阈值）
if [ -z "$temp" ] || [ "$temp" -le 0 ]; then
  if command -v sensors >/dev/null 2>&1; then
    v=$(sensors 2>/dev/null | awk '/Package id 0|Tctl|Tdie|CPU 温度|^cpu/ {
          for (i = 1; i <= NF; i++) if ($i ~ /^\+[0-9]+\.[0-9]°C/) { gsub(/[+°C]/, "", $i); print int($i); exit } }')
    [ -n "$v" ] && temp=$v
  fi
fi

if [ -z "$temp" ] || [ "$temp" -le 0 ]; then
  echo " --℃"
  exit 0
fi

# 图标随温度变化：雪花 → 温度计 → 火焰
if   [ "$temp" -lt 50 ]; then icon=$'\uf2cd'
elif [ "$temp" -lt 65 ]; then icon=$'\uf2c9'
elif [ "$temp" -lt 80 ]; then icon=$'\uf2c8'
else                          icon=$'\uf06d'
fi

printf '%s %s℃\n' "$icon" "$temp"
