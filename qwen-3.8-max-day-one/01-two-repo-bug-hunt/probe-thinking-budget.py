# -*- coding: utf-8 -*-
"""Thinking-budget discriminator for qwen3.8-max on the DashScope Anthropic gateway.

Follow-up to the V4-Flash effort probe (2026-08-04, 'are we sure Qwen ran high?'): the bench
sent Claude Code's native thinking param through the shim verbatim, and the raw stream
proves thinking RAN (108 blocks in the gbvb leg) - but not that the BUDGET bound.
Same design as the V4-Flash probe: one hard prompt, n=3 per budget tier, and if the
dial is ACTIVE the tiers separate in thinking volume; if INERT they collapse.

Anthropic-API constraints honored: budget_tokens >= 1024, max_tokens > budget,
temperature omitted (thinking forbids pinning it), so separation must beat noise.
Cost: ~9 calls at qwencloud list rates - well under $1.
"""
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
# 2026-08-04: the PAYG key (sk-ws-) now 403s "invalid api-key" on the intl endpoint under
# every header style - rotated/revoked since the bench's clean legs. The token-plan
# subscription endpoint + key still work (verified with a 30-token call) and the probe's
# ~9 calls are a rounding error against the reset 5h quota, so the probe runs there.
API = "https://token-plan.ap-southeast-1.maas.aliyuncs.com/apps/anthropic/v1/messages"
MODEL = "qwen3.8-max"
PROMPT = ("A 5x5 grid has its corners removed. In how many ways can you tile the remaining "
          "21 cells with exactly one L-tromino and six 1x3 straight trominoes? Reason step "
          "by step, then end with just the number.")
TIERS = [1024, 8192, 28000]
N = 3


def key():
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("DASHSCOPE_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no DASHSCOPE_API_KEY")


KEY = key()


def call(budget):
    body = {
        "model": MODEL,
        "max_tokens": budget + 4000,
        "thinking": {"type": "enabled", "budget_tokens": budget},
        "messages": [{"role": "user", "content": PROMPT}],
    }
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method="POST")
    req.add_header("Authorization", f"Bearer {KEY}")
    req.add_header("Content-Type", "application/json")
    req.add_header("anthropic-version", "2023-06-01")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read()[:200].decode(errors='replace')}", "wall": time.time() - t0}
    think = sum(len(b.get("thinking") or "") for b in data.get("content", [])
                if isinstance(b, dict) and b.get("type") == "thinking")
    text = " ".join(b.get("text") or "" for b in data.get("content", [])
                    if isinstance(b, dict) and b.get("type") == "text")
    usage = data.get("usage", {})
    return {"think_chars": think, "out_tok": usage.get("output_tokens"),
            "stop": data.get("stop_reason"), "digest": text.strip()[-40:],
            "wall": round(time.time() - t0, 1)}


def main():
    for budget in TIERS:
        rows = [call(budget) for _ in range(N)]
        errs = [r["error"] for r in rows if "error" in r]
        if errs:
            print(f"budget={budget:>6}  ERRORS: {errs}", flush=True)
            continue
        chars = [r["think_chars"] for r in rows]
        toks = [r["out_tok"] for r in rows]
        stops = [r["stop"] for r in rows]
        walls = [r["wall"] for r in rows]
        print(f"budget={budget:>6}  think_chars={chars} mean={sum(chars)//N}  "
              f"out_tok={toks}  stop={stops}  wall={walls}", flush=True)
        for r in rows:
            print(f"    digest: ...{r['digest']!r}", flush=True)


if __name__ == "__main__":
    main()
