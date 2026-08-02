# 02 — In-session turns: what a warm conversation changes

## Question

Cold one-shot calls make every request pay setup costs. In real use you ask a follow-up. Does keeping one session alive make later turns **faster**, and what happens to cost?

The hypothesis under test was that a warm prompt cache would speed up later turns. It does not. The interesting result is elsewhere.

## Method

Four configurations — Opus 5 at high and max, GPT-5.6 Luna at high and max — **three replicate sessions each**, six turns per session. 72 calls, zero failures.

Replicates, not longer sessions, are the point. An earlier single-session run put Luna-high's cost *above* Luna-max's, which is mechanically backwards. The cause was cache-hit rate differing between two lone sessions (35-75% against 70-90%). Hit rate is a property of when a session starts relative to cache state, so more turns cannot average it out and more sessions can.

All 12 sessions are advanced **one turn per round with the order rotated**, so no two consecutive calls share a configuration, every session meets the same question at the same turn depth, and serving drift spreads evenly across arms.

Turn 1 opens the session; turns 2-6 resume it:

```
codex exec --json --skip-git-repo-check -s read-only -m gpt-5.6-luna -c model_reasoning_effort=<e> <q>
codex exec resume <thread_id> --json --skip-git-repo-check -m gpt-5.6-luna -c model_reasoning_effort=<e> <q>

claude -p <q> --model claude-opus-5 --effort <e> --output-format stream-json --include-partial-messages --verbose
claude -p <q> --model claude-opus-5 --effort <e> ... --resume <session_id>
```

Note `codex exec resume` rejects `-s`; the sandbox is inherited from the opening call. Passing it kills every resumed turn instantly.

Same repo, same prompt prefix, same rate verification as experiment 01. Reported medians use **turns 2-6 only** — turn 1 is a cold call and belongs to experiment 01.

### The token-accounting trap (read this before reusing the CSV)

**The two CLIs do not mean the same thing by `input_tokens`.**

- **Codex `turn.completed.usage` is CUMULATIVE per thread.** Luna's reported output tokens climb 114 → 230 → 375 → 490 → 598 → 702 across six turns while each answer is ~110 tokens.
- **Claude `result.usage` is PER-REQUEST.** Opus's oscillate 212 / 185 / 145 / 204 / 209 / 182.

Computing per-turn cost from Codex's counters directly charges every later turn for all the turns before it. Our first pass did exactly that and reported warm Luna at 0.30¢/turn with a cost that "climbs across the session". Both were artifacts. `results.csv` carries the **raw reported** values, a `usage_semantics` column, and the **derived per-turn** values side by side so anyone can check the arithmetic.

## Results

Medians over turns 2-6, n=15 per configuration. Full rows in `results.csv`, raw output in `run.log`.

| Configuration | Median time | Median cost/turn | Median cache hit |
|---|---|---|---|
| Opus 5 · max | 9.8s | 2.788¢ | 100% |
| Opus 5 · high | 10.1s | 2.448¢ | 100% |
| GPT-5.6 Luna · high | 15.6s | 0.052¢ | 84.0% |
| GPT-5.6 Luna · max | 17.0s | 0.059¢ | 87.9% |

Opus cache-write tokens per turn, one session: **14,027** on turn 1, then 262 / 260 / 518 / 257.

## Findings

1. **Warm sessions do not make turns faster.** No arm improved materially from turn 2 to turn 6. The prompt cache was already ~92% warm on the first turn, so there was almost no headroom for warming to buy anything.

2. **Opus 5's cost drops about 4x in session, and the mechanism is visible.** 10.10¢ cold → 2.45¢ warm, because the ~14K-token cache write collapses to ~260 tokens after the first turn. Its per-request context also plateaus (~31K tokens from turn 2 onward) rather than growing.

3. **Luna's per-turn cost is roughly flat, and slightly cheaper warm than cold.** 0.11¢ cold → 0.052-0.059¢ warm. It does **not** climb across a session; the earlier claim that it did was the cumulative-counter artifact described above.

4. **The cost gap narrows but does not close: about 90x cold, about 43x in session.** Both models get cheaper warm; Opus falls further because it stops re-paying the cache write.

5. **Replicates fixed the backwards ordering.** Luna high 0.052¢ vs Luna max 0.059¢ at n=15 (84% and 88% cache hit), against 0.52¢ vs 0.27¢ from two lone sessions. Treat the two Luna arms as equal here regardless.

## Caveats

- **Small, tool-free questions.** The ~43x in-session ratio is specific to this shape and does **not** generalise to agentic work. On a real find-and-fix benchmark over two repositories, the same two models sat between 21x and 90x, because cost there is dominated by cache reads, where the rate gap is structural (25x by list price).
- **n=15 warm calls per configuration**, from 3 sessions of 5 warm turns. Enough to separate Opus from Luna, not enough to rank the two Luna arms.
- **Absolute times are not portable across sessions.** Everything here was measured in one interleaved window; a run 90 minutes earlier had every arm roughly 2x slower.
- **Timing includes CLI startup**, as in experiment 01.
- **Cost is API-equivalent**, computed from reported tokens at list rates. Both arms ran on subscriptions.
- **6 turns is short.** Where a growing transcript starts to hurt, and where compaction earns its keep, is not measured here.
