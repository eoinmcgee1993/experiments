#!/usr/bin/env python3
"""Final latency+cost bench: 6 configs x 5 runs, interleaved, in the repo.

Configs: Opus 5 high, Opus 5 max, Luna high, Luna max, Luna high+fast, Luna max+fast.

Interleaved: each round runs all 6 once, order rotates per round, so no two
consecutive calls share a config and each config is spread across the whole
window. Anthropic and OpenAI serve independently, but same-window measurement
stops "when I measured" being mistaken for "which model".

Rates verified to the cent by recomputing Pawel's own bug-hunt-bench rows:
  Luna   $0.20/M in, $0.02/M cached-in, $1.20/M out   -> gpt56luna row = $1.3988 exact
  Opus 5 $5/M in, $6.25/M cache-write, $0.50/M cache-read, $25/M out
                                                      -> opus5 = $22.8775, opus5max = $26.5549 exact

Token-field asymmetry, handled explicitly below:
  codex  input_tokens INCLUDES cached  -> fresh = input - cached
  claude input_tokens EXCLUDES cached  -> fresh = input
"""
import json
import statistics as st
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "Temp" / "data" / "final_bench.json"
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
]

LUNA = dict(inp=0.20, cache_read=0.02, cache_write=0.25, out=1.20)
OPUS = dict(inp=5.00, cache_read=0.50, cache_write=6.25, out=25.00)


def codex_build(effort, fast):
    def b(q):
        cmd = [CODEX, "exec", "--json", "--skip-git-repo-check", "-s", "read-only"]
        if fast:
            cmd += ["--enable", "fast_mode"]
        return cmd + ["-m", "gpt-5.6-luna", "-c", f"model_reasoning_effort={effort}", PREFIX + q]
    return b


def claude_build(effort):
    def b(q):
        return ["claude", "-p", PREFIX + q, "--model", "claude-opus-5", "--effort", effort,
                "--output-format", "stream-json", "--include-partial-messages", "--verbose"]
    return b


CONFIGS = [
    ("opus5-high",     claude_build("high"), "claude"),
    ("luna-max",       codex_build("max", False), "codex"),
    ("opus5-max",      claude_build("max"),  "claude"),
    ("luna-high-fast", codex_build("high", True), "codex"),
    ("luna-high",      codex_build("high", False), "codex"),
    ("luna-max-fast",  codex_build("max", True), "codex"),
]

rows = []
t_start = time.monotonic()

for r in range(5):
    q = QUESTIONS[r]
    for k in range(len(CONFIGS)):
        arm, build, kind = CONFIGS[(r + k) % len(CONFIGS)]
        u = {}
        chars = 0
        t0 = time.monotonic()
        p = subprocess.Popen(build(q), cwd=str(REPO), stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True,
                             encoding="utf-8", errors="replace", bufsize=1)
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
                if t == "item.completed" and ev.get("item", {}).get("type") == "agent_message":
                    chars += len(ev["item"].get("text", ""))
                elif t == "turn.completed":
                    u = ev.get("usage", {}) or {}
            else:
                if t == "stream_event":
                    e = ev.get("event", {})
                    if e.get("type") == "content_block_delta" and e.get("delta", {}).get("type") == "text_delta":
                        chars += len(e["delta"].get("text", ""))
                elif t == "result":
                    u = ev.get("usage", {}) or {}
        p.wait()
        total = time.monotonic() - t0

        if kind == "codex":
            inp_all = u.get("input_tokens") or 0
            cached = u.get("cached_input_tokens") or 0
            fresh = max(inp_all - cached, 0)
            cw = u.get("cache_write_input_tokens") or 0
            out = u.get("output_tokens") or 0
            rt = LUNA
        else:
            fresh = u.get("input_tokens") or 0
            cached = u.get("cache_read_input_tokens") or 0
            cw = u.get("cache_creation_input_tokens") or 0
            out = u.get("output_tokens") or 0
            rt = OPUS

        cost = (fresh / 1e6 * rt["inp"] + cached / 1e6 * rt["cache_read"]
                + cw / 1e6 * rt["cache_write"] + out / 1e6 * rt["out"])

        rows.append({"round": r + 1, "arm": arm, "q": r + 1, "total_s": total,
                     "chars": chars, "ok": p.returncode == 0, "fresh_in": fresh,
                     "cached_in": cached, "cache_write": cw, "out_tok": out,
                     "cost_usd": cost,
                     "elapsed_min": round((time.monotonic() - t_start) / 60, 1)})
        print(f"r{r+1} {arm:<15} {total:>6.1f}s  ${cost:.5f}  fresh={fresh} cached={cached} "
              f"out={out} ok={rows[-1]['ok']}", flush=True)
        OUT.write_text(json.dumps(rows, indent=1), encoding="utf-8")

summary = {}
for arm, _, _ in CONFIGS:
    g = [x for x in rows if x["arm"] == arm and x["ok"]]
    if not g:
        continue
    t = [x["total_s"] for x in g]
    c = [x["cost_usd"] for x in g]
    summary[arm] = {
        "n": len(g),
        "median_s": round(st.median(t), 1),
        "avg_s": round(st.mean(t), 1),
        "min_s": round(min(t), 1),
        "max_s": round(max(t), 1),
        "median_cost_usd": round(st.median(c), 6),
        "avg_cost_usd": round(st.mean(c), 6),
        "median_out_tok": round(st.median([x["out_tok"] for x in g])),
        "median_chars": round(st.median([x["chars"] for x in g])),
    }

OUT.write_text(json.dumps({"runs": rows, "summary": summary}, indent=1), encoding="utf-8")
print("\n=== SUMMARY (medians) ===")
print(json.dumps(summary, indent=1))
