#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agents.py ─ 本机 coding agent 状态探针（Hyprland / waybar 小挂件）

数据来源（只读，不依赖任何 agent 的官方 API）：
  1. /proc            → 哪些 agent 进程活着、CPU 是否在跑
  2. session JSONL    → 当前项目、模型、token 用量、最后一次活动时间
       pi      ~/.pi/agent/sessions/--<cwd>--/<ts>_<uuid>.jsonl
       codex   ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl  (+ session_index.jsonl 取标题)
       claude  ~/.claude/projects/<slug>/<uuid>.jsonl

用法：
  agents.py                 # 终端彩色报告
  agents.py --json          # waybar custom module（return-type: json）
  agents.py --raw           # 纯文本一行（tmux status / polybar 用）
  agents.py --notify        # 把报告丢进 notify-send
  agents.py --pretty        # 纯文本多行，不带颜色

只依赖标准库。
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

HOME = Path.home()
CACHE_FILE = Path(os.environ.get("XDG_CACHE_HOME", str(HOME / ".cache"))) / "waybar-agents.json"

# ────────────────────────────── 可调参数 ──────────────────────────────
ACTIVE_AGE = 20          # 会话文件 N 秒内有写入 → 判定为「正在干活」
BUSY_CPU = 0.20          # 进程 CPU 占用超过该比例（0~1）也判定为「正在干活」
NAME_LEN = 46            # tooltip 里标题截断长度
DOT_ON, DOT_OFF = "●", "○"   # 若显示成方块，把这两个字符换成 * 和 -

# ────────────────────────────── agent 定义 ──────────────────────────────


@dataclass
class AgentSpec:
    key: str
    label: str
    fmt: str                                   # session 解析器
    roots: list                                # session jsonl 的 glob
    proc: callable                             # (argv) -> bool，是否算一个交互会话进程
    live: bool = True                          # 是否参与「运行中」判定


def _is_pi(argv: list) -> bool:
    b0 = os.path.basename(argv[0]) if argv else ""
    if b0 == "pi":
        return True
    if b0 in ("node", "bun", "deno") and any("/pi" in a or a.endswith("cli.js") for a in argv[1:]):
        return True
    return False


def _is_codex(argv: list) -> bool:
    b0 = os.path.basename(argv[0]) if argv else ""
    if b0 not in ("codex", "codex-tui", "codex-cli"):
        return False
    # 常驻守护/子服务不算「会话」
    junk = ("app-server", "mcp-server", "code-mode-host", "--managed-daemon", "daemon", "serve")
    return not any(j in a for a in argv[1:] for j in junk)


def _simple(names):
    names = set(names)
    return lambda argv: bool(argv) and os.path.basename(argv[0]) in names


AGENTS = [
    AgentSpec("pi", "pi", "pi", [str(HOME / ".pi/agent/sessions/*/*.jsonl")], _is_pi),
    AgentSpec("codex", "codex", "codex", [str(HOME / ".codex/sessions/*/*/*/rollout-*.jsonl")], _is_codex),
    AgentSpec("claude", "claude", "claude", [str(HOME / ".claude/projects/*/*.jsonl")], _simple(["claude"])),
    AgentSpec("opencode", "opencode", "generic", [str(HOME / ".local/share/opencode/storage/session/*/*.json")], _simple(["opencode"])),
    AgentSpec("gemini", "gemini", "claude", [str(HOME / ".gemini/projects/*/*.jsonl")], _simple(["gemini"])),
    AgentSpec("aider", "aider", "generic", [], _simple(["aider"])),
]

# ────────────────────────────── 工具函数 ──────────────────────────────


def load_cache() -> dict:
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            c = json.load(f)
    except Exception:
        c = {}
    c.setdefault("files", {})
    c.setdefault("cpu", {})
    return c


def save_cache(cache: dict) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cache, f)
        os.replace(tmp, CACHE_FILE)
    except Exception:
        pass


def human(n: float) -> str:
    n = float(n or 0)
    for unit, div in (("B", 1), ("K", 1e3), ("M", 1e6), ("G", 1e9)):
        if n < div * 1e3 or unit == "G":
            return f"{n/div:.1f}{unit}" if n >= div else f"{int(n)}"
    return str(n)


