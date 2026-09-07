# AI slop bench V1: tell counts, calibration, the steered pilot

The head-to-head matrix (the headline) is in results/tournament.md; judge reliability in results/panel.md.

Arms: GPT-6 Astra, GPT-5.6 Sol, Fable 5.1, Opus 5, Grok 4.6, GPT-5.6 Terra, GPT-5.6 Luna, Muse Spark 1.3, Kimi K3, Gemini 3.8 Flash, GLM-5.3, Qwen 3.8 Flash. Prompts: 3. Samples per cell: 3. Default sampling and default reasoning effort everywhere. No system prompt. Variants:

- **bare**: the task text only.
- **steered**: the task text plus one line of style instruction, the kind a practitioner would type (`Plain prose only: no headers, no bullet points, no bold text, no em dashes. Write like a person.`).

The request bodies in the receipts are the models' entire context.

## 1. Deterministic tells (no model in the loop)

Counts per 1,000 words, `bench/score.py`, same code for every text. Lower is fewer tells. Markdown structure (headers, bullets) is reported but outside the composite. The human row is the author's own LinkedIn posts from 2021-2022, before ChatGPT.

### bare

| Text source | n | words | tells /1k | em_dash | neg_parallel | triad | signpost | self_clap | filler_transition | slop_words | bold_label | participial_tail | closing_recap | md_structure |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Human control (pre-ChatGPT posts) | 15 | 309 | **6.9** | 3.24 | 0.65 | 1.08 | 0.0 | 0.0 | 0.86 | 0.65 | 0.0 | 0.43 | 0.0 | 24.17 |
| Fable 5.1 | 9 | 493 | **14.2** | 6.76 | 1.58 | 2.48 | 0.68 | 0.23 | 0.0 | 0.23 | 1.8 | 0.45 | 0.0 | 14.42 |
| GPT-5.6 Luna | 9 | 320 | **17.0** | 5.22 | 1.39 | 5.91 | 0.7 | 0.0 | 0.0 | 1.39 | 1.04 | 1.39 | 0.0 | 18.78 |
| GPT-5.6 Terra | 9 | 324 | **18.2** | 7.54 | 2.06 | 5.48 | 1.03 | 0.0 | 0.0 | 0.69 | 1.03 | 0.34 | 0.0 | 20.21 |
| Opus 5 | 9 | 495 | **20.0** | 7.63 | 1.35 | 0.9 | 0.45 | 0.22 | 0.0 | 0.45 | 8.98 | 0.0 | 0.0 | 20.88 |
| GPT-5.6 Sol | 9 | 286 | **21.4** | 7.38 | 1.94 | 8.15 | 0.78 | 0.0 | 0.78 | 1.16 | 0.39 | 0.0 | 0.78 | 13.59 |
| GPT-6 Astra | 9 | 289 | **21.5** | 4.22 | 1.15 | 8.83 | 0.0 | 0.0 | 0.38 | 0.0 | 5.76 | 0.77 | 0.38 | 12.28 |
| Kimi K3 | 9 | 404 | **22.8** | 14.31 | 1.1 | 2.2 | 0.83 | 0.0 | 0.28 | 0.0 | 3.03 | 1.1 | 0.0 | 22.01 |
| Grok 4.6 | 9 | 341 | **23.2** | 8.16 | 1.96 | 10.44 | 0.65 | 0.0 | 0.0 | 0.33 | 0.98 | 0.65 | 0.0 | 9.79 |
| GLM-5.3 | 9 | 437 | **23.4** | 15.51 | 1.27 | 3.05 | 0.76 | 0.0 | 0.0 | 0.51 | 1.78 | 0.51 | 0.0 | 18.06 |
| Qwen 3.8 Flash | 9 | 338 | **23.7** | 7.56 | 0.99 | 11.18 | 0.33 | 0.0 | 0.0 | 0.66 | 2.3 | 0.66 | 0.0 | 17.75 |
| Gemini 3.8 Flash | 9 | 388 | **24.6** | 5.44 | 0.57 | 4.58 | 0.29 | 0.0 | 0.57 | 3.44 | 6.87 | 2.86 | 0.0 | 16.9 |
| Muse Spark 1.3 | 9 | 303 | **25.7** | 10.65 | 1.1 | 3.67 | 0.73 | 0.0 | 0.0 | 0.73 | 8.08 | 0.73 | 0.0 | 19.09 |

### steered

