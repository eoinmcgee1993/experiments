# Qwen3.8-Max: Day One (August 3, 2026)

Alibaba announced **Qwen3.8-Max** on Aug 3, 2026, ~02:15 UTC — 2.4 trillion parameters, "a new bar for coding and cowork," open weights promised for the following week. This set is the receipts behind one claim: **on my rig it is a mid-field bug hunter, and getting it to run at all was most of the day's work.**

Qwen3.8-Max is a **new arm bolted onto an existing rig**: the same two seeded repos, 105 bugs, prompts, and blind Codex judging as [bug-hunt-bench/](../bug-hunt-bench/) (Jul 19 – Aug 1: GPT-5.6 Sol/Luna, Opus 5, Fable 5, Grok 4.5, Kimi K3, Sonnet 5, Opus 4.8, DeepSeek V4). The comparison numbers quoted here are that set's numbers, not re-runs — read it first for the full method, the bench construction (repo B's bugs are real shipped regressions, reverted with their fix-commit SHAs), and the per-arm receipts. One thing this arm changes about its conclusions: P022, one of the "53 of 105 that survived every model" through Aug 1, is now fixed.

| # | Experiment | Question | Headline result |
|---|---|---|---|
| [01](01-two-repo-bug-hunt/) | Two-repo bug hunt | Is "a new bar for coding" a new bar on a real rig? | **19/105 planted bugs**, blind-judged at effort high — under Kimi K3 and Opus 5 (21 each), half of GPT-5.6 Sol's 42 (max). But it fixed **P022, a two-file API-contract plant no other model has fixed** in 18 scored runs, and **25 of its 26 claimed fixes verified real** |
| [02](02-five-attempts-to-run/) | Five attempts to run | What did day-one access actually cost? | **Five failed attempts across three endpoints** before one clean run: a 5-hour subscription quota gone in ~60 min of two-agent work, a mid-run gateway swap killed by replayed thinking-signature 404s, a free tier that hard-403'd instead of billing — **~$31 + one burned quota window + ~10h of clock for ~148 model-minutes** |

## Method notes & caveats

- **n=1 per repo.** Directional, not a ranking. The same rig at n=10 (different model set) shows planted-bug recall is unstable run to run: [frontier-vs-open-audit/](../frontier-vs-open-audit/).
- **Borrowed harness.** Qwen3.8-Max has no agentic CLI of its own; it ran in Claude Code through an Anthropic-API proxy shim to Alibaba's endpoints — the same arrangement as Kimi K3 in [kimi-k3-day-one/](../kimi-k3-day-one/). Comparison arms ran their native harnesses.
- **Effort is `high`, not max.** The "max" in the arm slug `qwen38max` is the model's name. Where a comparison number is a max-effort run (GPT-5.6 Sol's 42, Luna's 33), the table says so.
- **Day-one infrastructure.** The clean legs ran on the pay-as-you-go endpoint hours after launch; OpenRouter never listed the model during the bench window. Experiment 02 is about exactly that asymmetry. **This set expires** — the access story describes Aug 3, 2026 only.
- **Cost figures are token-estimates at Qwen Cloud list rates** ($2/M in, $0.25/M implicit-cache read, $6/M out). No OpenRouter listing means no independent credits-delta cross-check; treat every dollar figure accordingly.
- **What is published vs withheld.** Both repos are real: the Grok Build VS Code extension (mine) and Accredia (a production certification platform). Names are published; **the apps' code and bugs are not** — answer keys, seeded sources, agent transcripts/diffs, and judge packets are withheld, and the three judge-verified real (non-planted) Accredia defects appear in the verdicts as counts with descriptions redacted. Task prompts, metrics, verdicts, harness scripts, and raw run/proxy logs are published; machine paths are placeholder-scrubbed by [../.claude/hooks/anonymize.py](../.claude/hooks/anonymize.py). Nothing else is edited.

## Source post

[@PawelHuryn on X](https://x.com/i/status/2084345741812580853) · announcement: [@Alibaba_Qwen](https://x.com/i/status/2084100707423289643)

## License

MIT. Use anything; a link back is appreciated.