def ago(ts: float | None, now: float) -> str:
    if not ts:
        return "-"
    d = max(0, int(now - ts))
    if d < 60:
        return f"{d}s"
    if d < 3600:
        return f"{d//60}m"
    if d < 86400:
        return f"{d//3600}h"
    return f"{d//86400}d"


def clip(s: str, n: int) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def esc(s) -> str:
    """Pango markup 转义（tooltip 里的动态字段必须过一道）。"""
    return (str(s if s is not None else "").replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))


def short_model(m: str) -> str:
    if not m:
        return "?"
    m = m.rstrip("/").split("/")[-1]
    return clip(m, 28)


# ────────────────────────────── 进程扫描 ──────────────────────────────


def scan_procs(cache: dict, now: float) -> dict:
    """返回 {agent_key: [ {pid, cwd, cpu, busy} ]}"""
    out: dict = {a.key: [] for a in AGENTS}
    prev = cache.get("cpu", {})
    fresh: dict = {}
    prev_secs = cache.get("cpu_secs", now)
    dt = max(1.0, now - prev_secs)

    for pid_dir in os.scandir("/proc"):
        if not pid_dir.name.isdigit():
            continue
        pid = pid_dir.name
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                raw = f.read()
            argv = [x.decode("utf-8", "replace") for x in raw.split(b"\0") if x]
            if not argv:
                continue
            with open(f"/proc/{pid}/stat", "r", errors="replace") as f:
                stat = f.read().rsplit(") ", 1)[-1].split()
            ticks = (int(stat[11]) + int(stat[12])) / os.sysconf("SC_CLK_TCK")
            starttime = int(stat[19])
        except Exception:
            continue

        spec = next((a for a in AGENTS if a.proc(argv)), None)
        if spec is None:
            continue
        key = f"{pid}"
        old = prev.get(key)
        busy = 0.0
        if old and old[0] == starttime:
            busy = max(0.0, (ticks - old[1]) / dt)
        fresh[key] = [starttime, ticks]
        try:
            cwd = os.readlink(f"/proc/{pid}/cwd")
        except Exception:
            cwd = ""
        out[spec.key].append({"pid": int(pid), "cwd": cwd, "cpu": round(busy * 100), "busy": busy >= BUSY_CPU})

    cache["cpu"] = fresh
    cache["cpu_secs"] = now
    return out


# ────────────────────────────── session 解析 ──────────────────────────────


@dataclass
class Sess:
    path: str = ""
    cwd: str = ""
    name: str = ""
    model: str = ""
    tokens: int = 0
    out_tokens: int = 0
    cost: float = 0.0
    mtime: float = 0.0
    procs: list = field(default_factory=list)


def _text_of(msg) -> str:
    """从 various 形态的 message 里抠出纯文本。"""
    if isinstance(msg, str):
        return msg
    if isinstance(msg, dict):
        c = msg.get("content", msg)
        return _text_of(c)
    if isinstance(msg, list):
        for part in msg:
            if isinstance(part, dict):
                for k in ("text", "content", "input_text"):
                    v = part.get(k)
                    if isinstance(v, str) and v.strip():
                        return v
            elif isinstance(part, str) and part.strip():
                return part
    return ""


def parse_codex_title_index() -> dict:
    idx: dict = {}
    p = HOME / ".codex/session_index.jsonl"
    try:
        size = p.stat().st_size
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            if size > 400_000:
                f.seek(size - 400_000)
                f.readline()
            for line in f:
                try:
                    d = json.loads(line)
                    if d.get("id"):
                        idx[d["id"]] = d.get("thread_name") or ""
                except Exception:
                    pass
    except Exception:
        pass
    return idx