| Text source | n | words | tells /1k | em_dash | neg_parallel | triad | signpost | self_clap | filler_transition | slop_words | bold_label | participial_tail | closing_recap | md_structure |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Grok 4.6 | 9 | 294 | **3.4** | 0.0 | 0.0 | 3.4 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Opus 5 | 9 | 511 | **3.5** | 0.0 | 0.44 | 1.96 | 0.44 | 0.44 | 0.0 | 0.0 | 0.0 | 0.22 | 0.0 | 0.0 |
| Fable 5.1 | 9 | 505 | **4.2** | 0.0 | 0.22 | 2.64 | 0.66 | 0.0 | 0.22 | 0.0 | 0.0 | 0.44 | 0.0 | 0.0 |
| Human control (pre-ChatGPT posts) | 15 | 309 | **6.9** | 3.24 | 0.65 | 1.08 | 0.0 | 0.0 | 0.86 | 0.65 | 0.0 | 0.43 | 0.0 | 24.17 |
| GPT-6 Astra | 9 | 271 | **8.2** | 0.0 | 0.41 | 5.33 | 0.0 | 0.0 | 0.41 | 0.0 | 0.0 | 1.64 | 0.41 | 0.0 |
| GPT-5.6 Sol | 9 | 270 | **12.0** | 0.0 | 0.82 | 9.07 | 0.0 | 0.0 | 0.0 | 0.82 | 0.0 | 0.82 | 0.41 | 0.0 |

### Steerability, deterministic

Same model, same prompt, plus the one steering line. Change is steered minus bare, per 1,000 words.

| Model | bare | steered | change | em dashes bare -> steered | bold labels bare -> steered | md structure bare -> steered | words bare -> steered |
|---|--:|--:|--:|--:|--:|--:|--:|
| GPT-6 Astra | 21.5 | 8.2 | **-13.3** | 4.22 -> 0.0 | 5.76 -> 0.0 | 12.28 -> 0.0 | 289 -> 271 |
| GPT-5.6 Sol | 21.4 | 12.0 | **-9.4** | 7.38 -> 0.0 | 0.39 -> 0.0 | 13.59 -> 0.0 | 286 -> 270 |
| Fable 5.1 | 14.2 | 4.2 | **-10.0** | 6.76 -> 0.0 | 1.8 -> 0.0 | 14.42 -> 0.0 | 493 -> 505 |
| Opus 5 | 20.0 | 3.5 | **-16.5** | 7.63 -> 0.0 | 8.98 -> 0.0 | 20.88 -> 0.0 | 495 -> 511 |
| Grok 4.6 | 23.2 | 3.4 | **-19.8** | 8.16 -> 0.0 | 0.98 -> 0.0 | 9.79 -> 0.0 | 341 -> 294 |

Per prompt, tells per 1,000 words (mean of samples):

| Model | bare p1-essay | bare p2-launch | bare p3-linkedin | steered p1-essay | steered p2-launch | steered p3-linkedin |
|---|--:|--:|--:|--:|--:|--:|
| GPT-6 Astra | 22.4 | 28.3 | 15.5 | 9.7 | 5.2 | 7.3 |
| GPT-5.6 Sol | 22.6 | 13.5 | 24.5 | 10.7 | 20.1 | 9.3 |
| Fable 5.1 | 18.4 | 13.6 | 10.6 | 0.6 | 10.1 | 2.0 |
| Opus 5 | 25.0 | 18.0 | 16.8 | 1.9 | 6.5 | 2.0 |
| Grok 4.6 | 31.3 | 33.3 | 8.9 | 3.3 | 4.7 | 2.6 |
| GPT-5.6 Terra | 20.1 | 12.6 | 19.6 | - | - | - |
| GPT-5.6 Luna | 11.4 | 21.1 | 21.5 | - | - | - |
| Muse Spark 1.3 | 26.7 | 27.2 | 22.0 | - | - | - |
| Kimi K3 | 25.7 | 21.7 | 20.4 | - | - | - |
| Gemini 3.8 Flash | 25.0 | 31.0 | 17.9 | - | - | - |
| GLM-5.3 | 27.5 | 29.1 | 13.3 | - | - | - |
| Qwen 3.8 Flash | 26.8 | 30.3 | 10.9 | - | - | - |

Rhythm, bare variant (mean sentence length in words, share of sentences in the most common 10-word band, share of sentences of 3 words or fewer):

