# -*- coding: utf-8 -*-
"""Relaunch the Qwen3.8-Max bench chain when the token-plan 5h quota resets.

2026-08-03: two CONCURRENT arms exhausted the quota in ~60 min (throttle message:
"resets at 08-03 11:58:00 UTC"). This waits until 12:00:00 UTC (+2 min buffer),
then runs the chain SEQUENTIAL (gbvb -> abhb) to halve the burn rate. If abhb
still exhausts the follow-on window, it dies with rc!=0 and the telegram says so —
rerun just abhb in the window after.
"""
import subprocess
import sys
import time
from datetime import datetime, timezone

TARGET = datetime(2026, 8, 3, 12, 0, 0, tzinfo=timezone.utc)
CHAIN = r"<WORKDIR>\Temp\scripts\run_qwen38max_20260803.py"
EDITOR = r"<WORKDIR>"


def main():
    wait = (TARGET - datetime.now(timezone.utc)).total_seconds()
    print(f"waiting {wait/60:.1f} min until {TARGET.isoformat()} (quota reset + buffer)", flush=True)
    while wait > 0:
        time.sleep(min(wait, 300))
        wait = (TARGET - datetime.now(timezone.utc)).total_seconds()
    print("quota window open - launching sequential chain", flush=True)
    rc = subprocess.call(
        [sys.executable, CHAIN, "--slug", "qwen3.8-max",
         "--api-root", "https://token-plan.ap-southeast-1.maas.aliyuncs.com/apps/anthropic",
         "--key-var", "DASHSCOPE_API_KEY", "--sequential",
         "--fallback-api-root", "https://dashscope-intl.aliyuncs.com/apps/anthropic",
         "--fallback-key-var", "DASHSCOPE_PAYG_API_KEY"],
        cwd=EDITOR)
    print(f"chain rc={rc}", flush=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
