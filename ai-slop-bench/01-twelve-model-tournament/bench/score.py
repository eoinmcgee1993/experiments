"""Deterministic tell counter. No model in the loop; anyone can re-run it and get the same numbers.

Counts, per text, the patterns that readers have learned to associate with unedited LLM prose. The list is
opinionated and public (this file IS the rubric); the human control set in control/human/ gives the baseline
that makes the counts meaningful. Everything is normalised per 1,000 words.

Usage: python bench/score.py            -> results/scores.csv, results/scores_by_group.csv, prints the table
"""
import csv, json, pathlib, re, statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- lexical tells (word-boundary, case-insensitive)
SLOP_WORDS = [
    r"delv(?:e|es|ed|ing)", r"tapestry", r"myriad", r"underscor(?:e|es|ed|ing)", r"seamless(?:ly)?",
    r"robust(?:ly|ness)?", r"foster(?:s|ed|ing)?", r"elevat(?:e|es|ed|ing)", r"unlock(?:s|ed|ing)?",
    r"testament", r"landscape", r"navigat(?:e|es|ed|ing)", r"crucial(?:ly)?", r"pivotal",
    r"leverag(?:e|es|ed|ing)", r"harness(?:es|ed|ing)?", r"realm", r"embark(?:s|ed|ing)?", r"journey",
    r"transformative", r"paradigm", r"ever-evolving", r"multifaceted", r"holistic(?:ally)?",
    r"resonat(?:e|es|ed|ing)", r"empower(?:s|ed|ing|ment)?", r"unleash(?:es|ed|ing)?", r"beacon",
    r"intricate", r"nuanced", r"vibrant", r"meticulous(?:ly)?", r"streamlin(?:e|es|ed|ing)",
    r"revolutioniz(?:e|es|ed|ing)", r"cutting-edge", r"groundbreaking", r"actionable", r"synerg(?:y|ies)",
    r"supercharg(?:e|es|ed|ing)", r"north star", r"move the needle", r"double down", r"deep dive",
    r"dive deep", r"unpack(?:s|ed|ing)?", r"game-?chang(?:er|ers|ing)", r"fast-paced", r"digital age",
    r"plays a (?:crucial|vital|key|pivotal) role", r"a wide range of", r"in the world of", r"when it comes to",
    r"at its core", r"the beauty of", r"thrilled to", r"excited to (?:announce|share|introduce)",
    r"say goodbye to", r"say hello to", r"we'?ve got you covered", r"look no further", r"without further ado",
    r"buckle up", r"stay tuned", r"the best part\?", r"invaluable", r"impactful", r"a testament to",
    r"it'?s (?:important|worth) (?:to note|noting)", r"in today'?s", r"in an era",
]
# sentence-initial only
FILLER_TRANSITIONS = [
    "however", "additionally", "furthermore", "moreover", "that said", "ultimately", "importantly",
    "crucially", "notably", "indeed", "in fact", "of course", "interestingly", "essentially", "fundamentally",
    "first and foremost", "needless to say", "in other words", "at the end of the day", "in conclusion",
    "to sum up", "in summary", "to summarize", "in short", "put simply", "simply put",
]
# announcements of what the text is about to do, and closers that recap
SIGNPOSTS = [
    "let's dive in", "let's dive", "let's break it down", "let's break this down", "let's explore",
    "let's unpack", "let's be honest", "let's face it", "here's the thing", "here's why", "here's how",
    "here's what", "here's the deal", "here's the truth", "here's the reality", "the bottom line",
    "bottom line:", "the truth is", "the reality is", "the key takeaway", "key takeaway", "the takeaway",
    "the lesson:", "the lesson?", "the result?", "the answer?", "the catch?", "the problem?", "the fix?",
    "the kicker", "so what?", "why does this matter", "why this matters", "what this means", "the point is",
    "the good news", "the bad news", "the hard part", "the hard truth", "the uncomfortable truth", "spoiler:",
    "spoiler alert", "plot twist", "fast forward", "fast-forward", "tl;dr", "tldr", "final thought",
    "one more thing", "that's the post", "to be clear", "let me be clear",
]
# the text applauding itself
SELF_CLAP = [
    "let that sink in", "this changes everything", "make no mistake", "read that again", "think about that",
    "sit with that", "this is huge", "this is big", "mind-blowing", "i'll say it again", "say it louder",
    "full stop.", "that's not a typo", "you read that right", "wait for it", "it's that simple",
    "it really is that simple", "and that's okay", "and that's fine", "and that's the point",
]

NOT_BUT = re.compile(r"\b(?:not|n't|isn't|aren't|wasn't|weren't|doesn't|don't|didn't|never|no longer)\b"
                     r"(?:(?![.!?;]).){1,90}?\b(?:but|rather|instead)\b", re.I)
