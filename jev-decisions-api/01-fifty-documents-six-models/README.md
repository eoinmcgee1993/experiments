# 01 · 50 documents, six models: does the decision model actually win its own showcase task?

## Question

Invoice classification is the use case the vendor advertises, and the circulating cost comparisons
for Jev were all measured against frontier models. On that task, hardened until it discriminates:
how does Jev compare with the models an engineer would really choose, on accuracy and on billed
cost — and is its confidence number usable as an auto-approve threshold?

## Method

**Corpus.** 50 documents, 6 classes (`invoice`, `receipt`, `quote`, `purchase_order`,
`credit_note`, `statement`). Every document, with its assigned label, is in
[`bench/jev_quality_round2_20260919.py`](bench/jev_quality_round2_20260919.py) (items 1–18) and
[`bench/jev_50docs_20260919.py`](bench/jev_50docs_20260919.py) (items 19–50).

32 of the 50 are written so the surface cue **lies**. The intent behind each trap is documented in
the script's docstring; in short:

- a `PROFORMA INVOICE` for goods already shipped (an invoice, though the title is the usual quote word)
- a purchase order carrying unit prices (the money cue points at `quote`)
- a document titled `INVOICE SUMMARY — SEPTEMBER` whose body states it is not a request for payment (a statement)
- a self-billed invoice, raised by the buyer (the buyer/seller cue points at `purchase_order`)
- a deposit invoice, demanding money before supply (the timing cue points at `quote`)
- a zero-balance statement (the balance cue points at `receipt`)
- a credit written as a positive number, and one credit note that never uses the word "credit"
- three documents with no giveaway vocabulary at all: a freelancer's email (an invoice), a casual restock message (a purchase order), a "nothing is booked yet" price in an email (a quote)
- ten languages (English, Polish, German, Portuguese, Czech, Spanish, French, Dutch, Italian, Hungarian, Japanese), OCR damage, an amount written out in words, and one document buried in a quoted email thread

**Prompt.** Every arm receives the same six definitions and the same instruction. The instruction,
verbatim:

> Classify this document using ONLY the supplied definitions. The document's own title may be misleading, the text may be damaged by OCR, and it may not be in English; follow the definitions.

The Jev arm sends the document in `state`, the definitions as `criteria` on a `choice` question, and
the instruction as `instructions`. The chat arms get the definitions and instruction inlined and are
asked for JSON only (`max_tokens: 900`, `temperature: 0`, system message `Reply with ONLY minified
JSON.`). Both prompt constructions are in
[`bench/jev_50docs_20260919.py`](bench/jev_50docs_20260919.py).

**Runs.** 50 documents × 6 arms = 300 calls, 12 concurrent workers, 39s wall clock. One retry on a
transient failure so a network blip is not scored as a wrong answer. Raw per-decision records:
[`results/jev-50docs-20260919.json`](results/jev-50docs-20260919.json).

**Definitions-removed run.** The same 50 documents, the same arms, with `criteria` reduced to the
bare class names (`"invoice": "invoice"`) and the instruction reduced to `Classify this document.`
200 calls. [`bench/jev_50docs_nodefs_20260919.py`](bench/jev_50docs_nodefs_20260919.py),
[`results/jev-50docs-nodefs-20260919.json`](results/jev-50docs-nodefs-20260919.json).

**The first, non-discriminating version.** Before this corpus there was a 20-document version and
then an 18-document version. On the 20-document version **every arm scored 20/20**, including an 8B.
That round is kept in [`results/jev-quality-round2-20260919.json`](results/jev-quality-round2-20260919.json)
and is the reason the corpus was hardened. It is also the most likely explanation for why a public
comparison on this task shows no separation.

## Results

**Accuracy and billed cost, definitions supplied (n=50 per arm).**

| arm | class | correct | $/1k decisions | × vs Jev |
|---|---|---|---|---|
| `typesafe/jev-1.13` | typed decisions API | **50/50** | **$0.0247** | 1.00× |
| `openai/gpt-oss-20b` | open 20B | 48/50 | $0.0298 | 1.21× |
| `mistralai/ministral-8b-2512` | open 8B | 48/50 | $0.0309 | 1.25× |
| `anthropic/claude-haiku-4.5` | small, hosted | **50/50** | $0.3885 | 15.74× |
| `google/gemini-3.8-flash` | small, hosted | 49/50 | $1.0287 | 41.67× |
| `anthropic/claude-opus-5` | frontier | 49/50 | $2.8337 | 114.79× |

Jev billed 29,389 input and 3,113 output tokens across the 50 decisions. Output is priced at $0, so
the free-output headline is real; at one question per call it is worth about 4% of the bill.

**Every miss, all arms.** Four documents account for all six errors.

| item | true class | arm | picked |
|---|---|---|---|
| #13 statement buried in a billing email | `statement` | gpt-oss-20b | `receipt` |
| #13 | `statement` | ministral-8b | `receipt` |
| #16 statement of account, one open item, "please pay this amount" | `statement` | gemini-3.8-flash | `invoice` |
| #16 | `statement` | claude-opus-5 | `invoice` |
| #27 reminder of open items, three documents, one total | `statement` | ministral-8b | `invoice` |
| #39 `ORDER FORM`, binding only when signed | `quote` | gpt-oss-20b | `purchase_order` |

