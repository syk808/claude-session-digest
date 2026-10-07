"""Daily digest of your Claude Code sessions: what you asked, and the last reply of each turn. No LLM calls.

每日摘要：把某一天所有 Claude Code 会话里「你提的要求」和「每轮最后的答复」抽成一份 Markdown（不调用大模型）。

Usage:  python session_digest.py [YYYY-MM-DD] [--max 700] [--tz 8] [--all] [--out DIR]
Output: digest_YYYY-MM-DD.md in --out (default: next to this script)

It only reads the session logs under ~/.claude/projects and never modifies them.
The digest contains your own prompts and Claude's replies, so treat the output as private.
"""
import glob
import json
import os
import sys
from datetime import datetime, timedelta, timezone

def _opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv and sys.argv.index(name) + 1 < len(sys.argv) else default


# Days are cut in this UTC offset (hours). Default +8; override with --tz or DIGEST_TZ.
BJ = timezone(timedelta(hours=float(_opt("--tz", os.environ.get("DIGEST_TZ", "8")))))
ROOT = os.path.expanduser("~/.claude/projects")
HERE = os.path.dirname(os.path.abspath(__file__))
# User-role messages that were not typed by a human (harness notices, cross-session relays, compaction summaries)
SKIP_PREFIX = ("<task-notification", "Another Claude session sent", "[Cross-session", "<system-reminder",
               "<cross-session-message", "This session is being continued", "[SYSTEM NOTIFICATION",
               "<local-command", "Caveat:", "[Request interrupted")


def text_of(msg):
    c = (msg or {}).get("content")
    if isinstance(c, str):
        return c.strip()
    out = []
    for b in c or []:
        if isinstance(b, dict) and b.get("type") == "text":
            out.append(b.get("text", ""))
    return "\n".join(out).strip()


def is_human(j, txt):
    if j.get("type") != "user" or j.get("isSidechain"):
        return False
    if (j.get("origin") or {}).get("kind") not in (None, "human"):
        return False
    if not txt or txt.startswith(SKIP_PREFIX):
        return False
    return True


def strip_reminders(t):
    while "<system-reminder>" in t and "</system-reminder>" in t:
        a, b = t.index("<system-reminder>"), t.index("</system-reminder>") + len("</system-reminder>")
        t = (t[:a] + t[b:]).strip()
    return t


def main():
    valued = {"--max", "--tz", "--out"}
    args = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] not in valued]
    day = args[0] if args else datetime.now(BJ).strftime("%Y-%m-%d")
    mx = int(_opt("--max", "700"))
    out_dir = _opt("--out", HERE)
    include_all = "--all" in sys.argv
    d0 = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=BJ)
    d1 = d0 + timedelta(days=1)
    sessions = []
    for f in glob.glob(ROOT + "/*/*.jsonl"):
        if os.path.getmtime(f) < d0.timestamp():
            continue
        title, turns, cur, desktop = "", [], None, False
        try:
            fh = open(f, encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in fh:
            try:
                j = json.loads(line)
            except ValueError:
                continue
            t = j.get("type")
            if t == "custom-title":
                title = j.get("customTitle") or title
                continue
            if t not in ("user", "assistant") or j.get("isSidechain"):
                continue
            if j.get("entrypoint") == "claude-desktop":
                desktop = True
            try:
                ts = datetime.fromisoformat(j["timestamp"].replace("Z", "+00:00")).astimezone(BJ)
            except Exception:
                continue
            txt = text_of(j.get("message"))
            if t == "user":
                txt = strip_reminders(txt)
                if is_human(j, txt):
                    cur = {"ts": ts, "ask": txt, "reply": ""}
                    turns.append(cur)
            elif cur is not None and txt:
                cur["reply"] = txt          # keep the last text block of this turn
        day_turns = [x for x in turns if d0 <= x["ts"] < d1]
        # By default keep only sessions opened in the desktop app; headless `claude -p` runs are skipped. --all keeps everything.
        if day_turns and (desktop or include_all):
            sessions.append((title or os.path.basename(f)[:8], f, day_turns))
    sessions.sort(key=lambda s: s[2][0]["ts"])
    out = [f"# {day} session digest ({len(sessions)} sessions, {sum(len(s[2]) for s in sessions)} requests)\n"]
    for title, f, ts_ in sessions:
        out.append(f"\n## {title}  ({ts_[0]['ts']:%H:%M}-{ts_[-1]['ts']:%H:%M}, {len(ts_)} requests)")
        for x in ts_:
            ask = x["ask"].replace("\n", " ")[:300]
            rep = " ".join(x["reply"].split())
            rep = (rep[:mx] + " ...[truncated]... " + rep[-200:]) if len(rep) > mx + 250 else rep
            out.append(f"\n- **{x['ts']:%H:%M} user**: {ask}\n  **reply**: {rep or '(no text reply yet / still running)'}")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"digest_{day}.md")
    open(path, "w", encoding="utf-8").write("\n".join(out))
    print(path, len(sessions), "sessions", sum(len(s[2]) for s in sessions), "asks", os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
