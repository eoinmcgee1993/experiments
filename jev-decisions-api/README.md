# Jev decisions API

TypeSafe's Jev is a typed "decision model": you send text, a question and a list of options, and it
returns one option plus a confidence number. It never writes prose, and its output tokens are billed
at $0. In the 72 hours after launch it drew a large wave of projects and a set of widely-shared
comparison figures in the "hundreds of times cheaper" range, all measured against frontier models.
Nobody had published a measurement.

This set is that measurement. Two questions: **does it actually win on its own showcase task**, and
**can your domain knowledge reach it at all** when there is no fine-tuning channel.

Every document, every routing message, the criteria text, the exact scripts and the per-decision
records are in these folders. Total spend across both experiments: **$0.23**, 644 live API calls.

| # | Experiment | Question | Headline result |
|---|---|---|---|
| [01](01-fifty-documents-six-models/) | 50 documents, six models | On the task the vendor advertises, hardened until it discriminates, how does Jev compare on accuracy and on billed cost? | **Jev 50/50 at $0.025 per 1,000 decisions — and Claude Haiku 4.5 also 50/50 at 15.7x, two open models you can run yourself at 48/50 for 1.2–1.25x, and Opus 5 at 115x one answer behind.** With the written definitions removed, every one of Jev's errors came in below 0.80 confidence, so a 0.80 auto-approve cut let zero wrong answers through. |
| [02](02-house-rules-n24/) | House rules, n=24 | With no fine-tuning, how does company-specific policy reach the model — and what does it do when that policy is never written down? | **Written into the criteria: 24/24. Left unstated: 5/24, with 15 of the 19 misses above 0.90 confidence.** Labelled examples in state are a much weaker channel: 13/24, where an 8B open model scored 18/24 on the same examples. |

## Method notes

- One arm is the Jev Choice primitive (`POST /api/alpha/decisions`, model `typesafe/jev-1.13`). The
  other arms are ordinary chat models (`POST /v1/chat/completions`) asked for JSON only. Both go
  through OpenRouter, so the billed `cost` field is produced by the same accounting on both sides.
- Every arm receives the **same criteria text and the same instruction**, byte for byte. The chat
  arms get it inlined in the prompt; the Jev arm gets it in `criteria` and `instructions`. Both
  prompt forms are in the scripts, verbatim.
- Cost is read from each individual response, never from a pricing page. `$/1k decisions` is the
  summed billed cost divided by the number of usable answers, times 1,000.
- Jev exposes `supported_parameters: []` — no temperature, no seed, no top_p. The chat arms are all
  run at `temperature: 0`, which is the closest available comparison, not an identical one.
- Re-run: `set OPENROUTER_API_KEY`, then run the scripts in each experiment's `bench/` folder. They
  write into that experiment's `results/`.

## Caveats that apply to both experiments

- **The corpus is synthetic.** I wrote all 50 documents and all 24 routing messages. They are
  modelled on real document types, but no real invoice, customer message or company policy is in
  here, and a synthetic corpus cannot tell you what production accuracy will be.
- **I wrote the test and I had a prior.** The set was hardened specifically until it discriminated
  between models, after a first version that everything passed. That first, non-discriminating
  version is reported in experiment 01 rather than dropped.
- **Ground truth is my reading of my own definitions.** Where a document is genuinely contestable
  under those definitions, that is a defect in the item, not a model error. The full text of every
  item and its assigned label is in the scripts, so you can disagree with specific ones.
- **Accuracy and cost are concurrency-invariant; latency is not.** The main runs are concurrent, so
  per-call milliseconds from them are not comparable across arms. Latency is quoted only from an
  earlier sequential round and is labelled as such wherever it appears.
