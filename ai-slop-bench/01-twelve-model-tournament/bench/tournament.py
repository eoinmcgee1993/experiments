"""Head-to-head matrix from the judge receipts, one variant, panel pooled with recusal.

For every unordered pair of arms and every eligible judge (a judge never scores its own vendor's texts), a
pair of receipts (AB, BA) resolves to the arm named MORE AI in both orders, or to a flip. The matrix cell
(a, b) is the share of resolved verdicts naming a. Overall(a) is the mean of a's cells across all opponents
(each opponent weighs the same, whatever the number of resolved verdicts against it).

Writes results/tournament.json and results/tournament.md. Usage: python bench/tournament.py [--variant bare]
"""
import argparse, itertools, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "bench/config.json").read_text(encoding="utf-8"))
ARMS = list(CFG["arms"])
JUDGES = list(CFG["judges"])
PROMPTS = sorted(p.stem for p in (ROOT / "prompts").glob("*.txt"))
N = CFG["samples_per_cell"]


def load(judge):
    out = {}
    d = ROOT / "receipts/judge" / judge
    if d.exists():
        for f in d.glob("*.json"):
            rc = json.loads(f.read_text(encoding="utf-8"))
            out[rc["key"]] = rc["verdict"]["more_ai"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="bare", choices=list(CFG["variants"]))
    args = ap.parse_args()
    vp = "" if args.variant == "bare" else f"{args.variant}-"
    V = {j: load(j) for j in JUDGES}
    vendor = {a: CFG["arms"][a]["vendor"] for a in ARMS}

    named = {}; resolved = {}; flips = {}; per_judge = {}
    for a, b in itertools.combinations(ARMS, 2):
        key = (a, b)
        named[key] = {a: 0, b: 0}; resolved[key] = 0; flips[key] = 0; per_judge[key] = {}
        for j in JUDGES:
            if CFG["judges"][j]["vendor"] in (vendor[a], vendor[b]):
                continue
            per_judge[key][j] = {a: 0, b: 0, "flip": 0}
            for pid in PROMPTS:
                for n in range(1, N + 1):
                    base = f"{vp}{pid}-{n}-{a}-vs-{b}"
                    r1, r2 = V[j].get(base + "-AB"), V[j].get(base + "-BA")
                    if r1 is None or r2 is None:
                        continue
                    n1 = a if r1 == "A" else b
                    n2 = b if r2 == "A" else a
                    if n1 != n2:
                        flips[key] += 1; per_judge[key][j]["flip"] += 1; continue
                    resolved[key] += 1; named[key][n1] += 1; per_judge[key][j][n1] += 1

    share = {}  # share[(a,b)] = share of resolved verdicts naming a
    for (a, b), cnt in named.items():
        tot = resolved[(a, b)]
        if tot:
            share[(a, b)] = cnt[a] / tot
            share[(b, a)] = cnt[b] / tot
    overall = {}
    for a in ARMS:
        xs = [share[(a, b)] for b in ARMS if b != a and (a, b) in share]
        overall[a] = sum(xs) / len(xs) if xs else None
    order = sorted(ARMS, key=lambda a: (overall[a] is None, overall[a] if overall[a] is not None else 0))

    out = {
        "variant": args.variant,
        "panel": {j: CFG["judges"][j]["label"] for j in JUDGES},
        "recusal": CFG.get("judge_recusal", ""),
        "arms": {a: {"label": CFG["arms"][a]["label"], "vendor": vendor[a]} for a in ARMS},
        "order": order,
        "overall": overall,
        "pairs": [{"a": a, "b": b, "share_a_named": share.get((a, b)), "resolved": resolved[(a, b)],
                   "flips": flips[(a, b)], "judges": per_judge[(a, b)]} for a, b in itertools.combinations(ARMS, 2)],
    }
    (ROOT / "results/tournament.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")

    L = [f"# Head to head, {args.variant} variant\n",
         "Cell: share of resolved blind verdicts naming the ROW model as the text with more AI tells, against the column model. "
         "Panel: " + ", ".join(CFG["judges"][j]["label"] for j in JUDGES) + ". " + CFG.get("judge_recusal", "") + "\n",
         "| | " + " | ".join(CFG["arms"][b]["label"] for b in order) + " | overall | resolved | flips |",
         "|---|" + "--:|" * (len(order) + 3)]
    for a in order:
        cells = []
        for b in order:
            if a == b:
                cells.append("")
            else:
                s = share.get((a, b))
                cells.append(f"{s:.0%}" if s is not None else "-")
        res = sum(resolved[k] for k in resolved if a in k)
        fl = sum(flips[k] for k in flips if a in k)
        ov = f"**{overall[a]:.0%}**" if overall[a] is not None else "-"
        L.append(f"| {CFG['arms'][a]['label']} | " + " | ".join(cells) + f" | {ov} | {res} | {fl} |")
    md = "\n".join(L) + "\n"
    (ROOT / "results/tournament.md").write_text(md, encoding="utf-8", newline="\n")
    print(md)


if __name__ == "__main__":
    main()
