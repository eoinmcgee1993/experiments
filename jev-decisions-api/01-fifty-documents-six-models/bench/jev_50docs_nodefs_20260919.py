# -*- coding: utf-8 -*-
"""The same 50 documents with the DEFINITIONS TAKEN AWAY. Bare class names only.

The 50-document run gives every model six written definitions plus an instruction saying the title
may lie. Jev scored 50/50 there. That is a real result, and it is also the easy condition: somebody
already did the hard part by writing the rules down.

The condition a team actually starts in is this one - six class names, no definitions, no warning
about misleading titles. This is where the earlier 4-case probe found Jev picking wrong at 0.97-0.99
confidence. Same 50 documents, same models, only the criteria text removed.

Reported per model: accuracy with definitions vs without, and - for Jev, which is the only one that
returns calibrated numbers - the confidence it attached to the answers it got WRONG.
"""
import concurrent.futures as cf
import importlib.util
import json
import pathlib
import sys
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent            # EDIT 1 of 2 (see README)


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, HERE / fname)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


r50 = _load("r50", "jev_50docs_20260919.py")
DOCS, JEV, post = r50.DOCS, r50.JEV, r50.post
DEC_URL, CHAT_URL = r50.DEC_URL, r50.CHAT_URL

# Bare labels. No definitions, no tie-breaks, no warning that the title may lie.
NEUTRAL = {k: k.replace("_", " ") for k in r50.DOC_CRIT}
NEUTRAL_TEXT = "\n".join("- %s: %s" % (k, v) for k, v in NEUTRAL.items())
BARE_INSTR = "Classify this document."

MODELS = [JEV, "openai/gpt-oss-20b", "mistralai/ministral-8b-2512", "anthropic/claude-haiku-4.5"]
OUT = HERE.parent / "results" / "jev-50docs-nodefs-20260919.json"
LOCK, DONE = threading.Lock(), [0]


def one(model, text, truth):
    if model == JEV:
        r = post(DEC_URL, {"model": JEV, "state": {"document_text": text},
                           "questions": {"doc_type": {"type": "choice", "criteria": NEUTRAL,
                                                      "instructions": BARE_INSTR}}})
        if not r["ok"]:
            return {"truth": truth, "error": r.get("error"), "cost": 0.0}
        u, a = (r["d"].get("usage") or {}), r["d"]["answers"]["doc_type"]
        return {"picked": a["choice"], "truth": truth, "hit": a["choice"] == truth,
                "conf": a.get("confidence"), "cost": u.get("cost") or 0.0}
    p = ("Classify the document below into one of these types:\n%s\n\n%s\n\nDocument:\n%s"
         '\n\nAnswer with JSON only: {"type":"<one of: %s>"}'
         % (NEUTRAL_TEXT, BARE_INSTR, text, ", ".join(NEUTRAL)))
    r = post(CHAT_URL, {"model": model, "max_tokens": 900, "temperature": 0,
                        "messages": [{"role": "system", "content": "Reply with ONLY minified JSON."},
                                     {"role": "user", "content": p}]})
    if not r["ok"]:
        return {"truth": truth, "error": r.get("error"), "cost": 0.0}
    d, u = r["d"], (r["d"].get("usage") or {})
    txt = (d["choices"][0]["message"].get("content") or "").strip()
    if txt.startswith("```"):
        txt = txt.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0]
    i, j = txt.find("{"), txt.rfind("}")
    try:
        pick = str(json.loads(txt[i:j + 1]).get("type", "")).strip()
    except Exception:                                                         # noqa: BLE001
        return {"truth": truth, "error": "unparsable", "cost": float(u.get("cost") or 0)}
    return {"picked": pick, "truth": truth, "hit": pick == truth, "cost": float(u.get("cost") or 0)}


def main():
    tasks = [(m, i, t, g) for m in MODELS for i, (t, g) in enumerate(DOCS)]
    print("Definitions REMOVED. %d documents x %d models = %d calls.\n"
          % (len(DOCS), len(MODELS), len(tasks)))
    res = {m: [None] * len(DOCS) for m in MODELS}
    t0 = time.time()

    def work(task):
        m, i, t, g = task
        out = one(m, t, g)
        with LOCK:
            DONE[0] += 1
            if DONE[0] % 50 == 0:
                print("  %d/%d (%.0fs)" % (DONE[0], len(tasks), time.time() - t0), flush=True)
        return m, i, out

    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        for m, i, out in ex.map(work, tasks):
            res[m][i] = out

    with_defs = json.loads((HERE.parent / "results" / "jev-50docs-20260919.json")
                           .read_text(encoding="utf-8"))
    print("\n%-30s %14s %14s %8s" % ("model", "WITH defs", "WITHOUT defs", "drop"))
    print("-" * 70)
    agg = {}
    for m in MODELS:
        ok = [r for r in res[m] if "picked" in r]
        hits = sum(r["hit"] for r in ok)
        was = with_defs[m]["hits"]
        agg[m] = {"hits_nodefs": hits, "n": len(ok), "hits_withdefs": was,
                  "cost": sum(r.get("cost", 0) for r in res[m]), "rows": res[m]}
        print("%-30s %10d/%-3d %10d/%-3d %8d" % (m, was, with_defs[m]["n"], hits, len(ok),
                                                 hits - was))

    jev = [r for r in res[JEV] if "picked" in r]
    wrong = [r for r in jev if not r["hit"]]
    right = [r for r in jev if r["hit"]]
    print("\nJev without definitions - %d wrong out of %d." % (len(wrong), len(jev)))
    if wrong:
        cw = [r["conf"] for r in wrong if r["conf"] is not None]
        cr = [r["conf"] for r in right if r["conf"] is not None]
        print("  mean confidence when WRONG:   %.3f  (max %.3f)" % (sum(cw) / len(cw), max(cw)))
        print("  mean confidence when RIGHT:   %.3f" % (sum(cr) / len(cr)))
        print("  How many of its wrong answers it was >0.90 sure of: %d of %d"
              % (sum(c > 0.90 for c in cw), len(cw)))
        print("\n  Every wrong answer, with the confidence it reported:")
        for i, r in enumerate(res[JEV]):
            if "picked" in r and not r["hit"]:
                print("   conf %.2f  want %-14s got %-14s | %s"
                      % (r["conf"] or 0, r["truth"], r["picked"],
                         DOCS[i][0][:64].replace("\n", " ")))

    OUT.write_text(json.dumps(agg, indent=1, default=str), encoding="utf-8")
    print("\n  written: %s" % OUT)


if __name__ == "__main__":
    main()