# "It wasn't a prioritization problem. It was a listening problem." (any tense, any pronoun)
IT_IS_NOT = re.compile(r"\b(?:it|this|that|they|we|you|i)\s*(?:'s|'re|'m|is|are|was|were)\s*(?:not|n't)\b[^.!?]*[.!?]"
                       r"['\")]?\s+(?:it|this|that|they|we|you|i)\s*(?:'s|'re|'m|is|are|was|were)\b(?!\s*(?:not|n't))", re.I)
NOT_JUST = re.compile(r"\b(?:isn'?t|is not|aren'?t|are not|wasn'?t|was not|not|never)\s+(?:just|merely|only|simply|about)\b", re.I)
TRIAD = re.compile(r"(?:[\w'’-]+(?: [\w'’-]+){0,2}, ){1,}[\w'’-]+(?: [\w'’-]+){0,2},? (?:and|or) [\w'’-]+(?: [\w'’-]+){0,2}")
PARTICIPIAL_TAIL = re.compile(r",\s+(?!including|according|during|something|nothing|everything|anything|morning|evening)"
                              r"(?:[a-z]+ing)\b[^,;]{3,140}[.!?]$", re.I)
# "**The problem.** prose..." and "**The problem:** prose..." and "**The problem** - prose..."; the label's
# punctuation may sit inside or outside the asterisks, and prose must follow on the same line
BOLD_LABEL = re.compile(r"^\s*(?:[-*•]\s+|\d+[.)]\s+)?\*\*[^*\n]{1,80}?(?:[:.!?]\*\*|\*\*\s*[:.—–-])\s*\S", re.M)
MD_STRUCTURE = re.compile(r"^\s*(?:#{1,6}\s|[-*•→✅✔➡]\s*\S|\d+[.)]\s|(?:---|\*\*\*|___)\s*$|\*\*[^*\n]+\*\*\s*$)", re.M)
EM_DASH = re.compile(r"—|–| -- ")
WORD = re.compile(r"[A-Za-z0-9'’-]+")


def _phrase_count(text, phrases):
    t = text.lower().replace("’", "'")
    return sum(len(re.findall(r"(?<![\w-])" + re.escape(p) + r"(?![\w-])", t)) for p in phrases)


def _is_triad(m):
    """'A, B, and C' always counts. 'A, B and C' counts only when the three items are parallel (same word
    count), which drops 'Therefore, mastering Agile and Scrum ...' (an introductory clause, not a list)."""
    items = re.split(r",? (?:and|or) |, ", m)
    if len(items) != 3:
        return False
    if m.count(",") == 2:
        return True
    return len(items[0].split()) == len(items[1].split()) == len(items[2].split())


def _merged_span_count(text, patterns):
    spans = sorted(m.span() for p in patterns for m in p.finditer(text))
    n, end = 0, -1
    for s, e in spans:
        if s >= end:
            n += 1; end = e
    return n


def prose(text):
    """Drop structural lines (headers, bullets, rules) and markdown emphasis; keep the running prose."""
    keep = []
    for line in text.splitlines():
        if MD_STRUCTURE.match(line):
            # keep bullet TEXT for lexical counts but not for sentence rhythm
            continue
        keep.append(line)
    t = "\n".join(keep)
    t = re.sub(r"\*\*|__|`", "", t)
    t = re.sub(r"(?<!\w)[*_](?=\w)|(?<=\w)[*_](?!\w)", "", t)
    return t


def sentences(prose_text):
    flat = re.sub(r"\s*\n+\s*", " ", prose_text.strip())
    parts = re.split(r"(?<=[.!?])[\"'”’)]?\s+(?=[\"'“(A-Z0-9])", flat)
    return [s.strip() for s in parts if len(WORD.findall(s)) >= 1]


