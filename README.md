# claude-session-digest

Turn one day of Claude Code sessions into a single Markdown digest: every request you typed, and the last text reply of each turn. No LLM calls, no dependencies, one file.

把某一天所有 Claude Code 会话压成一份 Markdown 摘要：你提的每条要求，加上每一轮最后的文字答复。不调用大模型，没有依赖，只有一个文件。

## Why

When you run many sessions in parallel, it gets hard to answer "what did I actually ask for today, and what came back?". This script reads the local session logs and lays them out per session, in time order, so a person (or another Claude session) can turn them into a daily progress table.

## Usage

```
python session_digest.py                 # today
python session_digest.py 2026-10-07      # a given day
python session_digest.py 2026-10-07 --max 400 --tz 8 --out ./out
```

| Option | Meaning |
|---|---|
| `YYYY-MM-DD` | Day to digest. Default: today. |
| `--max N` | Keep at most N characters of each reply (plus the last 200). Default 700. |
| `--tz H` | UTC offset in hours used to cut the day. Default 8. Also `DIGEST_TZ`. |
| `--all` | Include headless `claude -p` runs. By default only sessions opened in the desktop app are kept. |
| `--out DIR` | Where to write `digest_YYYY-MM-DD.md`. Default: next to the script. |

## Output

```
# 2026-10-07 session digest (3 sessions, 12 requests)

## refactor-auth  (09:12-11:40, 5 requests)

- **09:12 user**: move the token refresh into the client wrapper
  **reply**: Done. The refresh now lives in `client.py` ...
```

(The example above is made up.)

## What it reads

- `~/.claude/projects/*/*.jsonl`, read-only.
- A message counts as a request only if it was typed by a human: harness notices, cross-session relays, compaction summaries and system reminders are skipped.
- Sub-agent (sidechain) turns are skipped.

## Privacy

The digest contains your prompts and Claude's replies. `digest_*.md` is git-ignored here; keep the output out of public repositories.

## Making a progress table from it

Give the digest to a model with a prompt along these lines:

> Read `digest_<date>.md`. Produce a table per session: item, status (done / in progress / waiting on me / failed), and the evidence for that status taken from the reply. Then list what is still open, what could be improved, and what was actually useful. Do not invent anything that is not in the digest.

## License

MIT