Every error in the whole run is a `statement` or a `quote` being read as something that demands
payment. No arm missed an item in the OCR, non-English or no-vocabulary groups.

**Definitions removed (bare class names).**

| arm | with definitions | without | Δ |
|---|---|---|---|
| `typesafe/jev-1.13` | 50/50 | 46/49 | −4 |
| `openai/gpt-oss-20b` | 48/50 | 46/50 | −2 |
| `mistralai/ministral-8b-2512` | 48/50 | 48/50 | 0 |
| `anthropic/claude-haiku-4.5` | 50/50 | 49/50 | −1 |

Jev's n is 49, not 50: one call returned HTTP 520 and both attempts failed. That is 1 failure in
1,079 calls across the whole investigation.

**Jev's confidence against its own correctness, definitions removed.**

| | mean confidence | n |
|---|---|---|
| answers it got right | 0.969 | 46 |
| answers it got wrong | 0.607 (max 0.770) | 3 |

Its three wrong answers, with the confidence it reported: 0.77 on an OCR-damaged `PRO FORMA INVOICE`
marked "not a tax invoice, goods not yet shipped" (a quote, called an invoice); 0.44 on the same
document type in Polish; 0.61 on a `TAX INVOICE` marked settled and paid (a receipt, called an
invoice).

**Auto-approve thresholds on the Jev arm.** "Wrong" = an incorrect answer that clears the threshold
and would ship without review.

| threshold | with definitions | without definitions |
|---|---|---|
| ≥0.80 | 48 auto (**0 wrong**), 2 to a human | 44 auto (**0 wrong**), 5 to a human |
| ≥0.90 | 47 auto (**0 wrong**), 3 to a human | 42 auto (**0 wrong**), 7 to a human |
| ≥0.95 | 45 auto (**0 wrong**), 5 to a human | 41 auto (**0 wrong**), 8 to a human |

## Findings

1. **Jev wins the table, and the win is one item wide.** 50/50 at the lowest cost in the field. But
   Claude Haiku 4.5 also scored 50/50, and the two open models that run on your own hardware landed
   48/50 at 1.21× and 1.25× the cost. The gap between Jev and a model you can self-host is one
   document and a quarter of a cent per thousand decisions.
2. **The "hundreds of times cheaper" figures are a property of the denominator.** Against Opus 5,
   Jev is 114.79× cheaper here — the right order of magnitude for the circulating claims, and a
   comparison nobody actually faces, because nobody classifies invoices with a frontier model.
   Against the 8B an engineer would really reach for, it is 1.25× cheaper and, in the earlier
   sequential round, slower (337 ms vs 248 ms median, one question per call).
3. **Opus 5, at 114.79× the price, finished one answer behind.** Price and accuracy are uncorrelated
   across this whole field.
4. **The confidence number is a usable threshold when the answer is in the document.** With the
   definitions stripped out, every error Jev made landed below 0.80 while its correct answers
   averaged 0.969. At a 0.80 cut, in both conditions, nothing wrong got through, and a human sees 2
   or 5 documents out of 50. Free per-option probabilities that separate this cleanly are a real
   engineering primitive. **This is a property of this run, not a guarantee** — see experiment 02
   for the condition where the same number is confidently wrong.
5. **A benchmark everything passes is measuring nothing.** The first 20-document version returned
   20/20 for all arms. Had I published that, it would have shown a six-way tie.

## Caveats

- **n = 50 per arm, one run per arm per condition.** No repeats, so nothing here bounds run-to-run
  variance on the main table. An earlier round did test label stability directly: across 3 repeats,
  no arm changed a single label, while Jev's *probability* moved by up to 0.06 on ambiguous items
  with no temperature control available to stop it.
- **Synthetic corpus, written by me, hardened until it discriminated.** See the set README. Accuracy
  here is not a forecast of production accuracy.
- **All six errors are in two classes.** `statement` versus a payment demand accounts for five of
  the six. A corpus weighted differently would rank these arms differently.
- **`temperature: 0` on the chat arms is not the same setting as Jev's fixed decode**, because Jev
  exposes no sampling parameters at all. This is the closest available comparison, not a controlled
  one.
- **Latency is not measured here.** The 337/248 ms figures come from the earlier sequential round.
  Per-call timings in this run's records were taken under 12-way concurrency and should not be read
  as latency.
- **The records are parsed per-decision results, not full response bodies.** Each row carries the
  chosen label, the truth, the billed cost, token counts and wall time. Full request and response
  bodies were not retained, so the receipts here are thinner than elsewhere in this repo. The
  scripts reproduce them end to end.
- **What would invalidate finding 1:** a real, labelled production corpus on which the open models
  fall further behind than one item, or a repeat run in which Jev drops below 50/50 and the ranking
  changes.
