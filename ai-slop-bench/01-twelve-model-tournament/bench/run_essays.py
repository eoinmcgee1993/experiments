"""Collect essays: one raw API call per (arm, prompt, sample). No system prompt, nothing beyond the task.

Variants (bench/config.json): `bare` sends the task text only; `steered` appends one line of style instruction.
Output:  <essays_dir>/<arm>/<prompt>-<n>.md        the model's text, byte-for-byte as returned
         <receipts_dir>/<arm>/<prompt>-<n>.json    full request body (= the model's entire context), full raw
                                                   response, normalised usage, wall time, sha256 of the essay
Idempotent: an existing receipt is never re-run. Concurrency across vendors via a thread pool.
Usage: python bench/run_essays.py [--variant bare|steered] [--arms a,b] [--workers 8]
"""
import argparse, hashlib, json, pathlib, sys, time, concurrent.futures as cf
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from transports import TRANSPORTS, usage_summary  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "bench/config.json").read_text(encoding="utf-8"))


def one(variant, arm, a, pid, prompt, n):
    v = CFG["variants"][variant]
    out_md = ROOT / v["essays_dir"] / arm / f"{pid}-{n}.md"
    out_rc = ROOT / v["receipts_dir"] / arm / f"{pid}-{n}.json"
    if out_rc.exists():
        return f"skip {variant}/{arm}/{pid}-{n}"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_rc.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        text, raw, body = TRANSPORTS[a["transport"]](a["model"], prompt, **a.get("params", {}))
    except Exception as e:  # noqa: BLE001
        return f"FAIL {variant}/{arm}/{pid}-{n}: {e}"
    wall = round(time.time() - t0, 1)
    if not text.strip():
        return f"FAIL {variant}/{arm}/{pid}-{n}: empty text"
    out_md.write_text(text, encoding="utf-8", newline="\n")
    rc = {"variant": variant, "arm": arm, "label": a["label"], "vendor": a["vendor"], "transport": a["transport"],
          "model_requested": a["model"], "serving_path": a["serving_path"], "prompt_id": pid, "sample": n,
          "prompt_text": prompt, "run_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "wall_s": wall,
          "request_body": body, "usage": usage_summary(a["transport"], raw),
          "essay_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "essay_words": len(text.split()),
          "response_raw": raw}
    out_rc.write_text(json.dumps(rc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    return (f"ok   {variant}/{arm}/{pid}-{n}  {rc['essay_words']}w  {wall}s  "
            f"reasoning={rc['usage'].get('reasoning_tokens')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="bare", choices=list(CFG["variants"]))
    ap.add_argument("--arms", default=",".join(CFG["arms"]))
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    suffix = CFG["variants"][args.variant]["suffix"]
    prompts = {p.stem: p.read_text(encoding="utf-8").strip() + suffix
               for p in sorted((ROOT / "prompts").glob("*.txt"))}
    jobs = [(args.variant, arm, CFG["arms"][arm], pid, txt, n) for arm in args.arms.split(",")
            for pid, txt in prompts.items() for n in range(1, CFG["samples_per_cell"] + 1)]
    print(f"{len(jobs)} cells, variant={args.variant}", flush=True)
    fails = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for res in ex.map(lambda j: one(*j), jobs):
            print(res, flush=True)
            fails += res.startswith("FAIL")
    print(f"DONE fails={fails}", flush=True)


if __name__ == "__main__":
    main()