| Text source | sent. mean | 10w band | staccato |
|---|--:|--:|--:|
| Human control (pre-ChatGPT posts) | 12.7 | 0.55 | 0.02 |
| GPT-6 Astra | 14.4 | 0.6 | 0.02 |
| GPT-5.6 Sol | 14.4 | 0.55 | 0.03 |
| Fable 5.1 | 14.8 | 0.45 | 0.06 |
| Opus 5 | 15.6 | 0.55 | 0.03 |
| Grok 4.6 | 13.2 | 0.54 | 0.07 |
| GPT-5.6 Terra | 14.0 | 0.53 | 0.06 |
| GPT-5.6 Luna | 16.2 | 0.53 | 0.02 |
| Muse Spark 1.3 | 12.2 | 0.57 | 0.1 |
| Kimi K3 | 13.0 | 0.56 | 0.09 |
| Gemini 3.8 Flash | 16.0 | 0.42 | 0.06 |
| GLM-5.3 | 13.2 | 0.5 | 0.09 |
| Qwen 3.8 Flash | 15.2 | 0.57 | 0.04 |

## 2. Blind pairwise judges (rubric in `bench/rubric.md`)

Each pair shown in both orders; a verdict counts only if the judge named the same text both times. 'Named more AI' is the share of resolved pairs in which the judge pointed at this model. Lower is better. Calibration pairs a human post with a model post; a judge must name the model.

### bare

**Gemini 3.8 Flash (thinking high)** (Google): resolved 353 of 495 pairs, 142 flipped with order. Calibration: named the model 99, the human 0, flipped 0.

**Grok 4.6** (xAI): resolved 329 of 495 pairs, 166 flipped with order. Calibration: named the model 96, the human 0, flipped 3.

**Opus 5** (Anthropic): resolved 274 of 405 pairs, 131 flipped with order. Calibration: named the model 90, the human 0, flipped 0.

**GPT-5.6 Sol (medium)** (OpenAI): resolved 205 of 252 pairs, 47 flipped with order. Calibration: named the model 70, the human 0, flipped 2.

| Model | Gemini 3.8 Flash | Grok 4.6 | Opus 5 | GPT-5.6 Sol | combined | pairs |
|---|--:|--:|--:|--:|--:|--:|
| Fable 5.1 | 8% | 19% | 0% | 17% | **14%** | 167 |
| Grok 4.6 | 29% | 0% | 15% | 17% | **20%** | 177 |
| GPT-6 Astra | 36% | 22% | 15% | 0% | **25%** | 187 |
| Opus 5 | 18% | 17% | 0% | 40% | **25%** | 178 |
| Muse Spark 1.3 | 56% | 55% | 42% | 70% | **56%** | 234 |
| GLM-5.3 | 64% | 57% | 35% | 64% | **56%** | 228 |
| Kimi K3 | 68% | 55% | 33% | 68% | **56%** | 222 |
| GPT-5.6 Sol | 63% | 55% | 68% | 0% | **62%** | 186 |
| Qwen 3.8 Flash | 73% | 57% | 68% | 51% | **63%** | 241 |
| GPT-5.6 Luna | 65% | 54% | 79% | 0% | **66%** | 169 |
| GPT-5.6 Terra | 66% | 75% | 85% | 0% | **75%** | 185 |
| Gemini 3.8 Flash | 0% | 85% | 70% | 76% | **78%** | 148 |

### steered

**Gemini 3.8 Flash (thinking high)** (Google): resolved 70 of 90 pairs, 20 flipped with order. Calibration: named the model 4, the human 0, flipped 1.

**Grok 4.6** (xAI): resolved 0 of 0 pairs, 0 flipped with order. Calibration: named the model 0, the human 0, flipped 0.

**Opus 5** (Anthropic): resolved 0 of 0 pairs, 0 flipped with order. Calibration: named the model 0, the human 0, flipped 0.

**GPT-5.6 Sol (medium)** (OpenAI): resolved 0 of 0 pairs, 0 flipped with order. Calibration: named the model 0, the human 0, flipped 0.

