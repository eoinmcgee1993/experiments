"""Build results/summary.md from the scorer output and the judge receipts. Prints it too."""
import csv, itertools, json, pathlib, statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "bench/config.json").read_text(encoding="utf-8"))
ARMS = list(CFG["arms"])
VARIANTS = list(CFG["variants"])
JUDGES = list(CFG["judges"])
from calib import pairings  # noqa: E402
LABEL = {a: v["label"] for a, v in CFG["arms"].items()}
LABEL["human"] = "Human control (pre-ChatGPT posts)"
PROMPTS = sorted(p.stem for p in (ROOT / "prompts").glob("*.txt"))
N = CFG["samples_per_cell"]


def load_verdicts(judge):
    out = {}
    for f in (ROOT / "receipts/judge" / judge).glob("*.json"):
        rc = json.loads(f.read_text(encoding="utf-8"))
        out[rc["key"]] = rc
    return out


def resolve(v, base, sfx1, sfx2, first, second):
    """Which side was named 'more AI' in both orders? Returns first/second, 'flip', or None if incomplete.
    In the <sfx1> receipt `first` is TEXT A; in the <sfx2> receipt `first` is TEXT B."""
    r1, r2 = v.get(base + sfx1), v.get(base + sfx2)
    if not r1 or not r2:
        return None
    n1 = first if r1["verdict"]["more_ai"] == "A" else second
    n2 = second if r2["verdict"]["more_ai"] == "A" else first
    return n1 if n1 == n2 else "flip"


def within(v, variant):
    vp = "" if variant == "bare" else f"{variant}-"
    named = {a: 0 for a in ARMS}; played = {a: 0 for a in ARMS}
    flips = total = 0; pairs = {}
    for pid in PROMPTS:
        for n in range(1, N + 1):
            for a, b in itertools.combinations(ARMS, 2):
                r = resolve(v, f"{vp}{pid}-{n}-{a}-vs-{b}", "-AB", "-BA", a, b)
                if r is None:
                    continue
                total += 1
                if r == "flip":
                    flips += 1; continue
                pairs[(pid, n, a, b)] = r
                played[a] += 1; played[b] += 1; named[r] += 1
    hits = misses = cflips = 0
    human = sorted(p.stem for p in (ROOT / "control/human").glob("*.md"))
    for stem, arm, n in pairings(list(CFG["arms"]), human, CFG["samples_per_cell"]):
        base = f"calib-{vp}{stem}-vs-{arm}-{n}"
        r = resolve(v, base, "-HM", "-MH", "human", arm)
        if r is None:
            continue
        if r == "flip":
            cflips += 1
        elif r == arm:
            hits += 1
        else:
            misses += 1
    return dict(named=named, played=played, flips=flips, total=total, pairs=pairs, calib=(hits, misses, cflips))


def cross(v):
    out = {a: {"steered_less": 0, "bare_less": 0, "flip": 0} for a in ARMS}
    for pid in PROMPTS:
        for n in range(1, N + 1):
            for arm in ARMS:
                r = resolve(v, f"cross-{pid}-{n}-{arm}", "-BS", "-SB", "bare", "steered")
                if r is None:
                    continue
                out[arm]["flip" if r == "flip" else ("steered_less" if r == "bare" else "bare_less")] += 1
    return out


