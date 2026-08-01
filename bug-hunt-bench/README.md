# bug-hunt-bench — 105 planted bugs, two real repos, nine coding models

**Question:** Hide bugs in a real codebase, keep the test suite green so nothing points at the
answers, then ask each frontier coding model — in its own native agentic CLI — to find and fix as
many as it can. Who actually fixes the most? And does a leaderboard built on one repo survive a
second, unrelated one?

Run twice, on two codebases that share nothing but a language.

| | Repo 1 | Repo 2 |
|---|---|---|
| What it is | A VS Code / Cursor sidebar extension (ACP client for a coding-agent CLI), ~28K lines TypeScript | A Vite/React/TypeScript LMS backed by Supabase Edge Functions and Clerk, ~60K lines |
| Bugs | **45** — 16 real shipped bugs reverted from the repo's own fix history, 29 authored in the same style | **60** — *every one* a real regression that shipped and was later fixed, each carrying its own fix-commit SHA |
| Green checks kept | 922 tests | 53 unit tests + typecheck + production build |
| Run | Jul 19–26 + Jul 31 – Aug 1, 2026 | Jul 26 + Jul 31 – Aug 1, 2026 |

Repo 2 is the stronger construction: no authored bugs at all. It was also built largely by AI,
and 59 of its 60 original fixes were written by an AI agent rather than a person.

**The task (identical for every model, both repos):** find and fix as many planted bugs as you can,
edit the source in place, keep the checks green (do not weaken tests), and write a `BUGS_FOUND.md`.
One round per model per repo, reasoning effort `high`, each in its native harness. Exact prompts:
[repo1-prompt.md](repo1-prompt.md) and [repo2-prompt.md](repo2-prompt.md).

**Grading:** each model's diff against the pristine repo is the ground truth — not its own report.
Scored against a withheld answer key by an independent blind judge per arm, submissions anonymized
and decoded only after every verdict is in. Buckets: `FIXED_MATCH` / `FIXED_PARTIAL` /
`CLAIMED_ONLY` / `MISSED`, plus extra fixes classified genuine or false-positive.

## Combined scoreboard

Strict fixes only — no partial credit. [combined-scoreboard.csv](combined-scoreboard.csv)

| Model | Harness | Fixed /105 | Repo 1 /45 | Repo 2 /60 | Genuine extras | Wall | Cost (list-equiv) |
|---|---|--:|--:|--:|--:|--:|--:|
| **GPT-5.6 Sol** | Codex CLI | **31** | 13 | 18 | 38 | 70.2 min | $29.16 |
| **Fable 5** | Claude Code | **24** | 9 | 15 | 3 | 31.4 min | $68.07 |
| **Opus 5** | Claude Code | **21** | 11 | 10 | 6 | 37.4 min | $38.77 |
| **Kimi K3** | Claude Code / OpenRouter | **21** | 4 | 17 | 6 | 107.8 min | $25.27 |
| **Grok 4.5** | Grok Build CLI (ACP) | **16** | 5 | 11 | 7 | 24.9 min | $8.40 floor |
| **Opus 4.8** | Claude Code | **9** | 2 | 7 | 1 | 34.8 min | $19.35 |
| **Sonnet 5** | Claude Code | **9** | 1 | 8 | 4 | 32.8 min | $15.12 |

**63 of the 105 bugs survived every model** in this seven-model wave (60 after the Jul 31 wave,
54 after the Aug 1 max wave below). Zero false-positive fixes from any arm on either repo: every
extra fix any model applied was a genuine unplanted defect.

Per-repo detail: [repo1-scoreboard.csv](repo1-scoreboard.csv) · [repo2-scoreboard.csv](repo2-scoreboard.csv).
Wall-clock, tokens and reconstructed cost: [repo1-metrics.csv](repo1-metrics.csv) ·
[repo2-metrics.csv](repo2-metrics.csv).

![combined](previous-editions/68-105-bugs-seven-models.png)

