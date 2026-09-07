# AI Slop Bench

Which frontier model writes the most AI slop when nobody tells it how to write? Twelve models, three short
writing tasks, no system prompt, three samples each. Every text meets every other model's text for the same task
and sample, blind, and four judge models name the one that reads more like AI. A judge never scores its own
vendor. Every text, every judgment and every raw API response is in this folder.

| # | Experiment | Question | Headline result |
|---|---|---|---|
| [01](01-twelve-model-tournament/) | Twelve models, blind pairwise | Whose default prose reads most like AI? | **Fable 5.1 was picked as the AI text 14% of the time, Gemini 3.8 Flash 77%.** Grok 4.6 (22%), Opus 5 (24%) and GPT-6 Astra (30%) complete the group under a third; the other eight sit at 55% or above. 108 texts, 1,647 judgments, 30% discarded as order flips. The judges never picked a human post over a model's: 0 of 355 |

## Method notes

- Texts are byte-for-byte what each API returned to a bare prompt. No system prompt, no style guidance, default
  sampling and reasoning effort. The request body in each generation receipt is the model's entire context.
- One judgment is one judge on one pair of texts, shown in both orders. It counts only when the judge names the
  same text both times. A flip is discarded.
- Re-run: set `OPENAI_API_KEY`, `XAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, then
  `python bench/run_essays.py`, `python bench/judge.py`, `python bench/tournament.py`, `python bench/panel.py`,
  `python bench/calibration_by_arm.py`. Every script skips receipts that already exist.