def parse_file(path: str, fmt: str, cache: dict, titles: dict) -> dict:
    """增量解析（append-only jsonl），缓存 byte offset + 聚合结果。"""
    try:
        st = os.stat(path)
    except Exception:
        return {}
    ent = cache["files"].get(path)
    if ent and ent.get("size") == st.st_size and ent.get("dev_ok", True):
        ent["mtime"] = st.st_mtime
        return ent
    if not ent or ent.get("size", 0) > st.st_size:
        ent = {"off": 0, "cwd": "", "name": "", "model": "", "tokens": 0,
               "out": 0, "cost": 0.0, "size": 0, "dev_ok": True}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            f.seek(ent["off"])
            for line in f:
                if not line.endswith("\n"):          # 半行，下次再读
                    break
                if fmt == "pi":
                    if '"cwd"' in line and not ent["cwd"]:
                        try:
                            d = json.loads(line)
                            if d.get("type") == "session":
                                ent["cwd"] = d.get("cwd", "")
                        except Exception:
                            pass
                    if '"name"' in line and '"session_info"' in line:
                        try:
                            ent["name"] = json.loads(line).get("name") or ent["name"]
                        except Exception:
                            pass
                    if '"usage"' in line:
                        try:
                            m = json.loads(line).get("message", {})
                            if m.get("role") == "assistant":
                                u = m.get("usage") or {}
                                ent["tokens"] += int(u.get("totalTokens", 0) or 0)
                                ent["out"] += int(u.get("output", 0) or 0)
                                ent["cost"] += float((u.get("cost") or {}).get("total", 0) or 0)
                                ent["model"] = m.get("model") or ent["model"]
                        except Exception:
                            pass
                    if not ent["name"] and '"role":"user"' in line:
                        try:
                            d = json.loads(line)
                            if d.get("type") == "message" and d["message"].get("role") == "user":
                                ent["name"] = _text_of(d["message"])[:120]
                        except Exception:
                            pass
                elif fmt == "codex":
                    if '"session_meta"' in line and not ent["cwd"]:
                        try:
                            pl = json.loads(line).get("payload", {})
                            ent["cwd"] = pl.get("cwd", "")
                            ent["model"] = pl.get("model") or ent["model"]
                            sid = pl.get("session_id") or pl.get("id") or ""
                            ent["name"] = titles.get(sid) or ent["name"]
                        except Exception:
                            pass
                    if '"total_token_usage"' in line:
                        try:
                            info = (json.loads(line).get("payload", {}).get("info") or {})
                            tot = info.get("total_token_usage") or {}
                            ent["tokens"] = int(tot.get("total_tokens", 0) or 0) or ent["tokens"]
                            ent["out"] = int(tot.get("output_tokens", 0) or 0) or ent["out"]
                        except Exception:
                            pass
                    if '"model"' in line and '"turn_context"' in line:
                        try:
                            ent["model"] = json.loads(line)["payload"].get("model") or ent["model"]
                        except Exception:
                            pass
                    if not ent["name"] and '"role":"user"' in line:
                        try:
                            pl = json.loads(line).get("payload", {})
                            if pl.get("role") == "user":
                                t = _text_of(pl)
                                if t and "<" not in t[:1]:
                                    ent["name"] = t[:120]
                        except Exception:
                            pass
                else:  # claude / generic
                    if '"cwd"' in line and not ent["cwd"]:
                        try:
                            ent["cwd"] = json.loads(line).get("cwd", "") or ent["cwd"]
                        except Exception:
                            pass
                    if '"usage"' in line or '"model"' in line:
                        try:
                            m = json.loads(line).get("message", {})
                            if isinstance(m, dict) and m.get("role") == "assistant":
                                u = m.get("usage") or {}
                                ent["tokens"] += int(u.get("input_tokens", 0) or 0) + \
                                    int(u.get("output_tokens", 0) or 0) + \
                                    int(u.get("cache_read_input_tokens", 0) or 0) + \
                                    int(u.get("cache_creation_input_tokens", 0) or 0)
                                ent["out"] += int(u.get("output_tokens", 0) or 0)
                                ent["model"] = m.get("model") or ent["model"]
                        except Exception:
                            pass
                    if not ent["name"] and '"role":"user"' in line:
                        try:
                            d = json.loads(line)
                            if d.get("message", {}).get("role") == "user":
                                ent["name"] = _text_of(d["message"])[:120]
                        except Exception:
                            pass
            ent["off"] = f.tell()
    except Exception:
        pass
    ent["size"] = st.st_size
    ent["mtime"] = st.st_mtime
    cache["files"][path] = ent
    return ent


def collect_sessions(spec: AgentSpec, cache: dict, titles: dict, since: float) -> list:
    infos = []
    for pattern in spec.roots:
        for path in glob.glob(pattern):
            try:
                m = os.path.getmtime(path)
            except Exception:
                continue
            if m < since:
                continue
            ent = parse_file(path, spec.fmt, cache, titles)
            if ent:
                infos.append(Sess(path=path, cwd=ent.get("cwd", ""), name=ent.get("name", ""),
                                  model=ent.get("model", ""), tokens=ent.get("tokens", 0),
                                  out_tokens=ent.get("out", 0), cost=ent.get("cost", 0.0), mtime=m))
    infos.sort(key=lambda s: s.mtime, reverse=True)
    return infos


