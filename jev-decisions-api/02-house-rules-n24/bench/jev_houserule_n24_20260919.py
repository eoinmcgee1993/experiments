# -*- coding: utf-8 -*-
"""Does your domain reach it, and what happens when you don't write it down? N=24, not N=4.

Why this rerun exists. The original probe had FOUR items and reported "2/4 wrong at 0.97-0.99
confidence", which the draft then used as evidence that Jev is confidently miscalibrated. That
reading was wrong and the number was doing unfair work. The "ground truth" in that test was an
arbitrary HOUSE rule (duplicate charges go to support, not billing) that was deliberately NOT
supplied in the neutral condition. Scoring the industry-standard answer as an error, and then
calling the high confidence attached to it "overconfidence", measures nothing about calibration -
any model and any human routes a duplicate charge to billing. It measures that an unstated rule
is unreachable, which is a different and much more useful claim.

So this tests the useful claim properly. Six house policies, each a deliberate inversion of the
natural reading, four messages each = 24 items. Three conditions:

  neutral      bare team names, house rule NOT supplied  -> can the prior be overridden by luck?
  house rule   the policy written into criteria          -> does written domain actually land?
  examples     bare names + 8 labelled examples in state -> is there a second channel?

Confidence is recorded in every condition. The honest question is not "is it wrong" - in the
neutral condition it SHOULD be wrong, the rule is unknowable - but how sure it sounds while it is.
"""
import concurrent.futures as cf
import importlib.util
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent            # EDIT 1 of 2 (see README)
spec = importlib.util.spec_from_file_location(
    "r50", HERE / "jev_50docs_20260919.py")
r50 = importlib.util.module_from_spec(spec)
sys.modules["r50"] = r50
spec.loader.exec_module(r50)
JEV, post, DEC_URL, CHAT_URL = r50.JEV, r50.post, r50.DEC_URL, r50.CHAT_URL
OUT = HERE.parent / "results" / "jev-houserule-n24-20260919.json"

# Each house rule INVERTS the natural reading, so the neutral condition cannot get it by default.
ITEMS = [
    # 1. charge errors -> support (natural: billing)
    ("I was charged twice for the same order.", "support"),
    ("There is a duplicate charge on my card.", "support"),
    ("You took 49 EUR instead of 29 EUR this month.", "support"),
    ("My card was billed after I already paid by transfer.", "support"),
    # 2. cancellations -> billing (natural: support / retention)
    ("Please cancel my subscription, I don't need it anymore.", "billing"),
    ("I want to cancel and stop being charged.", "billing"),
    ("How do I close my account for good?", "billing"),
    ("Cancel the renewal before it goes through next week.", "billing"),
    # 3. refunds past 30 days -> sales (natural: billing)
    ("I'd like a refund for a charge from three months ago.", "sales"),
    ("Can I get my money back? I bought this in June.", "sales"),
    ("Requesting a refund outside the 30 day window.", "sales"),
    ("It's been 90 days and I want that payment returned.", "sales"),
    # 4. login and password -> trust_safety (natural: support)
    ("I can't log in, the password reset email never arrives.", "trust_safety"),
    ("Locked out of my account after too many attempts.", "trust_safety"),
    ("Need to reset my password, the link expired.", "trust_safety"),
    ("Two factor codes aren't working for me.", "trust_safety"),
    # 5. invoice copies and tax details -> support (natural: billing)
    ("Can you send me a copy of last month's invoice?", "support"),
    ("I need our VAT number corrected on the invoice.", "support"),
    ("Please reissue invoice 4410 with our new address.", "support"),
    ("Where do I download my past invoices?", "support"),
    # 6. plan changes -> billing (natural: sales)
    ("I want to upgrade to the team plan.", "billing"),
    ("Please downgrade us to the starter tier.", "billing"),
    ("We'd like to add 10 more seats.", "billing"),
    ("Switch us from monthly to annual, please.", "billing"),
]
TEAMS = ["billing", "support", "sales", "trust_safety"]
NEUTRAL = {t: t.replace("_", " ") + " team" for t in TEAMS}
HOUSE = {
    "billing": "HOUSE RULE: billing owns subscription CANCELLATIONS, account closure, and all PLAN "
               "CHANGES (upgrades, downgrades, seat counts, billing period switches). It does NOT "
               "handle charge errors or refunds.",
    "support": "HOUSE RULE: support owns all payment ERRORS (duplicate, wrong or unexpected "
               "charges) and all INVOICE DOCUMENT requests (copies, reissues, tax detail "
               "corrections). It does NOT handle logins or cancellations.",
    "sales": "HOUSE RULE: sales owns REFUND requests made outside the 30 day window. It does not "
             "handle plan changes.",
    "trust_safety": "HOUSE RULE: trust & safety owns ALL account access problems - logins, password "
                    "resets, lockouts and two factor codes.",
}
EXAMPLES = [{"message": "You billed me twice in March", "team": "support"},
            {"message": "Wrong amount taken from my card", "team": "support"},
            {"message": "Cancel my plan please", "team": "billing"},
            {"message": "Stop my subscription", "team": "billing"},
            {"message": "Refund my purchase from April", "team": "sales"},
            {"message": "Money back on an old order", "team": "sales"},
            {"message": "Can't sign in, reset link dead", "team": "trust_safety"},
            {"message": "Account locked out", "team": "trust_safety"}]

