# Survey tables (2026-08-24, all via OpenRouter)

## 1. Passage token count — 20 models

Δ = prompt_tokens(`x` + PASSAGE) − prompt_tokens(`x`); PASSAGE is the 456-char fixed string in `model_fingerprint.py`. Special-token Δ = prompt_tokens(`x <token>`) − prompt_tokens(`x`).

| model | served by | base "x" | passage Δ | `<\|endoftext\|>` Δ | `<think>` Δ |
|---|---|--:|--:|--:|--:|
| **stealth/ox-alpha** | Stealth | 88 | **172** | 6 | 3 |
| **z-ai/glm-5.3** | Z.AI | 13 | **172** | 6 | 3 |
| **z-ai/glm-5.2** | Z.AI / Baidu / Sail Research / Ambient | 13 | **172** | 2 | 2 |
| tencent/hy-mt2-1.8b | Tencent | 4 | 162 | 6 | 2 |
| x-ai/grok-4.6 | xAI | 207 | 161 | 5 | 3 |
| moonshotai/kimi-k3 | DeepInfra | 89–90 | 160 | 6 | 3 |
| deepseek/deepseek-v4-pro | DigitalOcean | 5 | 159 | 7 | 2 |
| stepfun/step-3.7-flash | Novita | 23 | 159 | 7 | 2 |
| minimax/minimax-m2.7 | Minimax | 42 | 156 | 6 | 2 |
| openai/gpt-5.6-sol | OpenAI | 7 | 155 | 7 | 3 |
| minimax/minimax-m3 | Together | 177 | 153 | 3 | −1 |
| meta/muse-spark-1.2 | Meta | 8 | 153 | 6 | 3 |
| meituan/longcat-2.0 | AtlasCloud | 15 | 199 | 2 | 3 |
| qwen/qwen3.8-max | Alibaba | 37–49 | 200 | 8 | 4 |
| nvidia/nemotron-3.5-lightning | DeepInfra | 17 | 201 | 7 | 2 |
| xiaomi/mimo-v2.5-pro | StreamLake | 254 | 201 | 0 | 0 |
| bytedance/ui-tars-1.5-7b | Parasail | 20 | 203 | 2 | 3 |
| inclusionai/ling-3.0-flash | Novita | 21 | 204 | 2 | 2 |
| google/gemini-3.7-flash | Google | 1 | 207 | 6 | 3 |
| baidu/ernie-4.5-vl-424b-a47b | Novita | 1 | 208 | 6 | 3 |
| anthropic/claude-fable-5 | Google Vertex | 7 | 237 | 8 | 3 |

Only the GLM family lands on 172.

## 2. GLM-5.2 special tokens are the model's, not the server's

Same probes, provider pinned (`provider.order`, no fallbacks):

| provider | base | passage | `<\|endoftext\|>` | `<think>` | `<\|eot_id\|>` | `<\|im_start\|>` |
|---|--:|--:|--:|--:|--:|--:|
| Z.AI | 13 | 172 | 2 | 2 | 6 | 5 |
| Baidu | 13 | 172 | 2 | 2 | 6 | 5 |
| Sail Research | 13 | 172 | 2 | 2 | 6 | 5 |
| Ambient | 13 | 172 | 2 | 2 | 6 | 5 |

## 3. Extra special tokens, Chinese-lab references vs ox-alpha

| token | ox-alpha | GLM-5.3 | GLM-5.2 | Kimi K3 | Qwen3.8-Max | DeepSeek V4-Pro |
|---|--:|--:|--:|--:|--:|--:|
| `<\|im_user\|>` | 5 | 5 | 5 | 5 | 5 | 6 |
| `<\|im_assistant\|>` | — | — | 6 | 3 | 6 | 86 |
| `<\|im_end\|>` | — | — | 5 | 5 | 7 | 1 |
| `<\|begin_of_text\|>` | 6 | 6 | 6 | 6 | 6 | 7 |
| `<｜begin▁of▁sentence｜>` (DeepSeek BOS) | 11 | 11 | 11 | 13 | 11 | **2** |
| `[EOS]` | — | — | 3 | **0** | 3 | 4 |

## 4. Cold-call cache hits (is the hidden prefix cached?)

`cached_tokens` on the first call of a session, then on an identical second call, ~100-token prompt:

| model | served by | prompt_tokens | cached (call 1 / call 2) |
|---|---|--:|---|
| stealth/ox-alpha | Stealth | 88–92 (bare prompt) | **64** on the very first call |
| x-ai/grok-4.6 | xAI | 211 | **128** on the first call (its own ~200-token prefix) |
| deepseek/deepseek-v4-pro | BaseTen / Baidu | 94 / 93 | 0 / 0 |
| moonshotai/kimi-k3 | DeepInfra | 176 | 0 / 0 |
| qwen/qwen3.8-max | Alibaba | 140 | 0 / 0 |
| z-ai/glm-5.2 | Z.AI | 106 | 0 / 0 |
| google/gemini-3.7-flash | Google | 107 | 0 / 0 |

## 5. OpenRouter endpoint p50s (last 30 min at probe time)

| endpoint | latency p50 (ms) | throughput p50 (tok/s) |
|---|--:|--:|
| stealth/ox-alpha — Stealth | 3280 | 28 |
| z-ai/glm-5.3 — Z.AI | 2154 | 46 |
| z-ai/glm-5.2 — Baidu / Sail Research / Ambient | 1423 / 1649 / 1615 | 28 / 24 / 40.5 |
| moonshotai/kimi-k3 — Sail Research / Morph / DeepInfra | 1071 / 2864 / 849 | 43 / 11 / 20 |
| qwen/qwen3.8-max — Alibaba | 1532 | 44 |
| deepseek/deepseek-v4-pro — Baidu / StreamLake / GMICloud | 1101 / 1344 / 2689 | 46 / 26 / 13 |
| meta/muse-spark-1.2 — Meta | 1260 | 76 |
| openai/gpt-5.6-sol — OpenAI (3 endpoints) | 2414 / 7807 / 3557 | 46 / 36 / 58 |
| x-ai/grok-4.6 — xAI (3 endpoints) | 1099 / 1580 / 1181 | 54 / 56 / 51 |
| anthropic/claude-fable-5 — Azure / Claude Platform on AWS | 5831 / 7219 | 45 / 45 |
| google/gemini-3.7-flash — Google (3 endpoints) | 2117 / 13306 / 2345 | 75 / 30 / 100 |
