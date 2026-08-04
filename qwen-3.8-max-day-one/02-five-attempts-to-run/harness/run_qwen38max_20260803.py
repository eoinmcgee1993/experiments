# -*- coding: utf-8 -*-
"""Qwen3.8-Max bug-hunt arm (Pawel 2026-08-03, tweet 2084100707423289643).

Chain: dedicated proxy on :8792 -> gbvb + abhb arms CONCURRENT (same shape as the
07-31/08-01 waves; wall-clock carries the concurrency caveat) -> blind judging
(codex gpt-5.5, serial) -> Telegram summary with per-bench totals + OR credits delta.

Slug is required (--slug) because the model was announced hours before OR listed it;
the poller (poll_qwen38_20260803.py) discovers the slug and calls this script.
Proxy is spawned DETACHED so nothing kills it mid-run (the dsv4flash :8788 lesson).
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
import urllib.request

EDITOR = r"<WORKDIR>"
OUT = os.path.join(EDITOR, "Temp", "output")
PROXY = os.path.join(EDITOR, "Temp", "scripts", "kimi_proxy2.py")
ARM = "qwen38max"
PORT = 8792
DETACHED = 0x00000008 | 0x00000200

SCORING_DIRS = {
    "gbvb": os.path.join(EDITOR, "experiments", "grok-build-vscode-benchmark", "results", "scoring"),
    "abhb": os.path.join(EDITOR, "experiments", "accredia-bug-hunt-bench", "results", "scoring"),
}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def telegram(msg):
    try:
        subprocess.call([sys.executable, os.path.join(EDITOR, "tools", "telegram_send.py"), msg],
                        cwd=EDITOR, timeout=60)
    except Exception as exc:
        log(f"telegram failed: {exc}")


def or_key():
    for line in open(os.path.join(EDITOR, ".env"), encoding="utf-8"):
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    return None


def or_balance():
    """OpenRouter remaining credits (total_credits - total_usage), or None."""
    key = or_key()
    if not key:
        return None
    try:
        req = urllib.request.Request("https://openrouter.ai/api/v1/credits",
                                     headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)["data"]
        return float(data["total_credits"]) - float(data["total_usage"])
    except Exception as exc:
        log(f"credits fetch failed: {exc}")
        return None


def proxy_alive():
    """Local socket connect only. A GET / through the proxy round-trips the UPSTREAM,
    and the maas host answers slower than a sane timeout - the 09:02 launch aborted on
    exactly that false negative (and the retry double-bound :8792 via SO_REUSEADDR)."""
    import socket
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=3):
            return True
    except OSError:
        return False


def newest_totals(bench):
    """Totals for ARM from the newest scoring run in this bench's results dir."""
    dirs = sorted(glob.glob(os.path.join(SCORING_DIRS[bench], "*-score-*")))
    for d in reversed(dirs):
        summary = os.path.join(d, "summary.json")
        if not os.path.exists(summary):
            continue
        try:
            data = json.load(open(summary, encoding="utf-8"))
        except Exception:
            continue
        for arm in data.get("arms", []):
            if "qwen" in (arm.get("display_name", "") + arm.get("arm", "")).lower():
                return arm.get("totals", {}), os.path.basename(d)
        return None, os.path.basename(d)  # newest run exists but arm absent -> stop
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True,
                    help="upstream model id (OR slug, or qwen3.8-max on the coding base)")
    ap.add_argument("--api-root", default=None,
                    help="non-OR upstream root, e.g. "
                         "https://coding-intl.dashscope.aliyuncs.com/apps/anthropic")
    ap.add_argument("--key-var", default="OPENROUTER_API_KEY")
    ap.add_argument("--sequential", action="store_true",
                    help="run gbvb then abhb instead of concurrently - halves the burn rate "
                         "against the token-plan 5h quota (two concurrent arms exhausted it "
                         "in ~60min on 2026-08-03) and matches the sequential 07-26 baselines")
    ap.add_argument("--fallback-api-root", default=None,
                    help="on any failed leg, restart the proxy on this root and rerun that leg "
                         "once (Pawel 2026-08-03: pay-as-you-go escape hatch from quota walls)")
    ap.add_argument("--fallback-key-var", default=None)
    ap.add_argument("--skip-judging", action="store_true")
    args = ap.parse_args()
    on_openrouter = args.key_var == "OPENROUTER_API_KEY" and not args.api_root

    os.makedirs(OUT, exist_ok=True)
    balance_before = or_balance() if on_openrouter else None
    log(f"OR balance before arms: {balance_before}")

    if not proxy_alive():
        proxy_cmd = [sys.executable, PROXY, "--port", str(PORT), "--model", args.slug,
                     "--key-var", args.key_var]
        if args.api_root:
            # non-OR upstream: no OR reasoning extension; CLI's native thinking param passes verbatim
            proxy_cmd += ["--api-root", args.api_root]
        else:
            proxy_cmd += ["--reasoning-effort", "high"]
        log(f"starting proxy :{PORT} -> {args.slug} @ {args.api_root or 'openrouter'}, detached")
        subprocess.Popen(
            proxy_cmd,
            cwd=EDITOR,
            stdout=open(os.path.join(OUT, f"proxy-{PORT}.log"), "a", encoding="utf-8"),
            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=DETACHED)
        time.sleep(6)
    if not proxy_alive():
        telegram(f"Qwen3.8-Max bench: proxy :{PORT} failed to start - chain aborted")
        sys.exit(1)
    log("proxy alive")

    def launch(bench):
        sink = open(os.path.join(OUT, f"{ARM}-{bench}.log"), "a", encoding="utf-8")
        sink.write(f"\n=== {ARM} run ({args.slug}) ===\n")
        sink.flush()
        log(f"launching {bench}/{ARM}")
        return subprocess.Popen(
            [sys.executable, os.path.join(EDITOR, "tools", "bug_hunt_bench.py"),
             "run", bench, ARM],
            cwd=EDITOR, stdout=sink, stderr=subprocess.STDOUT)

    rcs = {}
    if args.sequential:
        for bench in ("gbvb", "abhb"):
            rcs[bench] = launch(bench).wait()
            log(f"{bench}/{ARM} done rc={rcs[bench]}")
    else:
        procs = {bench: launch(bench) for bench in ("gbvb", "abhb")}
        for bench, p in procs.items():
            rcs[bench] = p.wait()
            log(f"{bench}/{ARM} done rc={rcs[bench]}")

    failed = [b for b, rc in rcs.items() if rc != 0]
    if failed and args.fallback_api_root and args.fallback_key_var:
        log(f"FAILOVER: legs {failed} failed - swapping proxy to {args.fallback_api_root}")
        telegram(f"Qwen3.8-Max bench: leg(s) {', '.join(failed)} failed on the token-plan path - "
                 f"rerunning on the pay-as-you-go endpoint (Pawel-authorized fallback).")
        kill = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        for line in kill.stdout.splitlines():
            if f":{PORT}" in line and "LISTENING" in line:
                pid = line.split()[-1]
                subprocess.call(["taskkill", "/PID", pid, "/F"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        subprocess.Popen(
            [sys.executable, PROXY, "--port", str(PORT), "--model", args.slug,
             "--api-root", args.fallback_api_root, "--key-var", args.fallback_key_var],
            cwd=EDITOR,
            stdout=open(os.path.join(OUT, f"proxy-{PORT}.log"), "a", encoding="utf-8"),
            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=DETACHED)
        time.sleep(6)
        if proxy_alive():
            for bench in failed:
                rcs[bench] = launch(bench).wait()
                log(f"{bench}/{ARM} FAILOVER rerun done rc={rcs[bench]}")
        else:
            log("FAILOVER proxy failed to start - keeping original rcs")

    balance_after = or_balance() if on_openrouter else None
    delta = (None if balance_before is None or balance_after is None
             else round(balance_before - balance_after, 4))
    log(f"OR balance after arms: {balance_after} (delta {delta})")
    cost_line = f", OR credits delta ${delta}" if delta is not None else ""
    telegram(f"Qwen3.8-Max bench: arms done (gbvb rc={rcs['gbvb']}, abhb rc={rcs['abhb']})"
             f"{cost_line}. Judging starts (codex gpt-5.5, blind).")

    if args.skip_judging:
        log("skip-judging set - chain ends here")
        return

    lines = []
    for bench, cfg in [("gbvb", "gbvb_score_qwen38max_20260803.json"),
                       ("abhb", "abhb_score_qwen38max_20260803.json")]:
        label = f"{bench}-{ARM}"
        log(f"=== JUDGE {label} start ===")
        rc = subprocess.call(
            [sys.executable, os.path.join(EDITOR, "tools", "accredia_score.py"),
             "score", "--confirm-paid-judging", "--config",
             os.path.join(EDITOR, "Temp", "scripts", cfg)],
            cwd=EDITOR,
            stdout=open(os.path.join(OUT, f"judge-{label}.log"), "a", encoding="utf-8"),
            stderr=subprocess.STDOUT)
        log(f"=== JUDGE {label} done rc={rc} ===")
        totals, run_id = newest_totals(bench)
        if totals:
            lines.append(
                f"{bench}: {totals.get('fixed_match', '?')}/{totals.get('planted_total', '?')} strict"
                f" +{totals.get('fixed_partial', 0)} partial, +{totals.get('extra_genuine', 0)} extras,"
                f" {totals.get('claimed_only', 0)} claimed-only ({run_id})")
        else:
            lines.append(f"{bench}: judge rc={rc}, no totals parsed - check scoring dir")

    telegram("Qwen3.8-Max bench COMPLETE\n" + "\n".join(lines) +
             (f"\nOR credits delta ${delta}." if delta is not None else "") +
             "\nVerdicts in the benches' results/scoring dirs.")
    log("QWEN38MAX CHAIN COMPLETE")


if __name__ == "__main__":
    main()