def score_text(text):
    words = WORD.findall(re.sub(r"\*\*|__|`|#", "", text))
    n_words = max(1, len(words))
    p = prose(text)
    sents = sentences(p)
    lens = [len(WORD.findall(s)) for s in sents] or [0]
    n_s = len(sents)
    flat = re.sub(r"\s*\n+\s*", " ", p)

    c = {
        "em_dash": len(EM_DASH.findall(text)),
        "neg_parallel": _merged_span_count(flat, [NOT_BUT, IT_IS_NOT, NOT_JUST]),
        "triad": sum(1 for m in TRIAD.finditer(flat) if _is_triad(m.group(0))),
        "signpost": _phrase_count(text, SIGNPOSTS),
        "self_clap": _phrase_count(text, SELF_CLAP),
        "filler_transition": sum(1 for s in sents if any(
            re.match(r"^[\"'“(]?" + re.escape(f) + r"\b", s.lower().replace("’", "'")) for f in FILLER_TRANSITIONS)),
        "slop_words": sum(len(re.findall(r"(?<![\w-])(?:" + w + r")(?![\w-])", text, re.I)) for w in SLOP_WORDS),
        "bold_label": len(BOLD_LABEL.findall(text)),
        "md_structure": len(MD_STRUCTURE.findall(text)),
        # the comma must sit after a real main clause (5+ words), else "Therefore, mastering X is ..." matches
        "participial_tail": sum(1 for s in sents if (m := PARTICIPIAL_TAIL.search(s))
                                and len(WORD.findall(s[:m.start()])) >= 5),
    }
    last_para = [x for x in text.strip().split("\n\n") if x.strip()][-1].strip().lower() if text.strip() else ""
    c["closing_recap"] = int(any(last_para.startswith(x) for x in
                                 ("in conclusion", "ultimately", "in the end", "so,", "so ", "the bottom line",
                                  "at the end of the day", "in short", "to sum up", "in summary", "bottom line",
                                  "the lesson", "the takeaway", "final thought")))
    # md_structure is reported but kept OUT of the composite: lists are genre-normal in a LinkedIn post and the
    # human control is LinkedIn posts. The per-prompt table shows where models format prose that was asked for.
    tells = sum(v for k, v in c.items() if k != "md_structure")
    band = 0.0
    if n_s:
        bins = {}
        for L in lens:
            bins[L // 10] = bins.get(L // 10, 0) + 1
        band = max(bins.values()) / n_s
    return {
        "words": len(words), "sentences": n_s, **c,
        "tells": tells, "tells_per_1k": round(tells / n_words * 1000, 1),
        "questions": sum(1 for s in sents if s.endswith("?")),
        "staccato_share": round(sum(1 for L in lens if L <= 3) / max(1, n_s), 2),
        "sent_mean": round(statistics.mean(lens), 1),
        "sent_stdev": round(statistics.pstdev(lens), 1) if n_s > 1 else 0.0,
        "pct_10w_band": round(band, 2),
    }


CATS = ["em_dash", "neg_parallel", "triad", "signpost", "self_clap", "filler_transition", "slop_words",
        "bold_label", "participial_tail", "closing_recap", "md_structure"]  # last one is outside the composite


def main():
    cfg = json.loads((ROOT / "bench/config.json").read_text(encoding="utf-8"))
    rows = []
    for vname, v in cfg["variants"].items():
        for arm in cfg["arms"]:
            for f in sorted((ROOT / v["essays_dir"] / arm).glob("*.md")):
                pid, n = f.stem.rsplit("-", 1)
                rows.append({"group": arm, "variant": vname, "file": f"{v['essays_dir']}/{arm}/{f.name}",
                             "prompt": pid, "sample": int(n), **score_text(f.read_text(encoding="utf-8"))})
    for f in sorted((ROOT / "control/human").glob("*.md")):
        rows.append({"group": "human", "variant": "control", "file": f"control/human/{f.name}",
                     "prompt": "control", "sample": 0, **score_text(f.read_text(encoding="utf-8"))})
    (ROOT / "results").mkdir(exist_ok=True)
    with open(ROOT / "results/scores.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    groups = {}
    for r in rows:
        groups.setdefault((r["group"], r["variant"]), []).append(r)
    agg = []
    for (g, vn), rs in groups.items():
        tw = sum(r["words"] for r in rs)
        a = {"group": g, "variant": vn, "n": len(rs), "words_mean": round(tw / len(rs)),
             "tells_per_1k": round(sum(r["tells"] for r in rs) / tw * 1000, 1),
             "tells_per_1k_median": round(statistics.median(r["tells_per_1k"] for r in rs), 1)}
        for c in CATS:
            a[c + "_per_1k"] = round(sum(r[c] for r in rs) / tw * 1000, 2)
        a["sent_mean"] = round(statistics.mean(r["sent_mean"] for r in rs), 1)
        a["pct_10w_band"] = round(statistics.mean(r["pct_10w_band"] for r in rs), 2)
        a["staccato_share"] = round(statistics.mean(r["staccato_share"] for r in rs), 2)
        agg.append(a)
    with open(ROOT / "results/scores_by_group.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(agg[0].keys())); w.writeheader(); w.writerows(agg)
    print(f"{'group':8} {'variant':8} {'n':>3} {'words':>6} {'tells/1k':>9}  " + " ".join(f"{c[:9]:>9}" for c in CATS))
    for a in sorted(agg, key=lambda x: (x["variant"], x["tells_per_1k"])):
        print(f"{a['group']:8} {a['variant']:8} {a['n']:>3} {a['words_mean']:>6} {a['tells_per_1k']:>9}  "
              + " ".join(f"{a[c + '_per_1k']:>9}" for c in CATS))


if __name__ == "__main__":
    main()