## Findings

- **One repo was not enough to rank the middle.** Opus 5 beat Fable 5 on repo 1 (11–9) and lost on
  repo 2 (10–15). Kimi K3 went from second-to-last on repo 1 to second on repo 2, finishing level
  with Opus 5 overall at a third less cost. Only first place was stable.
- **GPT-5.6 Sol leads both, and audits beyond the brief.** It fixed **38 genuine defects nobody
  planted** across the two repos — 29 of them on repo 2 alone, where every other model found 1 to 6.
  Cross-tenant quiz access, a `|| 75` coercion silently rewriting a 0% pass mark to 75%, timed quiz
  submissions with no time-limit enforcement.
- **Sonnet 5 on repo 1 is the sharpest single result.** It fixed 1 of 45: two files touched, a 2.9KB
  diff, one correct fix *with a regression test*, then a report claiming an exhaustive line-by-line
  review of the codebase and listing "Suspected but not fixed: None". 44 bugs were still there.
  Confident, thorough-sounding, and wrong.
- **Opus 4.8 → Opus 5 is a real generational jump**: 9 → 21 combined, same harness, same prompt,
  same bugs.
- **Cost is not recall.** Fable 5 cost the most ($68) and placed second. Grok 4.5 was the cheapest
  arm by a wide margin and placed fifth. Kimi K3 matched Opus 5 for a third less money and three
  times the wall clock.

## The Jul 31 wave — two new models, the effort dial, a Sol re-run

On Jul 30 OpenAI cut GPT-5.6 Luna's API price by 80% and shipped serving improvements; DeepSeek
released V4-Flash the next morning. Four new arms ran the identical two-repo battery on Jul 31,
same prompts, same blind-judging pipeline:

| Arm | Effort | Fixed /105 | Repo 1 /45 | Repo 2 /60 | Genuine extras | Wall | Cost (list-equiv) |
|---|---|--:|--:|--:|--:|--:|--:|
| **GPT-5.6 Sol (re-run)** | high | **34** | 13 | 21 | 28 | 66.7 min | $33.92 |
| **GPT-5.6 Luna** | **max** | **33** | 17 | 16 | 31 | 85.7 min | $1.80 |
| **GPT-5.6 Luna** | high | **13** | 5 | 8 | 22 | 64.1 min | $0.57 |
| **DeepSeek V4-Flash** | high | **8** | 4 | 4 | 4 | 24.9 min | $0.61 |

![jul 31 wave — full nine-model board](73-bug-hunt-bench-v5.png)

- **Luna at max effort beats Fable 5 on both axes** — 33 strict fixes vs 24, $1.80 vs $68.07 —
  and lands one fix behind the flagship Sol re-run at ~1/19th of its cost. Post-price-cut list
  rates ($0.20/M input, $1.20/M output). Exact, not a floor: re-derived per-request from the
  Codex CLI session rollouts - the CLI pins context at 258,400 tokens, below OpenAI's 272K
  long-context surcharge line, so no request in any run hit surcharge pricing.
- **The effort dial is worth 2.5x on Luna.** Same model, same prices: 13 strict fixes at `high`,
  33 at `max`. On repo 1, `max` was also 2.4x *faster* than `high` (21.5 vs 51.1 min).
- **The Sol re-run measures OpenAI's serving update.** Repo 2: 21 fixes vs 18 in the Jul 26 run,
  29.5 min vs 48.3, $14.36 vs $18.40 — better on all three axes. Repo 1: the same 13-fix count as
  Jul 26 but a partially different set of bugs, slower and pricier on that leg. List prices
  unchanged; the wall/cost gains are serving-side.
- **DeepSeek V4-Flash is last on coverage and untouchable on absolute price**: 8 of 105 for $0.61
  total (real OpenRouter bill cross-checked at $0.62). Ran through the same OpenRouter shim as
  Kimi K3, reasoning effort high, 1M context.
