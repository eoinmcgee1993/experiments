#!/usr/bin/env python3
"""In-session (warm) matrix: 4 configs x 3 replicate sessions x 6 turns = 72 calls.

Why replicates: the single-session run put Luna-high (0.52c) ABOVE Luna-max
(0.27c), which is mechanically backwards. Cause was cache-hit variance between
two lone sessions (Luna-high ran 35-75% hit, Luna-max 70-90%). Cache hit varies
per session, so the fix is more SESSIONS, not more turns.

Interleaving: 12 live sessions are advanced one turn per round, order rotated
each round. No two consecutive calls share a config, every session sees the
same question at the same turn depth, and server drift spreads evenly.

Adds Opus 5 max, which the first warm run was missing.
"""
import json
import statistics as st
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "Temp" / "data" / "warm_matrix.json"
ERRLOG = REPO / "Temp" / "output" / "warm_matrix_stderr.log"
CODEX = str(Path.home() / ".vscode" / "extensions"
            / "openai.chatgpt-26.727.40816-win32-x64" / "bin" / "windows-x86_64" / "codex.exe")

PREFIX = ("Answer directly from your own knowledge in 2-3 sentences. "
          "Do not run any commands, do not read any files, do not use any tools. ")

QUESTIONS = [
    "What is AGENTS.md and where does it go in a repository?",
    "What does a reasoning effort setting actually control?",
    "What is the difference between GPT-5.6 Sol and GPT-5.6 Luna?",
    "What is MCP and why would a coding agent need it?",
    "What is the risk of running an autonomous agent loop with no human in the loop?",
    "What does context compaction do in a coding agent?",
]

LUNA = dict(inp=0.20, cr=0.02, cw=0.25, out=1.20)
OPUS = dict(inp=5.00, cr=0.50, cw=6.25, out=25.00)

CONFIGS = [
    ("luna-high",  "codex",  "high", LUNA),
    ("opus5-high", "claude", "high", OPUS),
    ("luna-max",   "codex",  "max",  LUNA),
    ("opus5-max",  "claude", "max",  OPUS),
]
REPLICATES = 3
TURNS = 6

sessions = [{"cfg": c, "rep": r, "id": None, "dead": False}
            for c in CONFIGS for r in range(REPLICATES)]


def build(cfg, effort, sess, q, turn):
    name, kind, _, _ = cfg
    if kind == "codex":
        if turn == 1:
            return [CODEX, "exec", "--json", "--skip-git-repo-check", "-s", "read-only",
                    "-m", "gpt-5.6-luna", "-c", f"model_reasoning_effort={effort}", PREFIX + q]
        return [CODEX, "exec", "resume", sess["id"], "--json", "--skip-git-repo-check",
                "-m", "gpt-5.6-luna", "-c", f"model_reasoning_effort={effort}", PREFIX + q]
    cmd = ["claude", "-p", PREFIX + q, "--model", "claude-opus-5", "--effort", effort,
           "--output-format", "stream-json", "--include-partial-messages", "--verbose"]
    if turn > 1:
        cmd += ["--resume", sess["id"]]
    return cmd


rows = []
t_start = time.monotonic()

for turn in range(1, TURNS + 1):
    q = QUESTIONS[turn - 1]
    for k in range(len(sessions)):
        sess = sessions[(turn + k) % len(sessions)]
        if sess["dead"]:
            continue
        name, kind, effort, rt = sess["cfg"]
        u, chars = {}, 0
        errf = open(ERRLOG, "a", encoding="utf-8")
        t0 = time.monotonic()
        p = subprocess.Popen(build(sess["cfg"], effort, sess, q, turn), cwd=str(REPO),
                             stdout=subprocess.PIPE, stderr=errf, stdin=subprocess.DEVNULL,
                             text=True, encoding="utf-8", errors="replace", bufsize=1)
        for line in p.stdout:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = ev.get("type")
            if kind == "codex":
                if t == "thread.started" and sess["id"] is None:
                    sess["id"] = ev.get("thread_id")
                elif t == "item.completed" and ev.get("item", {}).get("type") == "agent_message":
                    chars += len(ev["item"].get("text", ""))
                elif t == "turn.completed":
                    u = ev.get("usage", {}) or {}
            else:
                if t == "system" and ev.get("subtype") == "init" and sess["id"] is None:
                    sess["id"] = ev.get("session_id")
                elif t == "stream_event":
                    e = ev.get("event", {})
                    if e.get("type") == "content_block_delta" and e.get("delta", {}).get("type") == "text_delta":
                        chars += len(e["delta"].get("text", ""))
                elif t == "result":
                    u = ev.get("usage", {}) or {}
        p.wait()
        errf.close()
        ok = p.returncode == 0
        if not ok or sess["id"] is None:
            sess["dead"] = True

        if kind == "codex":
            inp = u.get("input_tokens") or 0
            cached = u.get("cached_input_tokens") or 0
            fresh = max(inp - cached, 0)
            cw = u.get("cache_write_input_tokens") or 0
        else:
            fresh = u.get("input_tokens") or 0
            cached = u.get("cache_read_input_tokens") or 0
            cw = u.get("cache_creation_input_tokens") or 0
            inp = fresh + cached
        out = u.get("output_tokens") or 0
        cost = fresh/1e6*rt["inp"] + cached/1e6*rt["cr"] + cw/1e6*rt["cw"] + out/1e6*rt["out"]

        rows.append({"arm": name, "rep": sess["rep"], "turn": turn,
                     "total_s": round(time.monotonic() - t0, 1), "in_tok": inp,
                     "cached": cached, "fresh": fresh, "cache_write": cw, "out_tok": out,
                     "cost_usd": cost, "ok": ok,
                     "elapsed_min": round((time.monotonic() - t_start) / 60, 1)})
        hit = round(100 * cached / inp, 1) if inp else 0
        print(f"t{turn} {name:<11} r{sess['rep']} {rows[-1]['total_s']:>6.1f}s "
              f"in={inp:<7} hit={hit:>5.1f}% out={out:<5} ${cost:.5f} ok={ok}", flush=True)
        OUT.write_text(json.dumps(rows, indent=1), encoding="utf-8")

summary = {}
for name, _, _, _ in CONFIGS:
    warm = [r for r in rows if r["arm"] == name and r["ok"] and r["turn"] > 1]
    if not warm:
        continue
    summary[name] = {
        "n_warm_calls": len(warm),
        "median_s": round(st.median([r["total_s"] for r in warm]), 1),
        "median_cost_c": round(st.median([r["cost_usd"] for r in warm]) * 100, 3),
        "mean_cost_c": round(st.mean([r["cost_usd"] for r in warm]) * 100, 3),
        "median_hit_pct": round(st.median([100*r["cached"]/r["in_tok"] for r in warm if r["in_tok"]]), 1),
        "median_out_tok": round(st.median([r["out_tok"] for r in warm])),
    }

OUT.write_text(json.dumps({"runs": rows, "summary": summary}, indent=1), encoding="utf-8")
print("\n=== WARM SUMMARY (turns 2-6, 3 sessions per config) ===")
print(json.dumps(summary, indent=1))
