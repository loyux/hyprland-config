#!/usr/bin/env python3
"""Display today's local Codex or Pi token usage in Waybar."""

import argparse
import fcntl
import json
import os
import sys
import time as clock
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import NamedTuple


HOME = Path.home()
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME") or HOME / ".cache") / "waybar/token-usage"
ICONS = {"codex": ("◈", "Codex"), "pi": ("π", "Pi")}
ACTIVE_SECONDS = 180  # Treat an unfinished turn with no new log events as stale.


class Usage(NamedTuple):
    input: int = 0
    output: int = 0
    cache_read: int = 0

    def __add__(self, other):
        return Usage(self.input + other.input, self.output + other.output,
                     self.cache_read + other.cache_read)


def load_json(path):
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def session_files(client):
    if client == "codex":
        base = Path(os.environ.get("CODEX_HOME") or HOME / ".codex")
        roots = [base / "sessions", base / "archived_sessions"]
        pattern = "rollout-*.jsonl"
    else:
        config = Path(os.environ.get("XDG_CONFIG_HOME") or HOME / ".config")
        agent_dirs = [HOME / ".pi/agent", config / "pi"]
        if agent_dir := os.environ.get("PI_CODING_AGENT_DIR"):
            agent_dirs.append(Path(agent_dir).expanduser())
        roots = [agent_dir / "sessions" for agent_dir in agent_dirs]
        for agent_dir in agent_dirs:
            configured = load_json(agent_dir / "settings.json")
            if isinstance(configured.get("sessionDir"), str):
                path = Path(configured["sessionDir"]).expanduser()
                if path.is_absolute():
                    roots.append(path)
        if session_dir := os.environ.get("PI_CODING_AGENT_SESSION_DIR"):
            roots.append(Path(session_dir).expanduser())
        pattern = "*.jsonl"

    for root in dict.fromkeys(path.resolve() for path in roots):
        yield from root.rglob(pattern)


def token_count(value):
    return value if type(value) is int and value > 0 else 0


def event_time(value):
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).timestamp()
        except (ValueError, OverflowError, OSError):
            return 0
    if type(value) in (int, float):
        # Pi message timestamps are milliseconds, while ISO timestamps include a timezone.
        return value / 1000 if value >= 100_000_000_000 else value
    return 0


def events(stream, *markers):
    for line in stream:
        if not line.endswith(b"\n") or not any(marker in line for marker in markers):
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict):
            yield entry


def codex_usage(stream, start, end):
    total = Usage()
    working = False
    previous_snapshot = None
    saw_usage_records = False
    seen_responses = set()
    for entry in events(stream, b'"event_msg"', b'"token_count"', b'"token_usage_record"'):
        payload = entry.get("payload") or entry
        if not isinstance(payload, dict):
            continue
        kind = payload.get("type")
        if entry.get("type") == "event_msg":
            if kind == "task_started":
                working = True
            elif kind in ("task_complete", "turn_aborted"):
                working = False
        if entry.get("type") == "token_usage_record":
            saw_usage_records = True
            usage = payload.get("usage")
            if response_id := payload.get("response_id"):
                response = json.dumps([response_id, payload.get("thread_token_usage")], sort_keys=True)
                if response in seen_responses:
                    continue
                seen_responses.add(response)
        else:
            if entry.get("type") == "response_item":
                payload = payload.get("payload", payload)
                if not isinstance(payload, dict):
                    continue
            if saw_usage_records or payload.get("type") != "token_count":
                continue
            info = payload.get("info") or {}
            if not isinstance(info, dict):
                continue
            usage = info.get("last_token_usage")
            snapshot = info.get("total_token_usage")
            # A rate-limit update can repeat the previous request's usage.
            if snapshot and snapshot == previous_snapshot:
                continue
            if snapshot:
                previous_snapshot = snapshot

        if not isinstance(usage, dict) or not start <= event_time(entry.get("timestamp")) < end:
            continue
        input_tokens = token_count(usage.get("input_tokens"))
        cache_read = min(input_tokens, token_count(usage.get("cached_input_tokens")))
        total += Usage(input_tokens, token_count(usage.get("output_tokens")), cache_read)
    return total, {}, working


