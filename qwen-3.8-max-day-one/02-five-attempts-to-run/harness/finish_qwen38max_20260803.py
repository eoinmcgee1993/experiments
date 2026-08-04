# -*- coding: utf-8 -*-
"""Finisher for the hot-swapped Qwen3.8-Max run: wait for both arm runners, then judge
both benches CONCURRENTLY (codex gpt-5.5, blind), then Telegram the /105 totals.

Replaces the chain's tail after the 14:46 surgery (chain killed to hot-swap the proxy;
arms relaunched by hand). Judge retry: one re-attempt per bench if totals don't parse
(codex judges can return schema-invalid output; harness records judge_failed, retry passes).
"""
import glob
import json
import os
import subprocess
import sys
import time

EDITOR = r"<WORKDIR>"
OUT = os.path.join(EDITOR, "Temp", "output")
GBVB_PID, ABHB_PID = int(sys.argv[1]), int(sys.argv[2])

SCORING_DIRS = {
    "gbvb": os.path.join(EDITOR, "experiments", "grok-build-vscode-benchmark", "results", "scoring"),
    "abhb": os.path.join(EDITOR, "experiments", "accredia-bug-hunt-bench", "results", "scoring"),
}
CONFIGS = {
    "gbvb": os.path.join(EDITOR, "Temp", "scripts", "gbvb_score_qwen38max_20260803.json"),
    "abhb": os.path.join(EDITOR, "Temp", "scripts", "abhb_score_qwen38max_20260803.json"),
}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def telegram(msg):
    try:
        subprocess.call([sys.executable, os.path.join(EDITOR, "tools", "telegram_send.py"), msg],
                        cwd=EDITOR, timeout=60)
    except Exception as exc:
        log(f"telegram failed: {exc}")


def alive(pid):
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
    return str(pid) in out.stdout


def newest_totals(bench):
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
        return None, os.path.basename(d)
    return None, None


def judge(bench):
    return subprocess.Popen(
        [sys.executable, os.path.join(EDITOR, "tools", "accredia_score.py"),
         "score", "--confirm-paid-judging", "--config", CONFIGS[bench]],
        cwd=EDITOR,
        stdout=open(os.path.join(OUT, f"judge-{bench}-qwen38max.log"), "a", encoding="utf-8"),
        stderr=subprocess.STDOUT)


def main():
    deadline = time.time() + 3 * 3600
    log(f"waiting on arm runners gbvb={GBVB_PID} abhb={ABHB_PID}")
    while time.time() < deadline and (alive(GBVB_PID) or alive(ABHB_PID)):
        time.sleep(30)
    if alive(GBVB_PID) or alive(ABHB_PID):
        telegram("Qwen3.8-Max bench: arms still running after 3h - finisher timed out, check logs.")
        sys.exit(1)
    log("both arms done - launching both judges concurrently")
    telegram("Qwen3.8-Max bench: both repo legs finished on the pay-as-you-go path. "
             "Blind judging (codex gpt-5.5) running on both benches concurrently.")

    procs = {bench: judge(bench) for bench in ("gbvb", "abhb")}
    lines = []
    combined = {}
    for bench, p in procs.items():
        rc = p.wait()
        totals, run_id = newest_totals(bench)
        if not totals:
            log(f"{bench} judge rc={rc}, totals missing - one retry")
            rc = judge(bench).wait()
            totals, run_id = newest_totals(bench)
        if totals:
            combined[bench] = totals
            lines.append(
                f"{bench}: {totals.get('fixed_match', '?')}/{totals.get('planted_total', '?')} strict"
                f" +{totals.get('fixed_partial', 0)} partial, +{totals.get('extra_genuine', 0)} extras,"
                f" {totals.get('claimed_only', 0)} claimed-only ({run_id})")
        else:
            lines.append(f"{bench}: judge rc={rc}, totals STILL missing - check scoring dirs")

    if len(combined) == 2:
        strict = sum(t.get("fixed_match", 0) for t in combined.values())
        lines.insert(0, f"COMBINED: {strict}/105 strict")
    telegram("Qwen3.8-Max bench COMPLETE\n" + "\n".join(lines))
    print("\n".join(lines))
    log("FINISHER COMPLETE")


if __name__ == "__main__":
    main()
