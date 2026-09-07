"""Blind pairwise judging with a published rubric, by models that are not arms and share no vendor with one.

Three kinds of pair, every one shown to every judge TWICE, in both orders. A pair counts only if the judge
names the same text in both orders; a flip is recorded as position-dependent.
  within   every pair of arms, same prompt, same sample index, same variant     key  [<variant>-]<pid>-<n>-<a>-vs-<b>-{AB,BA}
Recusal: a judge never scores a pair that contains a text from its own vendor (bench/config.json judge_recusal).
  calib    each human control text vs a model text of the LinkedIn prompt        key  calib-[<variant>-]<human>-vs-<arm>-<n>-{HM,MH}
  cross    each model's bare text vs its own steered text, same prompt/sample    key  cross-<pid>-<n>-<arm>-{BS,SB}
Bare keys carry no variant prefix (they predate variants). A judge that cannot tell the pre-ChatGPT human posts
from the model posts is not trusted with the leaderboard.

Receipts: receipts/judge/<judge>/<key>.json (full request body, full raw response, parsed verdict). Idempotent.
Usage: python bench/judge.py [--judges gemini,muse] [--variant bare|steered] [--cross] [--no-within] [--workers 8]
"""
import argparse, itertools, json, pathlib, re, sys, time, concurrent.futures as cf
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from transports import TRANSPORTS, usage_summary  # noqa: E402
from calib import pairings  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "bench/config.json").read_text(encoding="utf-8"))
RUBRIC = (ROOT / "bench/rubric.md").read_text(encoding="utf-8")

PROMPT = """You are comparing two texts written in response to the same task. Decide which one reads MORE like unedited, default output from an AI language model.

Judge ONLY the presence of the tells listed below. Do not judge argument quality, factual accuracy, length, formatting preference, or whether you agree with the content. A longer, better-argued or more polished text is not more human. Pick the text with MORE tells.

{rubric}

TASK GIVEN TO BOTH WRITERS:
{task}

=== TEXT A ===
{a}
=== END OF TEXT A ===

=== TEXT B ===
{b}
=== END OF TEXT B ===

Answer with a single JSON object and nothing else:
{{"more_ai": "A" or "B", "confidence": 1-5, "tells_A": ["short tell", ...], "tells_B": ["short tell", ...]}}
"""


def parse(text):
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j < 0:
        raise ValueError("no json object")
    d = json.loads(t[i:j + 1])
    if d.get("more_ai") not in ("A", "B"):
        raise ValueError("more_ai missing")
    return d