- **Survivors: 63 → 60.** Luna-high fixed one repo-1 bug that had survived all prior arms
  (including Luna-max — different effort levels catch different bugs), and the Sol re-run fixed
  two repo-2 survivors. Every other new-arm fix was already covered. 60 of 105 have now survived
  every arm ever run, across nine models and eleven scored runs.
- **Zero false-positive fixes again.** All extras across the four new arms were judged genuine;
  two arms each made one additional cosmetic, non-functional change (classified as neither fix
  nor defect).

New rows are appended to the same CSVs: [combined-scoreboard.csv](combined-scoreboard.csv),
[repo1-scoreboard.csv](repo1-scoreboard.csv), [repo2-scoreboard.csv](repo2-scoreboard.csv),
[repo1-metrics.csv](repo1-metrics.csv), [repo2-metrics.csv](repo2-metrics.csv) (voided
false-start rows kept, marked `VOID` in notes — the log wins).

Naming note: earlier commits used a `v2-` file prefix meaning "bench v2" (repo 2). That collided
with the card edition numbers (V3/V4/V5), so files are now named by repo.

Source post for this wave: [@PawelHuryn on X](https://x.com/PawelHuryn/status/2083279026299588816).

## The Aug 1 wave — the effort dial at max

Four models re-ran the identical two-repo battery at reasoning effort `max`, with their `high`
runs above as baselines. Same prompts, same blind-judging pipeline, same routing rule (no model
grades its own family: Sol graded by Grok 4.5, the other three by GPT-5.5).

| Arm | Effort | Fixed /105 | vs high | Repo 1 /45 | Repo 2 /60 | Genuine extras | Wall | Cost (list-equiv) |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| **GPT-5.6 Sol** | **max** | **42** | +8 | 19 | 23 | 40 | 163.8 min | $69.61 |
| **Fable 5** | **max** | **29** | +5 | 12 | 17 | 5 | 57.3 min | $104.49 |
| **Opus 5** | **max** | **27** | +6 | 13 | 14 | 2 | 60.0 min | $51.33 |
| **Grok 4.5** | **max** | **13** | **-3** | 5 | 8 | 5 | 25.4 min | $10.94 floor |

The full effort dial, strict fixes /105:

| Effort | GPT-5.6 Sol | GPT-5.6 Luna | Fable 5 | Opus 5 | Grok 4.5 |
|---|--:|--:|--:|--:|--:|
| high | 34 | 13 | 24 | 21 | 16 |
| max | 42 | 33 | 29 | 27 | 13 |

![the current board — 9 models, 14 runs](74-bug-hunt-bench-v6.png)

- **Sol at max is the all-time leader**: 42 of 105 strict, plus 40 genuine extras — for 2.7 hours
  of wall clock and $69.61, the longest and second-priciest run on the board.
- **The dial is not monotonic. Grok 4.5 got *worse* at max**: 13 strict fixes vs 16 at high, on a
  higher bill ($10.94 vs $8.40, both reconstructed floors).
- **Opus 5 at max starts claiming fixes it didn't make**: 5 claimed-only report entries (2 on
  repo 1, 3 on repo 2) vs zero in its high run. Fable 5 at max stayed clean — zero claimed-only
  on either repo.
- **Fable 5 at max is the priciest run on the board and added zero new coverage**: $104.49 for
  29 fixes, every one already fixed by some earlier run.
- **Survivors: 60 → 54.** Six bugs that had survived every earlier arm fell in this wave.
  **54 of 105 have survived everything** — nine models, fourteen scored runs.
- **Zero false-positive fixes, again**, now across all fourteen runs: every extra fix in this
  wave was judged genuine (three further changes classified cosmetic, not fixes).
- Sol-max's cost is exact, not a floor, for the same reason as Luna's: the Codex CLI's
  258,400-token context pin keeps every request below OpenAI's long-context surcharge line.

