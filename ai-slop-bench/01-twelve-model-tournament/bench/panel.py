"""Panel reliability, from the judge receipts: per-judge flip rate, per-judge calibration (human vs model), and
agreement between judges on the matchups they both scored. Writes results/panel.md.

A matchup is one (prompt, sample, a, b). A judge's verdict on it is a (name) if AB and BA agree, else "flip".
Agreement counts matchups where two judges both resolved and named the same text. Usage: python bench/panel.py
"""
import itertools, json, pathlib

from calib import pairings

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "bench/config.json").read_text(encoding="utf-8"))
ARMS = list(CFG["arms"])
JUDGES = list(CFG["judges"])
PROMPTS = sorted(p.stem for p in (ROOT / "prompts").glob("*.txt"))
N = CFG["samples_per_cell"]
HUMAN = sorted(p.stem for p in (ROOT / "control/human").glob("*.md"))


def load(judge):
    out = {}
    d = ROOT / "receipts/judge" / judge
    if d.exists():
        for f in d.glob("*.json"):
            rc = json.loads(f.read_text(encoding="utf-8"))
            out[rc["key"]] = rc["verdict"]["more_ai"]
    return out


def verdict(v, base, first, second, s1="-AB", s2="-BA"):
    r1, r2 = v.get(base + s1), v.get(base + s2)
    if r1 is None or r2 is None:
        return None
    n1 = first if r1 == "A" else second
    n2 = second if r2 == "A" else first
    return n1 if n1 == n2 else "flip"


def main():
    V = {j: load(j) for j in JUDGES}
    vendor = {a: CFG["arms"][a]["vendor"] for a in ARMS}
    L = ["# Panel reliability, bare variant\n"]

    # per judge: matchups resolved / flipped, and calibration
    L += ["## Per judge\n",
          "| Judge | matchups scored | resolved | flips | flip rate | calibration: named model / named human / flip |",
          "|---|--:|--:|--:|--:|---|"]
    per = {}
    for j in JUDGES:
        res = fl = 0
        for pid in PROMPTS:
            for n in range(1, N + 1):
                for a, b in itertools.combinations(ARMS, 2):
                    if CFG["judges"][j]["vendor"] in (vendor[a], vendor[b]):
                        continue
                    r = verdict(V[j], f"{pid}-{n}-{a}-vs-{b}", a, b)
                    if r is None:
                        continue
                    if r == "flip":
                        fl += 1
                    else:
                        res += 1
        cm = ch = cf = 0
        for h, arm, n in pairings(ARMS, HUMAN, N):
            if CFG["judges"][j]["vendor"] == vendor[arm]:
                continue
            r = verdict(V[j], f"calib-{h}-vs-{arm}-{n}", "human", "model", "-HM", "-MH")
            if r == "model":
                cm += 1
            elif r == "human":
                ch += 1
            elif r == "flip":
                cf += 1
        per[j] = (res, fl)
        tot = res + fl
        L.append(f"| {CFG['judges'][j]['label']} | {tot} | {res} | {fl} | {fl / tot:.0%} | {cm} / {ch} / {cf} |" if tot
                 else f"| {CFG['judges'][j]['label']} | 0 | 0 | 0 | - | {cm} / {ch} / {cf} |")

    # pairwise agreement between judges on shared matchups
    L += ["\n## Agreement between judges\n",
          "Matchups both judges resolved (no flip on either side), and how often they named the same text.\n",
          "| Judges | both resolved | agree | agreement |", "|---|--:|--:|--:|"]
    for j1, j2 in itertools.combinations(JUDGES, 2):
        both = agree = 0
        for pid in PROMPTS:
            for n in range(1, N + 1):
                for a, b in itertools.combinations(ARMS, 2):
                    if {CFG["judges"][j1]["vendor"], CFG["judges"][j2]["vendor"]} & {vendor[a], vendor[b]}:
                        continue
                    r1 = verdict(V[j1], f"{pid}-{n}-{a}-vs-{b}", a, b)
                    r2 = verdict(V[j2], f"{pid}-{n}-{a}-vs-{b}", a, b)
                    if r1 in (None, "flip") or r2 in (None, "flip"):
                        continue
                    both += 1
                    agree += r1 == r2
        L.append(f"| {CFG['judges'][j1]['label']} vs {CFG['judges'][j2]['label']} | {both} | {agree} | "
                 + (f"{agree / both:.0%} |" if both else "- |"))

    # coverage: how many judges scored each pair of arms
    L += ["\n## Judges per pair\n", "| Pair | eligible judges |", "|---|---|"]
    for a, b in itertools.combinations(ARMS, 2):
        el = [CFG["judges"][j]["label"] for j in JUDGES if CFG["judges"][j]["vendor"] not in (vendor[a], vendor[b])]
        if len(el) < len(JUDGES):
            L.append(f"| {CFG['arms'][a]['label']} vs {CFG['arms'][b]['label']} | {', '.join(el)} |")
    L.append(f"\nEvery pair not listed is scored by all {len(JUDGES)} judges.\n")
    md = "\n".join(L)
    (ROOT / "results/panel.md").write_text(md, encoding="utf-8", newline="\n")
    print(md)


if __name__ == "__main__":
    main()