def call(judge, j, key, task, text_a, text_b):
    out = ROOT / "receipts/judge" / judge / f"{key}.json"
    if out.exists():
        return f"skip {judge}/{key}"
    out.parent.mkdir(parents=True, exist_ok=True)
    prompt = PROMPT.format(rubric=RUBRIC, task=task, a=text_a, b=text_b)
    last = None
    for attempt in range(2):
        t0 = time.time()
        try:
            # 16K: Gemini's thinking (3K+ tokens at high) counts against the cap; 6K produced empty answers
            text, raw, body = TRANSPORTS[j["transport"]](j["model"], prompt, max_tokens=16000, **j.get("params", {}),
                                                          json_mode=(j["transport"] == "google"))
            verdict = parse(text)
        except Exception as e:  # noqa: BLE001
            last = repr(e)[:200]; continue
        rc = {"judge": judge, "model": j["model"], "key": key, "wall_s": round(time.time() - t0, 1),
              "run_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "request_body": body,
              "usage": usage_summary(j["transport"], raw), "verdict": verdict, "response_raw": raw}
        out.write_text(json.dumps(rc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
        return f"ok   {judge}/{key} -> {verdict['more_ai']} ({verdict.get('confidence')})"
    return f"FAIL {judge}/{key}: {last}"


def load_essays(variant):
    d = CFG["variants"][variant]["essays_dir"]
    out = {}
    for arm in CFG["arms"]:
        for f in (ROOT / d / arm).glob("*.md"):
            out[(arm, f.stem)] = f.read_text(encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judges", default=",".join(CFG["judges"]))
    ap.add_argument("--variant", default="bare", choices=list(CFG["variants"]))
    ap.add_argument("--cross", action="store_true", help="also judge each model's bare text vs its steered text")
    ap.add_argument("--no-within", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--first", default="", help="comma-separated arms whose pairs are judged first (e.g. the arms only one judge can score)")
    args = ap.parse_args()
    base = {p.stem: p.read_text(encoding="utf-8").strip() for p in sorted((ROOT / "prompts").glob("*.txt"))}
    suffix = CFG["variants"][args.variant]["suffix"]
    arms = list(CFG["arms"])
    human = sorted((ROOT / "control/human").glob("*.md"))
    vp = "" if args.variant == "bare" else f"{args.variant}-"
    lp = "p3-linkedin"

    jobs = []  # (key, task, text_a, text_b, arms_in_pair)
    vendor = {a: CFG["arms"][a]["vendor"] for a in arms}
    if not args.no_within:
        essay = load_essays(args.variant)
        for pid, task0 in base.items():
            task = task0 + suffix
            for n in range(1, CFG["samples_per_cell"] + 1):
                for a, b in itertools.combinations(arms, 2):
                    ta, tb = essay.get((a, f"{pid}-{n}")), essay.get((b, f"{pid}-{n}"))
                    if ta is None or tb is None:
                        continue
                    jobs.append((f"{vp}{pid}-{n}-{a}-vs-{b}-AB", task, ta, tb, (a, b)))
                    jobs.append((f"{vp}{pid}-{n}-{a}-vs-{b}-BA", task, tb, ta, (a, b)))
        hfile = {hf.stem: hf for hf in human}
        for stem, arm, n in pairings(arms, sorted(hfile), CFG["samples_per_cell"]):
            hf = hfile[stem]
            tm = essay.get((arm, f"{lp}-{n}"))
            if tm is None:
                continue
            th = hf.read_text(encoding="utf-8")
            task = (base[lp] + suffix + "\n(One of the texts is a real LinkedIn post by a person, written on its "
                    "own topic; judge tells, not topic.)")
            jobs.append((f"calib-{vp}{hf.stem}-vs-{arm}-{n}-HM", task, th, tm, (arm,)))
            jobs.append((f"calib-{vp}{hf.stem}-vs-{arm}-{n}-MH", task, tm, th, (arm,)))
    if args.cross:
        bare, steered = load_essays("bare"), load_essays("steered")
        for pid, task in base.items():
            for n in range(1, CFG["samples_per_cell"] + 1):
                for arm in arms:
                    tb, ts = bare.get((arm, f"{pid}-{n}")), steered.get((arm, f"{pid}-{n}"))
                    if tb is None or ts is None:
                        continue
                    jobs.append((f"cross-{pid}-{n}-{arm}-BS", task, tb, ts, (arm,)))
                    jobs.append((f"cross-{pid}-{n}-{arm}-SB", task, ts, tb, (arm,)))

    # recusal: a judge never scores a pair that contains a text from its own vendor
    work = [(judge, CFG["judges"][judge], *jb[:4]) for judge in args.judges.split(",") for jb in jobs
            if CFG["judges"][judge]["vendor"] not in {vendor[a] for a in jb[4]}]
    if args.first:
        first = set(args.first.split(","))
        jobs.sort(key=lambda jb: 0 if first & set(jb[4]) else 1)
        work = [(judge, CFG["judges"][judge], *jb[:4]) for judge in args.judges.split(",") for jb in jobs
                if CFG["judges"][judge]["vendor"] not in {vendor[a] for a in jb[4]}]
    print(f"{len(work)} judge calls after recusal ({len(jobs)} jobs per judge before it)", flush=True)
    fails = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for res in ex.map(lambda w: call(*w), work):
            if not res.startswith("skip"):
                print(res, flush=True)
            fails += res.startswith("FAIL")
    print(f"DONE fails={fails}", flush=True)


if __name__ == "__main__":
    main()