New rows are appended to the same CSVs as before; the two grok false-starts (a CLI auth clash,
see method notes) are kept and marked `VOID`.

## Method notes & caveats

- **n = 1 per cell.** One round per model per repo. Re-scoring repo 2 under the same judge moved one
  arm by a single fix, so treat `fixed` as ±1 and extras as ±2. Deltas are directional, not a
  ranking to the bug. The Kimi/Opus 5 tie at 21 is a tie.
- **Native harnesses, not one fixed harness.** GPT in Codex CLI, Grok in the grok CLI over ACP, the
  Claude-family arms in Claude Code, Kimi K3 in Claude Code through an OpenRouter shim (it ships no
  CLI of its own). By design: each model in the harness its own vendor ships.
- **Judging changed between the two runs, and was checked.** Repo 1's published numbers were graded
  by Opus 4.8. Everything is now graded by GPT-5.5 (Codex), except the GPT-5.6 arm, which Grok 4.5
  grades so no model scores its own submission. Re-judging repo 1 under the new routing reproduced
  **all six previously published arms exactly** — strict fixes and extras, zero delta. That is what
  makes the two halves of the /105 addable. Details and two further controls:
  [judge-calibration.md](judge-calibration.md). The Jul 31 wave keeps the same rule: the three
  GPT-5.6 arms were graded by Grok 4.5, DeepSeek V4-Flash by GPT-5.5. The Aug 1 max wave likewise:
  Sol-max by Grok 4.5, the Fable, Opus and Grok max arms by GPT-5.5. One GPT-5.5 packet came back
  schema-invalid, was recorded as `judge_failed`, and scored clean on retry.
- **Jul 31 wall-clock ran under concurrent load.** The four new arms ran two-at-a-time to four-at-
  a-time on one machine (the earlier waves were sequential), so their wall-clock is comparable
  within the wave but overstated against the sequential baselines. Fixes, tokens and cost are
  unaffected. The Aug 1 max wave ran under mixed concurrency with one hard exception: the grok CLI
  refreshes a shared credentials file on read, so two concurrent grok processes can race and wipe
  it — both initial grok-max starts died exactly that way (the `VOID` rows in the metrics CSVs),
  and every grok run and grok-judged verdict after that ran serialized.
- **"Planted" undersells the set.** All 60 repo-2 bugs are real shipped regressions. On repo 1, 16 of
  45 are (a documented floor — squashed release commits hide bugs fixed inside one cycle).
- **The benchmarks are withheld to keep them usable.** The **answer keys, the seeded sources, and the
  per-model diffs are not published** — publishing them would burn both benches. Scoreboards, metrics
  and the exact prompts are here; the prompts are self-contained specs.
- **Two cost figures are not bills.** Grok's CLI reports context *fill*, not cumulative *spend*, so
  its cost is a reconstructed **floor** (the token-accounting defect written up in
  [five-models-three-harnesses/](../five-models-three-harnesses/)). Kimi's is a local price-table
  estimate of an OpenRouter charge. Don't rank costs across differently-metered arms to the dollar.
- **De-identified.** Repo 1 is a real, public VS Code extension. Repo 2 is a private product and is
  described only by its stack. Private paths are scrubbed; numbers, timestamps and verdicts are as
  produced.

## Previous editions

Superseded cards (six- and seven-model boards, per-repo seven-model cards) live in
[previous-editions/](previous-editions/). The current board is the nine-model card above.

## Source posts

[@PawelHuryn on X](https://x.com/PawelHuryn/status/2078834615519731832) — the original single-repo
run. The two-repo result follows.

[@PawelHuryn on X](https://x.com/PawelHuryn/status/2081510124439417200) — the two-repo,
seven-model thread.

[@PawelHuryn on X](https://x.com/PawelHuryn/status/2083279026299588816) — the Jul 31 wave: Luna at
max effort, better and cheaper than Fable 5.

## License

MIT. Use anything; a link back is appreciated.