| Model | Gemini 3.8 Flash | Grok 4.6 | Opus 5 | GPT-5.6 Sol | combined | pairs |
|---|--:|--:|--:|--:|--:|--:|
| GPT-5.6 Terra | 0% | 0% | 0% | 0% | **0%** | 0 |
| GPT-5.6 Luna | 0% | 0% | 0% | 0% | **0%** | 0 |
| Muse Spark 1.3 | 0% | 0% | 0% | 0% | **0%** | 0 |
| Kimi K3 | 0% | 0% | 0% | 0% | **0%** | 0 |
| Gemini 3.8 Flash | 0% | 0% | 0% | 0% | **0%** | 0 |
| GLM-5.3 | 0% | 0% | 0% | 0% | **0%** | 0 |
| Qwen 3.8 Flash | 0% | 0% | 0% | 0% | **0%** | 0 |
| Fable 5.1 | 11% | 0% | 0% | 0% | **11%** | 28 |
| Opus 5 | 20% | 0% | 0% | 0% | **20%** | 25 |
| Grok 4.6 | 42% | 0% | 0% | 0% | **42%** | 24 |
| GPT-6 Astra | 59% | 0% | 0% | 0% | **59%** | 27 |
| GPT-5.6 Sol | 100% | 0% | 0% | 0% | **100%** | 36 |

### Steerability, judged: each model's bare text vs its own steered text

Same prompt, same sample index. 'Steered less AI' counts pairs where the judge named the bare text as the one with more tells in both orders.

| Model | Gemini 3.8 Flash: steered less / bare less / flip | Grok 4.6: steered less / bare less / flip | Opus 5: steered less / bare less / flip | GPT-5.6 Sol: steered less / bare less / flip | combined steered less |
|---|---|---|---|---|--:|
| GPT-6 Astra | 9 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | **9/9** |
| GPT-5.6 Sol | 8 / 1 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | **8/9** |
| Fable 5.1 | 9 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | **9/9** |
| Opus 5 | 9 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | **9/9** |
| Grok 4.6 | 9 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | **9/9** |
| GPT-5.6 Terra | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | **0/0** |
| GPT-5.6 Luna | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | **0/0** |
| Muse Spark 1.3 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | **0/0** |
| Kimi K3 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | **0/0** |
| Gemini 3.8 Flash | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | **0/0** |
| GLM-5.3 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | **0/0** |
| Qwen 3.8 Flash | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | **0/0** |

## 3. Run facts

| Model | variant | serving path | effort | reasoning tok (mean) | wall s (mean) | input tok seen by model |
|---|---|---|---|--:|--:|--:|
| GPT-6 Astra | bare | OpenAI first-party, Responses API | medium | 45 | 12 | 36 |
| GPT-5.6 Sol | bare | OpenAI first-party, Responses API | medium | 39 | 8 | 36 |
| Fable 5.1 | bare | OpenRouter -> Anthropic (first-party key unavailable at run time) | default (not set) | 182 | 23 | 53 |
| Opus 5 | bare | OpenRouter -> Anthropic (first-party key unavailable at run time) | default (not set) | 370 | 22 | 51 |
| Grok 4.6 | bare | xAI first-party, chat completions | default (not set) | 566 | 19 | 666 |
| GPT-5.6 Terra | bare | OpenAI first-party, Responses API | medium | 33 | 8 | 36 |
| GPT-5.6 Luna | bare | OpenAI first-party, Responses API | medium | 60 | 6 | 36 |
| Muse Spark 1.3 | bare | OpenRouter -> Meta | default (not set) | 1464 | 20 | 37 |
| Kimi K3 | bare | OpenRouter -> Moonshot AI | default (not set) | 2098 | 33 | 118 |
| Gemini 3.8 Flash | bare | Google first-party, generateContent (thinking level not set) | default (not set) | 776 | 7 | 32 |
| GLM-5.3 | bare | OpenRouter -> Z.ai | default (not set) | 3996 | 100 | 42 |
| Qwen 3.8 Flash | bare | OpenRouter -> Alibaba | default (not set) | 769 | 14 | 93 |
| GPT-6 Astra | steered | OpenAI first-party, Responses API | medium | 37 | 14 | 61 |
| GPT-5.6 Sol | steered | OpenAI first-party, Responses API | medium | 37 | 8 | 61 |
| Fable 5.1 | steered | OpenRouter -> Anthropic (first-party key unavailable at run time) | default (not set) | 289 | 24 | 88 |
| Opus 5 | steered | OpenRouter -> Anthropic (first-party key unavailable at run time) | default (not set) | 226 | 20 | 86 |
| Grok 4.6 | steered | xAI first-party, chat completions | default (not set) | 1309 | 32 | 690 |
