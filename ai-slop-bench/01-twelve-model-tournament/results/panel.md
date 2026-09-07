# Panel reliability, bare variant

## Per judge

| Judge | matchups scored | resolved | flips | flip rate | calibration: named model / named human / flip |
|---|--:|--:|--:|--:|---|
| Gemini 3.8 Flash (thinking high) | 495 | 353 | 142 | 29% | 99 / 0 / 0 |
| Grok 4.6 | 495 | 329 | 166 | 34% | 96 / 0 / 3 |
| Opus 5 | 405 | 274 | 131 | 32% | 90 / 0 / 0 |
| GPT-5.6 Sol (medium) | 252 | 205 | 47 | 19% | 70 / 0 / 2 |

## Agreement between judges

Matchups both judges resolved (no flip on either side), and how often they named the same text.

| Judges | both resolved | agree | agreement |
|---|--:|--:|--:|
| Gemini 3.8 Flash (thinking high) vs Grok 4.6 | 222 | 216 | 97% |
| Gemini 3.8 Flash (thinking high) vs Opus 5 | 185 | 166 | 90% |
| Gemini 3.8 Flash (thinking high) vs GPT-5.6 Sol (medium) | 115 | 107 | 93% |
| Grok 4.6 vs Opus 5 | 160 | 142 | 89% |
| Grok 4.6 vs GPT-5.6 Sol (medium) | 103 | 100 | 97% |
| Opus 5 vs GPT-5.6 Sol (medium) | 73 | 65 | 89% |

## Judges per pair

