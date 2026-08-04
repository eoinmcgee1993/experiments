# 01 — Two-repo bug hunt: 19/105, blind-judged

## Question

Alibaba announced Qwen3.8-Max (2.4T parameters) on Aug 3, 2026 as "a new bar for coding." Same day, on a rig where five Western frontier models already have scores: is it?

## Method

- **Two seeded repos, 105 planted bugs total.** Repo A (`gbvb`): the Grok Build VS Code extension — TypeScript, extension host + webview + ACP client — with **45 planted bugs**. Repo B (`abhb`): Accredia, a production Vite/React/TypeScript app on Supabase Edge Functions — with **60 planted bugs**. Plants are runtime logic defects; the suite stays green (some tests were neutralized when bugs were planted). Full task prompts, verbatim: [prompt-gbvb.md](prompt-gbvb.md), [prompt-abhb.md](prompt-abhb.md).
- **Harness:** Qwen3.8-Max has no agentic CLI, so it borrowed Claude Code's through an Anthropic-API proxy shim ([../02-five-attempts-to-run/harness/kimi_proxy2.py](../02-five-attempts-to-run/harness/kimi_proxy2.py)) — the same pattern the Kimi K3 set used. Model string `claude-opus-5[1m]` sets only the CLI's 1M-context assumption; the proxy rewrites every upstream call to Qwen3.8-Max. Served by Alibaba's own endpoints (OpenRouter never listed the model during the run — see [02](../02-five-attempts-to-run/)).
- **Effort: `high`** — the runner passes `--effort high` to the CLI. Not max. (The "max" in the arm slug `qwen38max` is the model's name, Qwen3.8-**Max** — unlike `fable5max`/`opus5max`/`gpt56solmax`, where the suffix means effort max.) Subagents and web tools disabled, 4h timeout per leg, one leg per repo (n=1 per repo).
- **Blind judging:** the run's report + full diff are packaged into an anonymized packet (model-identifying terms redacted — see `redact_terms` in [score-config-gbvb.json](score-config-gbvb.json) / [score-config-abhb.json](score-config-abhb.json)) and judged by Codex (GPT-5.5, effort high, read-only sandbox) against the answer key. **Diff is ground truth**; the report is intent evidence only. `claimed_only` = claimed in the report, not actually fixed in the diff. Extras (non-planted fixes) are verified genuine separately.

## Results

| Repo | Plants | Strict fixed | Partial | Claimed only | Genuine extras | Cosmetic/false | Wall | Est. cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A — Grok Build extension (gbvb) | 45 | **5** (11.1%) | 0 | 0 | 3 | 0 | 66.5 min | $16.64 |
| B — Accredia (abhb) | 60 | **14** (23.3%) | 0 | 1 | 3 | 0 | 81.7 min | $14.46 |
| **Combined** | **105** | **19** (18.1%) | 0 | 1 | 6 | 0 | 148.1 min summed | **$31.10** |

Raw judge verdicts with per-plant IDs: [verdicts-gbvb.md](verdicts-gbvb.md) · [verdicts-abhb.md](verdicts-abhb.md). Scoring summaries: [summary-gbvb.json](summary-gbvb.json) · [summary-abhb.json](summary-abhb.json). Run metrics incl. the three voided attempts: [metrics_qwen.csv](metrics_qwen.csv).

Token profile (clean legs, from metrics): 64.16M total tokens — 8.28M input, 0.88M cache write, **54.86M cache read (85.5%)**, 136.4K output.

Field comparison, same rig (numbers from [../../bug-hunt-bench/](../../bug-hunt-bench/), where the per-arm receipts live):

| Model | Combined /105 | Effort | Note |
|---|---:|---|---|
| GPT-5.6 Sol | 42 | max | field leader |
| GPT-5.6 Luna | 33 | max | ~$1.80 total |
| Kimi K3 | 21 | high | |
| Opus 5 | 21 | high | |
| **Qwen3.8-Max** | **19** | **high** | ~$31, 148 min |
| Grok 4.5 | 16 | high | ~25 min total |

## Findings

1. **19/105 is mid-field, not "a new bar."** At its own effort tier it lands just under Kimi K3 and Opus 5 (21 each); GPT-5.6 Luna fixed 33 for ~$1.80 against Qwen's 19 for ~$31.
2. **It fixed one bug no other model has.** Plant P022 on Repo B — a two-file API-contract plant (fields dropped from a response shape *and* the client's type/projection; fixing it requires connecting both sides). Across all 18 blind-judged runs in that bench's scoring archive (11 models, effort variants included), Qwen3.8-Max is the only arm to fix it.
3. **The report is honest: 25 of 26 claimed fixes verified real.** 19 plant fixes confirmed by diff, 6 extras all verified genuine, 0 cosmetic, and a single claimed-but-not-fixed entry (P079). Several heavier arms in this field post claimed-only counts of 2–3.
4. **The profile is a slow, cache-heavy grinder.** 85.5% of its 64M tokens were cache reads and it wrote only 136K output tokens across 148 summed minutes — long context reuse, comparatively little writing, at 2.4T parameters.

## Caveats

- **n=1 per repo.** Directional, not a ranking. Recall on this rig is unstable run to run (see the n=10 variance evidence in [frontier-vs-open-audit/](../../frontier-vs-open-audit/)).
- **Day-one serving.** Both clean legs ran on Alibaba's pay-as-you-go endpoint hours after launch, concurrently on one account — walls may carry mutual contention. "148 minutes" is the sum of the two legs; the actual span was ~85 min.
- **Cost is a token-estimate at Qwen Cloud list rates** ($2.00/M in, $0.25/M implicit-cache read, $6.00/M out), not a metered bill — DashScope offers no OpenRouter-style credits-delta cross-check, and the July DeepSeek V4-Pro lesson (listed cache discounts not always honored) cuts both ways.
- **Effort passthrough is one-sided evidence.** The CLI sent its native high-effort thinking parameter through the shim verbatim; whether Alibaba's Anthropic-compatible gateway honors it exactly as Anthropic does is upstream behavior we cannot verify.
- **Comparison numbers are [../../bug-hunt-bench/](../../bug-hunt-bench/)'s published numbers** from the same rig and judge setup, not re-runs; GPT-5.6 Sol's 42 and Luna's 33 are max-effort numbers, labeled as such.
- **Withheld:** answer keys, seeded sources, agent transcripts and diffs, judge packets (they quote the repos). The three Repo B extras descriptions are redacted in [verdicts-abhb.md](verdicts-abhb.md) — they describe real, non-planted defects in Accredia's code, and we don't publish the app's code or bugs. The gbvb verdicts header reads "Accredia Bug Hunt Bench" — a shared scorer-template title, kept as produced.
