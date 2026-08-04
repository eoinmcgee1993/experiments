# -*- coding: utf-8 -*-
"""Watch OpenRouter for Qwen3.8-Max, then fire the bug-hunt chain automatically.

Qwen announced Qwen3.8-Max 2026-08-03 ~02:15 UTC (tweet 2084100707423289643); the API is
live on Alibaba's own Qwen Cloud (no key held) but the OR listing lags. This poller checks
the public OR models list every 15 min for up to 48 h. When a matching slug appears it:

  1. syncs the qwen38max arm in tools/bug_hunt_bench.json to OR reality
     (prices from the OR listing; model string drops to bare claude-opus-5 if the
     OR-served context is < 900K - the [1m] assumption would overrun a trimmed window),
  2. tells Pawel via Telegram that the chain is firing,
  3. runs run_qwen38max_20260803.py --slug <slug> inline (arms + blind judging + report).

Launched DETACHED so it survives Claude session restarts (dsv4pro precedent).
Log: Temp/output/poll_qwen38.log. Kill: taskkill on the pythonw/py PID in the log header.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

EDITOR = r"<WORKDIR>"
CONFIG = os.path.join(EDITOR, "tools", "bug_hunt_bench.json")
CHAIN = os.path.join(EDITOR, "Temp", "scripts", "run_qwen38max_20260803.py")
POLL_S = 900
MAX_H = 48


def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def telegram(msg):
    try:
        subprocess.call([sys.executable, os.path.join(EDITOR, "tools", "telegram_send.py"), msg],
                        cwd=EDITOR, timeout=60)
    except Exception as exc:
        log(f"telegram failed: {exc}")


def find_model():
    """Return the OR model dict for Qwen3.8-Max, or None."""
    try:
        with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=60) as resp:
            models = json.load(resp)["data"]
    except Exception as exc:
        log(f"models fetch failed: {exc}")
        return None
    hits = [m for m in models
            if "qwen3.8" in m["id"].lower() and "max" in m["id"].lower()
            and not m["id"].lower().endswith(":free")]
    if not hits:
        return None
    # prefer the plain slug over dated/preview variants
    hits.sort(key=lambda m: len(m["id"]))
    return hits[0]


def sync_arm_config(model):
    """Point the qwen38max arm at OR reality: list prices, context-safe model string."""
    with open(CONFIG, encoding="utf-8") as fh:
        cfg = json.load(fh)
    arm = cfg["arms"]["qwen38max"]
    pricing = model.get("pricing", {})

    def per_million(field):
        try:
            return round(float(pricing.get(field)) * 1_000_000, 6)
        except (TypeError, ValueError):
            return None

    prices = {
        "input": per_million("prompt"),
        "cache_write": 0.0,
        "cache_read": per_million("input_cache_read"),
        "output": per_million("completion"),
    }
    for key, value in prices.items():
        if value is not None:
            arm["prices_per_million"][key] = value

    ctx = model.get("context_length") or 0
    if ctx and ctx < 900_000:
        arm["model"] = "claude-opus-5"
        arm["notes"] += (f"; OR serves ctx={ctx} (<900K) so the CLI model string dropped to bare"
                         f" claude-opus-5 (200K assumption) - set by the poller")
    arm["notes"] += (f"; OR listed {model['id']} ctx={ctx}"
                     f" prompt={pricing.get('prompt')} completion={pricing.get('completion')}"
                     f" cache_read={pricing.get('input_cache_read')} - synced by poller "
                     + time.strftime("%Y-%m-%d %H:%M"))
    with open(CONFIG, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(cfg, fh, indent=2)
        fh.write("\n")
    log(f"arm config synced: ctx={ctx} prices={prices}")


def main():
    log(f"poller start pid={os.getpid()} (every {POLL_S}s, max {MAX_H}h)")
    deadline = time.time() + MAX_H * 3600
    while time.time() < deadline:
        model = find_model()
        if model:
            slug = model["id"]
            log(f"FOUND {slug} ctx={model.get('context_length')} pricing={model.get('pricing')}")
            sync_arm_config(model)
            telegram(f"Qwen3.8-Max is live on OpenRouter as {slug} - firing the 105-bug bench "
                     f"chain now (gbvb+abhb concurrent, then blind codex judging). "
                     f"Results land here when done.")
            rc = subprocess.call([sys.executable, CHAIN, "--slug", slug], cwd=EDITOR)
            log(f"chain rc={rc}")
            sys.exit(rc)
        time.sleep(POLL_S)
    log("48h deadline hit - no OR listing")
    telegram("Qwen3.8-Max: still not on OpenRouter after 48h of polling. Chain is staged - "
             "options: keep waiting (relaunch poller), or get a DashScope/Qwen Cloud API key "
             "for a direct run.")
    sys.exit(2)


if __name__ == "__main__":
    main()