def pi_usage(stream, start, end):
    unkeyed = Usage()
    keyed = {}
    working = False
    for entry in events(stream, b'"usage"', b'"message"'):
        kind = entry.get("type")
        message = entry.get("message") or {}
        if not isinstance(message, dict):
            continue
        if kind == "message":
            role = message.get("role")
            if role == "user":
                working = True
            elif role == "assistant":
                working = message.get("stopReason") == "toolUse"
        if kind == "message" and message.get("role") in ("assistant", "toolResult"):
            usage = message.get("usage")
        elif kind in ("compaction", "branch_summary", "usage"):
            usage = entry.get("usage")
        else:
            continue
        timestamp = event_time(entry.get("timestamp") or message.get("timestamp"))
        if not isinstance(usage, dict) or not start <= timestamp < end:
            continue
        cache_read = token_count(usage.get("cacheRead"))
        input_tokens = token_count(usage.get("input")) + cache_read + token_count(usage.get("cacheWrite"))
        counts = Usage(input_tokens, token_count(usage.get("output")), cache_read)
        if response_id := message.get("responseId"):
            key = ["response", message.get("provider"), response_id, timestamp]
        elif entry_id := entry.get("id"):
            key = ["entry", entry_id, timestamp]
        else:
            unkeyed += counts
            continue
        # A Pi fork can include copies of its parent's messages.
        keyed.setdefault(json.dumps(key), counts)
    return unkeyed, keyed, working


def collect_today(client):
    today = date.today()
    start = datetime.combine(today, time.min).timestamp()
    end = datetime.combine(today + timedelta(days=1), time.min).timestamp()
    active_since = clock.time() - ACTIVE_SECONDS
    cache_path = CACHE_DIR / f"{client}.json"
    parser = codex_usage if client == "codex" else pi_usage
    previous = load_json(cache_path)
    cached_files = previous.get("files", {}) if previous.get("day_start") == start else {}
    files = {}
    seen_rollouts = set()
    working = False
    for path in session_files(client):
        try:
            stat = path.stat()
            if stat.st_mtime < min(start, active_since):
                continue
            identity = f"{stat.st_dev}:{stat.st_ino}"
            if identity in files or (client == "codex" and path.name in seen_rollouts):
                continue
            fingerprint = [stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns]
            cached = cached_files.get(identity, {})
            if cached.get("fingerprint") == fingerprint and "working" in cached:
                files[identity] = cached
            else:
                with path.open("rb") as stream:
                    unkeyed, keyed, file_working = parser(stream, start, end)
                files[identity] = {"fingerprint": fingerprint, "unkeyed": unkeyed,
                                   "keyed": keyed, "working": file_working}
            if stat.st_mtime >= active_since and path.parent.name != "archived_sessions":
                working |= files[identity]["working"]
            if client == "codex":
                seen_rollouts.add(path.name)
        except FileNotFoundError:
            # A session can move to the archive during a refresh.
            continue

    if files != cached_files or previous.get("day_start") != start:
        tmp = cache_path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"day_start": start, "files": files}, separators=(",", ":")))
        tmp.replace(cache_path)

    total = Usage()
    unique = {}
    for data in files.values():
        total += Usage(*data["unkeyed"])
        for key, counts in data["keyed"].items():
            unique.setdefault(key, counts)
    for counts in unique.values():
        total += Usage(*counts)
    return total, working


def millions(tokens):
    return f"{tokens / 1_000_000:.2f}M"


def render(client, usage, working):
    icon, name = ICONS[client]
    if usage is None:
        return {"text": f"{icon} —", "tooltip": f"{name} 今日用量暂不可用", "class": "unavailable"}
    total = usage.input + usage.output
    hit = f"{usage.cache_read / usage.input:.1%}" if usage.input else "—"
    tooltip = (f"<b>{name} · 今日 token</b>\n"
               f"总计  {millions(total)}\n"
               f"输入  {millions(usage.input)}（含缓存）\n"
               f"输出  {millions(usage.output)}\n"
               f"缓存命中率  {hit}")
    return {"text": f"{icon} {millions(total)}", "tooltip": tooltip,
            "class": "working" if working else "idle"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("client", choices=ICONS)
    client = parser.parse_args().client
    try:
        CACHE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
        with (CACHE_DIR / f"{client}.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            usage, working = collect_today(client)
    except OSError as error:
        print(f"{client} token usage: {error.strerror}", file=sys.stderr)
        usage, working = None, False
    print(json.dumps(render(client, usage, working), ensure_ascii=False))


if __name__ == "__main__":
    main()
