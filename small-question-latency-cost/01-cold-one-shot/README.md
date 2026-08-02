# 01 — Cold one-shot calls: time and cost per small question

## Question

On a small, tool-free question, how do Opus 5 and GPT-5.6 Luna compare on wall-clock time and cost when every call is a **fresh CLI invocation**? This is the shape most people picture when they compare "speed" between two coding agents, and it is the shape that flatters neither model honestly, because a cold call pays setup costs a real session pays once.

## Method

Six configurations, five questions each, run **sequentially, never concurrently**, with the config order rotated every round so no two consecutive calls share a configuration. Rotation matters: OpenAI serving latency drifted up to 4x within single sessions during this work, and a blocked design would have charged that drift to whichever arm held the slow window.

| | |
|---|---|
| Opus 5 | `claude -p <q> --model claude-opus-5 --effort {high,max} --output-format stream-json --include-partial-messages --verbose` |
| GPT-5.6 Luna | `codex exec --json --skip-git-repo-check -s read-only -m gpt-5.6-luna -c model_reasoning_effort={high,max} <q>` |
| Fast mode variants | as above plus `--enable fast_mode` (these two arms are in the raw log and CSV; they are excluded from the published card, see Findings 4) |

Working directory was a **real repository containing an `AGENTS.md` that points at a `CLAUDE.md`**, not an empty folder. An earlier version of this experiment ran in an empty directory and had to be thrown away: with no instructions to find, Codex shelled out to PowerShell repeatedly hunting for context (76,431 input tokens on a probe, against 13,506 when it answers cleanly), which inflated its times against a Claude run that did no such thing. In a real repo both harnesses load a comparable payload and neither ran a single shell command.

Every prompt was prefixed verbatim with:

```
Answer directly from your own knowledge in 2-3 sentences. Do not run any commands, do not read any files, do not use any tools.
```

The five questions are in `final_bench.py`.

**Timing** is Python `time.monotonic()` around the subprocess: stamped before spawn, stamped on process exit. It therefore **includes CLI startup and harness overhead**, which is what a user actually waits for. It is not an API-level latency measurement.

**Cost** is computed from the token counts each CLI reports, at published list rates. Rates were verified by recomputing three rows of an unrelated benchmark from their raw token counts and matching the recorded totals to the cent:

| Model | Rates used | Verification |
|---|---|---|
| GPT-5.6 Luna | $0.20/M in · $0.02/M cached in · $1.20/M out | recomputed a prior run to $1.3988 vs $1.3988 recorded |
| Opus 5 | $5.00/M in · $6.25/M cache write · $0.50/M cache read · $25.00/M out | recomputed two prior runs to $22.8775 and $26.5549, both exact |

These are **API-equivalent** figures. Both models actually ran on subscriptions, where marginal dollar cost is zero.

## Results

Medians, n=5 per configuration. Full per-call rows in `results.csv`, raw output in `run.log`.

| Configuration | Median time | Median cost | Median output tokens |
|---|---|---|---|
| Opus 5 · high | 8.1s | 10.097¢ | 195 |
| Opus 5 · max | 8.6s | 10.147¢ | 211 |
| GPT-5.6 Luna · high | 16.0s | 0.112¢ | 61 |
| GPT-5.6 Luna · max | 22.6s | 0.111¢ | 103 |
| GPT-5.6 Luna · high · fast | 16.8s | 0.112¢ (bills 2x) | 65 |
| GPT-5.6 Luna · max · fast | 15.7s | 0.119¢ (bills 2x) | 127 |

## Findings

1. **Opus 5 answers a small question in about half the time and roughly 90x the cost.** 8.1s / 10.10¢ against Luna's 16.0s / 0.11¢.

2. **Most of Opus's cold cost is a cache write, not the answer.** $0.087 of its $0.101 per call is the prompt-cache write of the repository instructions. A cold CLI invocation pays that every single time; a live session pays it once (see experiment 02).

3. **Opus's effort dial is nearly free on easy questions.** high → max moves time 8.1s → 8.6s and cost 10.097¢ → 10.147¢. Luna's dial costs more time (16.0s → 22.6s) at flat cost.

4. **Fast mode did not make Luna faster.** 16.8s vs 16.0s at high, 15.7s vs 22.6s at max — one direction each, on n=5, inside a variance band where a single session drifted 4x. OpenAI documents fast mode as 1.5x faster at 2.5x ChatGPT credits (2x on API Priority). We could not reproduce the speedup; the billing multiplier is real. Excluded from the published card for that reason, retained here.

## Caveats

- **n=5 per cell.** The Opus-vs-Luna separation is larger than the observed spread and survives; the orderings *within* the Luna arms do not. Do not read Luna high vs Luna max vs fast mode as ranked.
- **Small, tool-free questions only.** At high effort Opus 5 barely reasons on these (a probe showed 0 thinking tokens at `high`, 500 at `max`). On hard work Opus can think far longer before its first token, and this experiment says nothing about that regime.
- **Timing includes CLI startup**, so absolute seconds are not portable to API or IDE use. Ratios are the durable part.
- **Serving drift is large.** Pooled blocks of 10 calls in a related run averaged 42s, 40s, 18s and 74s within one 30-minute window. Cross-session comparisons of absolute times are not meaningful; everything compared here was measured in one interleaved window.
- **Cost is API-equivalent, not spend.** Both arms ran on subscriptions.
- Anthropic and OpenAI serve independently, so drift on one side does not imply drift on the other.