# ────────────────────────────── 汇总 ──────────────────────────────


def gather(now: float) -> dict:
    cache = load_cache()
    procs = scan_procs(cache, now)
    titles = parse_codex_title_index()
    midnight = time.mktime(time.localtime(now)) - (time.localtime(now).tm_hour * 3600 +
                                                   time.localtime(now).tm_min * 60 + time.localtime(now).tm_sec)
    result = {"now": now, "agents": []}

    for spec in AGENTS:
        plist = procs.get(spec.key, [])
        infos = collect_sessions(spec, cache, titles, midnight)
        day_tokens = sum(s.tokens for s in infos)
        day_out = sum(s.out_tokens for s in infos)
        day_cost = sum(s.cost for s in infos)
        last = infos[0] if infos else None

        # 进程 ↔ 会话 关联（按 cwd 匹配，退化为最新一个）
        by_cwd = {s.cwd: s for s in infos if s.cwd}
        live: list = []
        for p in plist:
            s = by_cwd.get(p["cwd"]) or (last if len(plist) == 1 else None)
            if s is not None:
                s.procs.append(p)
                live.append((p, s))

        working = bool(plist) and (any(p["busy"] for p in plist) or
                                   (last and now - last.mtime <= ACTIVE_AGE))
        state = "working" if working else ("idle" if plist else ("recent" if infos else "off"))
        # 没有进程时，「活跃」只看文件是否在动（比如 agent 跑在别的机器/容器写同一目录）
        if not plist and last and now - last.mtime <= ACTIVE_AGE:
            state = "working"

        result["agents"].append({
            "key": spec.key, "label": spec.label, "state": state,
            "procs": plist, "live": [{"pid": p["pid"], "cwd": p["cwd"], "cpu": p["cpu"],
                                      "name": clip(s.name, NAME_LEN), "model": short_model(s.model),
                                      "tokens": s.tokens, "ago": ago(s.mtime, now)} for p, s in live],
            "last": None if not last else {"cwd": last.cwd, "name": clip(last.name, NAME_LEN),
                                           "model": short_model(last.model), "tokens": last.tokens,
                                           "ago": ago(last.mtime, now)},
            "day": {"sessions": len(infos), "tokens": day_tokens, "out": day_out, "cost": day_cost},
            "sessions": len(infos),
        })

    prune_cache(cache, now)
    save_cache(cache)
    result["day_total"] = sum(a["day"]["tokens"] for a in result["agents"])
    return result


def prune_cache(cache: dict, now: float) -> None:
    keep = {}
    for path, ent in cache["files"].items():
        try:
            if now - os.path.getmtime(path) < 86400 * 3:
                keep[path] = ent
        except Exception:
            continue
    cache["files"] = keep


# ────────────────────────────── 输出 ──────────────────────────────

ICONS = {"pi": "π", "codex": "◈", "claude": "✳", "opencode": "▣", "gemini": "✦", "aider": "Δ"}


def render_line(a: dict) -> str:
    icon = ICONS.get(a["key"], "•")
    dot = DOT_ON if a["state"] == "working" else DOT_OFF
    n = len(a["procs"])
    txt = f"{icon}{a['label']}{dot}"
    if n > 1:
        txt += f"×{n}"
    return txt, (a["state"] in ("working", "idle"))


