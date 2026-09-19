# 02 · House rules, n=24: how does your domain reach a model you cannot train?

## Question

Jev's documentation describes no fine-tuning, no custom training and no calibration on customer
data. So every company-specific rule has to arrive through the request itself. Two things follow
that are worth measuring rather than assuming: **which channel actually carries a rule** (criteria
text, or labelled examples), and **what the model does when the rule exists inside your company but
was never written into the prompt**.

The second half matters because it is the normal case. Most routing policy lives in someone's head
or in a wiki, not in the API call.

## Method

**Corpus.** 24 support messages, 4 teams (`billing`, `support`, `sales`, `trust_safety`), 6 house
policies with 4 messages each. Every policy is a deliberate **inversion of the natural reading**, so
the correct answer cannot be reached by default industry knowledge:

| policy | house rule | what the obvious reading says |
|---|---|---|
| charge errors (duplicate, wrong amount) | `support` | billing |
| cancellations and account closure | `billing` | support / retention |
| refunds requested outside 30 days | `sales` | billing |
| logins, password resets, lockouts, 2FA | `trust_safety` | support |
| invoice copies, reissues, tax detail fixes | `support` | billing |
| plan changes (upgrade, downgrade, seats, billing period) | `billing` | sales |

Every message and every rule is in
[`bench/jev_houserule_n24_20260919.py`](bench/jev_houserule_n24_20260919.py).

**Three conditions**, each run against both `typesafe/jev-1.13` and `mistralai/ministral-8b-2512`:

1. **neutral** — criteria are the bare team names (`"billing": "billing team"`), instruction
   `Route this message to a team.` The house rule is never supplied, so this measures what the model
   does with a rule it cannot know.
2. **house rule in criteria** — the policy written into the `criteria` text for each team.
3. **neutral + examples** — bare team names again, plus 8 labelled past routing decisions placed in
   `state` (2 per team, covering 4 of the 6 policies).

144 calls total. Raw per-decision records, including Jev's confidence on every answer:
[`results/jev-houserule-n24-20260919.json`](results/jev-houserule-n24-20260919.json).

## Results

**Accuracy against the house rule (n=24 per cell).**

| condition | `jev-1.13` | `ministral-8b` |
|---|---|---|
| neutral — rule NOT supplied | **5/24** | 7/24 |
| house rule written into `criteria` | **24/24** | 24/24 |
| neutral + 8 labelled examples in `state` | 13/24 | **18/24** |

**Jev's confidence, by condition.**

| condition | mean conf. when it followed the rule | mean conf. when it broke the rule | misses above 0.90 |
|---|---|---|---|
| neutral | 0.950 (n=5) | 0.902 (n=19) | **15 of 19** |
| house rule in criteria | 0.988 (n=24) | — (no misses) | — |
| neutral + examples | 0.855 (n=13) | 0.724 (n=11) | 4 of 11 |

## Findings

1. **Criteria text is the channel, and it works completely.** Written into `criteria`, an arbitrary
   policy that contradicts the obvious answer is followed 24 out of 24 times, at 0.988 mean
   confidence. Whatever else is true, steering is not the weak point.
2. **Labelled examples are a much weaker channel — and weaker here than on an ordinary 8B.** Given
   the same 8 examples in place of rules, Jev reached 13/24 while ministral-8b reached 18/24. This
   is the one place a "learns from your data" story would show up in the numbers, and it does not.
   Nothing accumulates between calls either: every rule has to be re-sent on every request.
3. **When the rule is unstated, it is confidently wrong.** 5/24, with **15 of the 19 misses above
   0.90 confidence**. Read together with experiment 01, where every error on a document-answerable
   task landed below 0.80, the shape is specific: the confidence number tracks **whether the text is
   clear**, not whether the model knows your business. Unstated policy is invisible to it, and
   invisible in a way the confidence score does not flag.
4. **So the threshold from experiment 01 protects you against ambiguous documents, not against
   missing rules.** Those are different failures and only one of them shows up in the number.

## Caveats

- **n = 24 per cell, one run per cell.** No repeats; this does not bound run-to-run variance.
- **An earlier version of this test at n=4 was reported wrongly, and the correction is the reason
  this one exists.** That version used the same inversion design and reported "2 of 4 wrong at
  0.97–0.99 confidence" as evidence of general overconfidence. That reading was wrong: the ground
  truth was an unstated arbitrary rule, so a confident *correct-by-industry-standard* answer was
  being scored as miscalibration. The honest claim is the narrower one in finding 3 — unstated rules
  are unreachable and the confidence number does not flag their absence. The n=4 version measured a
  real thing and described it as something bigger.
- **The inversions are deliberately adversarial.** Real house rules usually align with the obvious
  reading more often than these do, so the neutral-condition score is a floor, not an estimate of
  what a real policy set would produce.
- **The examples condition is not a fair test of few-shot learning in general.** 8 examples covering
  4 of 6 policies is a small, partial demonstration set, chosen to match what a team would plausibly
  paste in. A larger or better-covering set would likely score higher. What it does establish is
  that at the same budget, examples carry less than rules do.
- **Only two arms.** Jev and one 8B. This says nothing about how frontier chat models handle the
  same three conditions.
- **What would invalidate finding 3:** a run where unstated-rule errors come back with low
  confidence, which would mean the number is tracking knowledge rather than textual clarity.