| Pair | eligible judges |
|---|---|
| GPT-6 Astra vs GPT-5.6 Sol | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-6 Astra vs Fable 5.1 | Gemini 3.8 Flash (thinking high), Grok 4.6 |
| GPT-6 Astra vs Opus 5 | Gemini 3.8 Flash (thinking high), Grok 4.6 |
| GPT-6 Astra vs Grok 4.6 | Gemini 3.8 Flash (thinking high), Opus 5 |
| GPT-6 Astra vs GPT-5.6 Terra | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-6 Astra vs GPT-5.6 Luna | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-6 Astra vs Muse Spark 1.3 | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-6 Astra vs Kimi K3 | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-6 Astra vs Gemini 3.8 Flash | Grok 4.6, Opus 5 |
| GPT-6 Astra vs GLM-5.3 | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-6 Astra vs Qwen 3.8 Flash | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Sol vs Fable 5.1 | Gemini 3.8 Flash (thinking high), Grok 4.6 |
| GPT-5.6 Sol vs Opus 5 | Gemini 3.8 Flash (thinking high), Grok 4.6 |
| GPT-5.6 Sol vs Grok 4.6 | Gemini 3.8 Flash (thinking high), Opus 5 |
| GPT-5.6 Sol vs GPT-5.6 Terra | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Sol vs GPT-5.6 Luna | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Sol vs Muse Spark 1.3 | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Sol vs Kimi K3 | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Sol vs Gemini 3.8 Flash | Grok 4.6, Opus 5 |
| GPT-5.6 Sol vs GLM-5.3 | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Sol vs Qwen 3.8 Flash | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| Fable 5.1 vs Opus 5 | Gemini 3.8 Flash (thinking high), Grok 4.6, GPT-5.6 Sol (medium) |
| Fable 5.1 vs Grok 4.6 | Gemini 3.8 Flash (thinking high), GPT-5.6 Sol (medium) |
| Fable 5.1 vs GPT-5.6 Terra | Gemini 3.8 Flash (thinking high), Grok 4.6 |
| Fable 5.1 vs GPT-5.6 Luna | Gemini 3.8 Flash (thinking high), Grok 4.6 |
| Fable 5.1 vs Muse Spark 1.3 | Gemini 3.8 Flash (thinking high), Grok 4.6, GPT-5.6 Sol (medium) |
| Fable 5.1 vs Kimi K3 | Gemini 3.8 Flash (thinking high), Grok 4.6, GPT-5.6 Sol (medium) |
| Fable 5.1 vs Gemini 3.8 Flash | Grok 4.6, GPT-5.6 Sol (medium) |
| Fable 5.1 vs GLM-5.3 | Gemini 3.8 Flash (thinking high), Grok 4.6, GPT-5.6 Sol (medium) |
| Fable 5.1 vs Qwen 3.8 Flash | Gemini 3.8 Flash (thinking high), Grok 4.6, GPT-5.6 Sol (medium) |
| Opus 5 vs Grok 4.6 | Gemini 3.8 Flash (thinking high), GPT-5.6 Sol (medium) |
| Opus 5 vs GPT-5.6 Terra | Gemini 3.8 Flash (thinking high), Grok 4.6 |
| Opus 5 vs GPT-5.6 Luna | Gemini 3.8 Flash (thinking high), Grok 4.6 |
| Opus 5 vs Muse Spark 1.3 | Gemini 3.8 Flash (thinking high), Grok 4.6, GPT-5.6 Sol (medium) |
| Opus 5 vs Kimi K3 | Gemini 3.8 Flash (thinking high), Grok 4.6, GPT-5.6 Sol (medium) |
| Opus 5 vs Gemini 3.8 Flash | Grok 4.6, GPT-5.6 Sol (medium) |
| Opus 5 vs GLM-5.3 | Gemini 3.8 Flash (thinking high), Grok 4.6, GPT-5.6 Sol (medium) |
| Opus 5 vs Qwen 3.8 Flash | Gemini 3.8 Flash (thinking high), Grok 4.6, GPT-5.6 Sol (medium) |
| Grok 4.6 vs GPT-5.6 Terra | Gemini 3.8 Flash (thinking high), Opus 5 |
| Grok 4.6 vs GPT-5.6 Luna | Gemini 3.8 Flash (thinking high), Opus 5 |
| Grok 4.6 vs Muse Spark 1.3 | Gemini 3.8 Flash (thinking high), Opus 5, GPT-5.6 Sol (medium) |
| Grok 4.6 vs Kimi K3 | Gemini 3.8 Flash (thinking high), Opus 5, GPT-5.6 Sol (medium) |
| Grok 4.6 vs Gemini 3.8 Flash | Opus 5, GPT-5.6 Sol (medium) |
| Grok 4.6 vs GLM-5.3 | Gemini 3.8 Flash (thinking high), Opus 5, GPT-5.6 Sol (medium) |
| Grok 4.6 vs Qwen 3.8 Flash | Gemini 3.8 Flash (thinking high), Opus 5, GPT-5.6 Sol (medium) |
| GPT-5.6 Terra vs GPT-5.6 Luna | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Terra vs Muse Spark 1.3 | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Terra vs Kimi K3 | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Terra vs Gemini 3.8 Flash | Grok 4.6, Opus 5 |
| GPT-5.6 Terra vs GLM-5.3 | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Terra vs Qwen 3.8 Flash | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Luna vs Muse Spark 1.3 | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Luna vs Kimi K3 | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Luna vs Gemini 3.8 Flash | Grok 4.6, Opus 5 |
| GPT-5.6 Luna vs GLM-5.3 | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| GPT-5.6 Luna vs Qwen 3.8 Flash | Gemini 3.8 Flash (thinking high), Grok 4.6, Opus 5 |
| Muse Spark 1.3 vs Gemini 3.8 Flash | Grok 4.6, Opus 5, GPT-5.6 Sol (medium) |
| Kimi K3 vs Gemini 3.8 Flash | Grok 4.6, Opus 5, GPT-5.6 Sol (medium) |
| Gemini 3.8 Flash vs GLM-5.3 | Grok 4.6, Opus 5, GPT-5.6 Sol (medium) |
| Gemini 3.8 Flash vs Qwen 3.8 Flash | Grok 4.6, Opus 5, GPT-5.6 Sol (medium) |

Every pair not listed is scored by all 4 judges.