CONDITIONS = [("neutral (rule NOT supplied)", NEUTRAL, False),
              ("house rule written into criteria", HOUSE, False),
              ("neutral + 8 labelled examples in state", NEUTRAL, True)]
CHAT_MODEL = "mistralai/ministral-8b-2512"


def jev_one(crit, examples, text):
    state = {"message": text}
    if examples:
        state["past_routing_decisions"] = EXAMPLES
    r = post(DEC_URL, {"model": JEV, "state": state,
                       "questions": {"team": {"type": "choice", "criteria": crit,
                                              "instructions": "Route this message to a team."}}})
    if not r["ok"]:
        return {"error": r.get("error")}
    a = r["d"]["answers"]["team"]
    return {"picked": a["choice"], "conf": a.get("confidence"),
            "cost": (r["d"].get("usage") or {}).get("cost") or 0.0}


def chat_one(crit, examples, text):
    ex = ("\nPast routing decisions:\n" + "\n".join("  %s -> %s" % (e["message"], e["team"])
                                                    for e in EXAMPLES)) if examples else ""
    p = ("Route the message to one team.\n%s%s\n\nMessage: %s\n\n"
         'Answer with JSON only: {"team":"<one of: %s>"}'
         % ("\n".join("- %s: %s" % (k, v) for k, v in crit.items()), ex, text, ", ".join(TEAMS)))
    r = post(CHAT_URL, {"model": CHAT_MODEL, "max_tokens": 700, "temperature": 0,
                        "messages": [{"role": "system", "content": "Reply with ONLY minified JSON."},
                                     {"role": "user", "content": p}]})
    if not r["ok"]:
        return {"error": r.get("error")}
    txt = (r["d"]["choices"][0]["message"].get("content") or "").strip()
    if txt.startswith("```"):
        txt = txt.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0]
    i, j = txt.find("{"), txt.rfind("}")
    try:
        return {"picked": str(json.loads(txt[i:j + 1]).get("team", "")).strip(),
                "cost": float((r["d"].get("usage") or {}).get("cost") or 0)}
    except Exception:                                                         # noqa: BLE001
        return {"error": "unparsable"}


def main():
    print("%d messages, 3 conditions, house rules INVERT the natural reading.\n" % len(ITEMS))
    tasks = []
    for ci, (label, crit, ex) in enumerate(CONDITIONS):
        for ii, (text, truth) in enumerate(ITEMS):
            tasks.append(("jev", ci, ii, crit, ex, text, truth))
            tasks.append(("chat", ci, ii, crit, ex, text, truth))
    t0 = time.time()

    def work(t):
        kind, ci, ii, crit, ex, text, truth = t
        out = (jev_one if kind == "jev" else chat_one)(crit, ex, text)
        out["truth"] = truth
        if "picked" in out:
            out["hit"] = out["picked"] == truth
        return kind, ci, ii, out

    res = {"jev": [[None] * len(ITEMS) for _ in CONDITIONS],
           "chat": [[None] * len(ITEMS) for _ in CONDITIONS]}
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        for kind, ci, ii, out in pool.map(work, tasks):
            res[kind][ci][ii] = out
    print("  %d calls, %.0fs\n" % (len(tasks), time.time() - t0))

    print("%-42s %-18s %-18s" % ("condition", "jev-1.13", "ministral-8b"))
    print("-" * 80)
    for ci, (label, _, _) in enumerate(CONDITIONS):
        cells = []
        for kind in ("jev", "chat"):
            ok = [r for r in res[kind][ci] if "picked" in r]
            cells.append("%d/%d" % (sum(r["hit"] for r in ok), len(ok)))
        print("%-42s %-18s %-18s" % (label, cells[0], cells[1]))

    print("\nJev's confidence, by condition:")
    for ci, (label, _, _) in enumerate(CONDITIONS):
        ok = [r for r in res["jev"][ci] if "picked" in r and r.get("conf") is not None]
        hit = [r["conf"] for r in ok if r["hit"]]
        mis = [r["conf"] for r in ok if not r["hit"]]
        print("  %-42s follows rule %.3f (n=%d) | breaks rule %.3f (n=%d)"
              % (label, sum(hit) / len(hit) if hit else float("nan"), len(hit),
                 sum(mis) / len(mis) if mis else float("nan"), len(mis)))
        if mis:
            print("       of the %d it got wrong, %d were above 0.90 confident"
                  % (len(mis), sum(c > 0.90 for c in mis)))

    OUT.write_text(json.dumps({"items": ITEMS, "res": res}, indent=1, default=str),
                   encoding="utf-8")
    print("\n  written: %s" % OUT)


if __name__ == "__main__":
    main()