def to_json(data: dict) -> str:
    shown = [a for a in data["agents"] if a["state"] != "off"]
    parts, any_alive = [], False
    for a in shown:
        t, alive = render_line(a)
        any_alive = any_alive or alive
        parts.append(t)
    text = " ".join(parts) if parts else "agents"

    if any(a["state"] == "working" for a in data["agents"]):
        cls = "working"
    elif any_alive:
        cls = "idle"
    else:
        cls = "off"

    lines = [f"<b>coding agents</b>   今日合计 {human(data['day_total'])} tok"]
    for a in data["agents"]:
        if a["state"] == "off":
            continue
        mark = {"working": f"{DOT_ON} 运行中", "idle": f"{DOT_OFF} 空闲",
                "recent": "◌ 今天用过", "off": "·"}[a["state"]]
        head = f"<b>{ICONS.get(a['key'],'•')} {a['label']}</b>  {mark}"
        if a["procs"]:
            head += f"  {len(a['procs'])} 进程"
        if a["day"]["tokens"]:
            head += f"  · 今日 {human(a['day']['tokens'])} tok"
        if a["day"]["cost"]:
            head += f" / ${a['day']['cost']:.2f}"
        lines.append(head)
        rows = a["live"] if a["procs"] else ([a["last"]] if a["last"] else [])
        for s in rows[:4]:
            proj = os.path.basename((s.get("cwd") or "").rstrip("/")) or "-"
            bits = [esc(proj), esc(s.get("model") or "?"), f"{human(s.get('tokens', 0))} tok", f"{esc(s.get('ago',''))} 前"]
            if "cpu" in s:
                bits.insert(1, f"cpu {s['cpu']}%")
            lines.append(f"  ├ {esc(clip(s.get('name') or '(无标题)', NAME_LEN))}")
            lines.append("  │ " + " · ".join(bits))
        if a["procs"] and not a["live"] and a["last"]:
            s = a["last"]
            lines.append(f"  └ 最近：{esc(clip(s['name'], 40))}  ({esc(s['ago'])} 前)")
    if len(lines) == 1:
        lines.append("今天没有 agent 活动")
    tooltip = "\n".join(lines)
    return json.dumps({"text": text, "class": cls, "alt": cls, "tooltip": tooltip}, ensure_ascii=False)


def to_raw(data: dict) -> str:
    parts = []
    for a in data["agents"]:
        if a["state"] == "off":
            continue
        parts.append(render_line(a)[0])
    return " ".join(parts) or "agents-"


COL = {"g": "\033[32m", "y": "\033[33m", "d": "\033[2m", "c": "\033[36m",
       "r": "\033[0m", "b": "\033[1m", "m": "\033[35m"}


def to_pretty(data: dict, color: bool = True) -> str:
    def c(k, s):
        return f"{COL[k]}{s}{COL['r']}" if color else s

    out = [c("b", f"coding agents  {time.strftime('%H:%M:%S', time.localtime(data['now']))}") +
           c("d", f"   今日合计 {human(data['day_total'])} tok")]
    for a in data["agents"]:
        if a["state"] == "off":
            continue
        mark = {"working": c("g", f"{DOT_ON} 运行中"), "idle": c("y", f"{DOT_OFF} 空闲"),
                "recent": c("d", "◌ 今天用过")}[a["state"]]
        line = f"{ICONS.get(a['key'],'•')} {c('b', a['label'].ljust(8))} {mark}"
        line += c("d", f"  {len(a['procs'])} 进程" if a["procs"] else "")
        line += c("d", f"  今日 {human(a['day']['tokens'])} tok" +
                  (f" / ${a['day']['cost']:.2f}" if a["day"]["cost"] else "") +
                  f"  {a['day']['sessions']} 会话")
        out.append(line)
        rows = a["live"] if a["procs"] else ([a["last"]] if a["last"] else [])
        for s in rows[:5]:
            proj = os.path.basename((s.get("cwd") or "").rstrip("/")) or "-"
            bits = [proj, s.get("model") or "?", f"{human(s.get('tokens',0))} tok", f"{s.get('ago','')} 前"]
            if "cpu" in s:
                bits.insert(1, f"cpu {s['cpu']}%")
            out.append("   ├ " + clip(s.get("name") or "(无标题)", NAME_LEN))
            out.append(c("d", "   │ " + " · ".join(bits)))
    if len(out) == 1:
        out.append(c("d", "  今天没有 agent 活动"))
    return "\n".join(out)


# ────────────────────────────── main ──────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description="本机 coding agent 状态探针")
    ap.add_argument("--json", action="store_true", help="waybar custom module JSON")
    ap.add_argument("--raw", action="store_true", help="单行纯文本")
    ap.add_argument("--pretty", action="store_true", help="多行纯文本（无颜色）")
    ap.add_argument("--notify", action="store_true", help="notify-send 弹报告")
    args = ap.parse_args()

    data = gather(time.time())

    if args.json:
        sys.stdout.write(to_json(data) + "\n")
    elif args.raw:
        print(to_raw(data))
    elif args.notify:
        import subprocess
        subprocess.run(["notify-send", "-t", "8000", "coding agents", to_pretty(data, color=False)])
    elif args.pretty or not sys.stdout.isatty():
        print(to_pretty(data, color=False))
    else:
        print(to_pretty(data, color=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