def main():
    L = []
    P = L.append
    agg = {(a["group"], a["variant"]): a for a in csv.DictReader(open(ROOT / "results/scores_by_group.csv", encoding="utf-8"))}
    rows = list(csv.DictReader(open(ROOT / "results/scores.csv", encoding="utf-8")))
    cats = [k[:-7] for k in next(iter(agg.values())) if k.endswith("_per_1k") and k != "tells_per_1k"]
    have = [vn for vn in VARIANTS if any(g[1] == vn for g in agg)]

    P("# AI slop bench V1: tell counts, calibration, the steered pilot\n")
    P("The head-to-head matrix (the headline) is in results/tournament.md; judge reliability in results/panel.md.\n")
    P(f"Arms: {', '.join(LABEL[a] for a in ARMS)}. Prompts: {len(PROMPTS)}. Samples per cell: {N}. "
      f"Default sampling and default reasoning effort everywhere. No system prompt. Variants:\n")
    for vn in have:
        P(f"- **{vn}**: {CFG['variants'][vn]['note']}" + (f" (`{CFG['variants'][vn]['suffix'].strip()}`)" if CFG['variants'][vn]['suffix'] else "") + ".")
    P("\nThe request bodies in the receipts are the models' entire context.\n")

    # ---------------- scorer
    P("## 1. Deterministic tells (no model in the loop)\n")
    P("Counts per 1,000 words, `bench/score.py`, same code for every text. Lower is fewer tells. Markdown structure "
      "(headers, bullets) is reported but outside the composite. The human row is the author's own LinkedIn posts "
      "from 2021-2022, before ChatGPT.\n")
    for vn in have:
        P(f"### {vn}\n")
        P("| Text source | n | words | tells /1k | " + " | ".join(cats) + " |")
        P("|---|--:|--:|--:|" + "--:|" * len(cats))
        rs = [agg[("human", "control")]] + [agg[(a, vn)] for a in ARMS if (a, vn) in agg]
        for a in sorted(rs, key=lambda x: float(x["tells_per_1k"])):
            P(f"| {LABEL.get(a['group'], a['group'])} | {a['n']} | {a['words_mean']} | **{a['tells_per_1k']}** | "
              + " | ".join(a[c + "_per_1k"] for c in cats) + " |")
        P("")
    if "steered" in have:
        P("### Steerability, deterministic\n")
        P("Same model, same prompt, plus the one steering line. Change is steered minus bare, per 1,000 words.\n")
        P("| Model | bare | steered | change | em dashes bare -> steered | bold labels bare -> steered | md structure bare -> steered | words bare -> steered |")
        P("|---|--:|--:|--:|--:|--:|--:|--:|")
        for a in ARMS:
            b, s = agg.get((a, "bare")), agg.get((a, "steered"))
            if not b or not s:
                continue
            d = float(s["tells_per_1k"]) - float(b["tells_per_1k"])
            P(f"| {LABEL[a]} | {b['tells_per_1k']} | {s['tells_per_1k']} | **{d:+.1f}** | "
              f"{b['em_dash_per_1k']} -> {s['em_dash_per_1k']} | {b['bold_label_per_1k']} -> {s['bold_label_per_1k']} | "
              f"{b['md_structure_per_1k']} -> {s['md_structure_per_1k']} | {b['words_mean']} -> {s['words_mean']} |")
        P("")
    P("Per prompt, tells per 1,000 words (mean of samples):\n")
    P("| Model | " + " | ".join(f"{vn} {p}" for vn in have for p in PROMPTS) + " |")
    P("|---|" + "--:|" * (len(have) * len(PROMPTS)))
    for arm in ARMS:
        cells = []
        for vn in have:
            for pid in PROMPTS:
                xs = [float(r["tells_per_1k"]) for r in rows if r["group"] == arm and r["variant"] == vn and r["prompt"] == pid]
                cells.append(f"{statistics.mean(xs):.1f}" if xs else "-")
        P(f"| {LABEL[arm]} | " + " | ".join(cells) + " |")
    P("")
    P("Rhythm, bare variant (mean sentence length in words, share of sentences in the most common 10-word band, share of sentences of 3 words or fewer):\n")
    P("| Text source | sent. mean | 10w band | staccato |")
    P("|---|--:|--:|--:|")
    for a in [agg[("human", "control")]] + [agg[(x, "bare")] for x in ARMS if (x, "bare") in agg]:
        P(f"| {LABEL.get(a['group'], a['group'])} | {a['sent_mean']} | {a['pct_10w_band']} | {a['staccato_share']} |")
    P("")

    # ---------------- judges
    P("## 2. Blind pairwise judges (rubric in `bench/rubric.md`)\n")
    P("Each pair shown in both orders; a verdict counts only if the judge named the same text both times. "
      "'Named more AI' is the share of resolved pairs in which the judge pointed at this model. Lower is better. "
      "Calibration pairs a human post with a model post; a judge must name the model.\n")
    V = {j: load_verdicts(j) for j in JUDGES}
    for vn in have:
        P(f"### {vn}\n")
        W = {j: within(V[j], vn) for j in JUDGES}
        if not any(W[j]["total"] for j in JUDGES):
            P("(no verdicts yet)\n"); continue
        for j in JUDGES:
            w = W[j]; jj = CFG["judges"][j]; h, m, cf_ = w["calib"]
            P(f"**{jj['label']}** ({jj['vendor']}): resolved {w['total'] - w['flips']} of {w['total']} pairs, "
              f"{w['flips']} flipped with order. Calibration: named the model {h}, the human {m}, flipped {cf_}.\n")
        P("| Model | " + " | ".join(CFG["judges"][j]["label"].split(" (")[0] for j in JUDGES) + " | combined | pairs |")
        P("|---|" + "--:|" * (len(JUDGES) + 2))
        comb = {a: (sum(W[j]["named"][a] for j in JUDGES), sum(W[j]["played"][a] for j in JUDGES)) for a in ARMS}
        for a in sorted(ARMS, key=lambda x: comb[x][0] / max(1, comb[x][1])):
            cells = [f"{W[j]['named'][a] / max(1, W[j]['played'][a]):.0%}" for j in JUDGES]
            P(f"| {LABEL[a]} | " + " | ".join(cells) + f" | **{comb[a][0] / max(1, comb[a][1]):.0%}** | {comb[a][1]} |")
        if len(JUDGES) == 2:
            a_, b_ = JUDGES
            common = set(W[a_]["pairs"]) & set(W[b_]["pairs"])
            agree = sum(W[a_]["pairs"][k] == W[b_]["pairs"][k] for k in common)
            P(f"\nJudge agreement: {agree} of {len(common)} pairs both resolved ({agree / max(1, len(common)):.0%}). Chance is 50%.\n")
        else:
            P("")
    if "steered" in have:
        C = {j: cross(V[j]) for j in JUDGES}
        if any(sum(C[j][a].values()) for j in JUDGES for a in ARMS):
            P("### Steerability, judged: each model's bare text vs its own steered text\n")
            P("Same prompt, same sample index. 'Steered less AI' counts pairs where the judge named the bare text "
              "as the one with more tells in both orders.\n")
            P("| Model | " + " | ".join(f"{CFG['judges'][j]['label'].split(' (')[0]}: steered less / bare less / flip" for j in JUDGES) + " | combined steered less |")
            P("|---|" + "---|" * len(JUDGES) + "--:|")
            for a in ARMS:
                cells = [f"{C[j][a]['steered_less']} / {C[j][a]['bare_less']} / {C[j][a]['flip']}" for j in JUDGES]
                sl = sum(C[j][a]["steered_less"] for j in JUDGES); tot = sum(C[j][a]["steered_less"] + C[j][a]["bare_less"] for j in JUDGES)
                P(f"| {LABEL[a]} | " + " | ".join(cells) + f" | **{sl}/{tot}** |")
            P("")

    # ---------------- run facts
    P("## 3. Run facts\n")
    P("| Model | variant | serving path | effort | reasoning tok (mean) | wall s (mean) | input tok seen by model |")
    P("|---|---|---|---|--:|--:|--:|")
    for vn in have:
        for arm in ARMS:
            d = ROOT / CFG["variants"][vn]["receipts_dir"] / arm
            rcs = [json.loads(f.read_text(encoding="utf-8")) for f in d.glob("*.json")] if d.exists() else []
            if not rcs:
                continue
            rt = [r["usage"].get("reasoning_tokens") or 0 for r in rcs]
            it = [r["usage"].get("input_tokens") or 0 for r in rcs]
            eff = {r["usage"].get("effort_echoed") for r in rcs} - {None}
            P(f"| {LABEL[arm]} | {vn} | {rcs[0]['serving_path']} | {', '.join(eff) if eff else 'default (not set)'} | "
              f"{statistics.mean(rt):.0f} | {statistics.mean(r['wall_s'] for r in rcs):.0f} | {statistics.mean(it):.0f} |")
    P("")
    out = "\n".join(L)
    (ROOT / "results/summary.md").write_text(out, encoding="utf-8", newline="\n")
    print(out)


if __name__ == "__main__":
    main()
