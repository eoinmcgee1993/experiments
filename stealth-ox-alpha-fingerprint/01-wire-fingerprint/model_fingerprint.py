#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_fingerprint.py — wire-level fingerprint of OpenRouter models, built for stealth releases.

A stealth slug hides the lab, not the wire. What still leaks through OpenRouter's normalization:
  1. TOKENIZER — usage.prompt_tokens on a fixed passage (delta against a 1-char baseline) is a
     family signature (o200k vs Claude vs Gemini vs Qwen vs DeepSeek vs Llama). Special-token
     strings (<|endoftext|>, <|im_start|>, <|begin_of_text|>, ...) collapse to 1 token, get
     rejected, or split into pieces depending on the tokenizer.
  2. TOOL-CALL IDS — call_xxx (OpenAI-style, also Google's OpenAI shim and most OSS servers),
     toolu_xxx (Anthropic), call_<digits> (Google), etc.; argument JSON spacing too.
  3. REASONING SHAPE — reasoning_details types/ids/signatures (OpenAI summaries+encrypted,
     Anthropic signed thinking, Gemini thought signatures, raw text for OSS).
  4. METADATA — system_fingerprint (OpenAI fp_...), native_finish_reason vocabulary, usage
     detail keys, response id/created shape, provider field, OR model card (modality, ctx,
     max_completion, supported_parameters, tokenizer tag).
  5. TIMING — TTFT and tokens/s from a streamed answer, n runs.
  6. BEHAVIOUR — self-identification line, knowledge-cutoff answer, style tells (em dashes,
     markdown headers, bullets) on a fixed prompt.

Every raw response is saved (Temp/data/<out>/<model>/<probe>.json); the summary table is printed
and written as fingerprint.json + README.md next to them. Errors are recorded, not retried — a 400
on a parameter is a finding.

Usage:
  python tools/model_fingerprint.py --models stealth/ox-alpha,openai/gpt-5.6-sol,x-ai/grok-4.6,anthropic/claude-fable-5
  python tools/model_fingerprint.py --models stealth/ox-alpha --skip-timing --reasoning-effort high
Reads OPENROUTER_API_KEY from .env. Stdlib only. Costs cents per model (Fable/Opus-class: tens of cents).
"""
import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
API = "https://openrouter.ai/api/v1"
DEFAULT_MODELS = [
    "stealth/ox-alpha", "openai/gpt-5.6-sol", "x-ai/grok-4.6", "anthropic/claude-fable-5",
    "google/gemini-3.7-flash", "moonshotai/kimi-k3", "qwen/qwen3.8-max",
    "deepseek/deepseek-v4-pro", "meta/muse-spark-1.2", "z-ai/glm-5.2",
]

PASSAGE = (
    "Naïve café résumé — 東京 Zürich straße 🚀 ¿Qué tal? "
    "def fib(n):\n    return n if n < 2 else fib(n-1) + fib(n-2)\n"
    "SELECT COUNT(*) FROM orders WHERE created_at >= '2026-08-24T00:00:00Z';\n"
    "0x7FFFFFFF 3.14159265358979 1,048,576 18446744073709551615 "
    "supercalifragilisticexpialidocious antidisestablishmentarianism "
    "https://openrouter.ai/api/v1/chat/completions?model=stealth%2Fox-alpha "
    "The ¥1,200 invoice (ref. #A-77) was paid on 2026-08-24; thanks!"
)
SPECIAL = ["<|endoftext|>", "<|im_start|>", "<|begin_of_text|>", "<|eot_id|>",
           "<｜begin▁of▁sentence｜>", "<start_of_turn>", "[INST]", "<|startoftext|>",
           "<|reserved_special_token_0|>", "<|fim_prefix|>", "<think>"]
REASONING_PROMPT = ("What is the sum of the first 20 prime numbers? Work it out carefully, "
                    "then answer with just the number.")
IDENTITY_PROMPT = ("In one line: which company trained you, what is your exact model name, "
                   "and what is your knowledge cutoff date?")
STYLE_PROMPT = "Explain in exactly four sentences why a flaky test is worse than a failing test."
STREAM_PROMPT = "Write about 200 words on how prompt caching works in LLM APIs. Plain prose."
TOOL = {"type": "function", "function": {
    "name": "get_weather", "description": "Get the current weather for a city.",
    "parameters": {"type": "object", "properties": {
        "city": {"type": "string"}, "unit": {"type": "string", "enum": ["c", "f"]}},
        "required": ["city"]}}}


def read_key():
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no OPENROUTER_API_KEY in .env")


KEY = None


PACE_S = 1.0


def call(body, timeout=300, stream=False, _attempt=0):
    """POST chat/completions. Returns dict(status, headers, json|text, elapsed, [stream events]).

    429/5xx are retried with backoff (a rate limit is not a fingerprint - the stealth slug
    threw 429s after ~15 quick calls on 2026-08-24 and blanked the tokenizer row); 4xx other
    than 429 are returned as findings. PACE_S sleeps after every call to stay under limits."""
    req = urllib.request.Request(f"{API}/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {KEY}",
                                          "Content-Type": "application/json",
                                          "HTTP-Referer": "https://productcompass.pm",
                                          "X-Title": "model_fingerprint"}, method="POST")
    t0 = time.time()
    time.sleep(PACE_S)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            if not stream:
                raw = resp.read().decode("utf-8", "replace")
                try:
                    data = json.loads(raw)
                except ValueError:
                    data = {"_raw": raw[:2000]}
                return {"status": resp.status, "headers": headers, "json": data,
                        "elapsed": round(time.time() - t0, 3)}
            events, first_any, first_reason, first_content, usage = [], None, None, None, None
            for line in resp:
                s = line.decode("utf-8", "replace").strip()
                if not s.startswith("data:"):
                    continue
                payload = s[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                except ValueError:
                    continue
                now = time.time() - t0
                if first_any is None:
                    first_any = now
                delta = ((chunk.get("choices") or [{}])[0].get("delta") or {})
                if first_reason is None and (delta.get("reasoning") or delta.get("reasoning_details")):
                    first_reason = now
                if first_content is None and delta.get("content"):
                    first_content = now
                if chunk.get("usage"):
                    usage = chunk["usage"]
                if len(events) < 3:
                    events.append(chunk)
            return {"status": resp.status, "headers": headers, "elapsed": round(time.time() - t0, 3),
                    "ttfb": first_any, "ttf_reasoning": first_reason, "ttf_content": first_content,
                    "usage": usage, "first_chunks": events}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            data = json.loads(raw)
        except ValueError:
            data = {"_raw": raw[:2000]}
        # OpenRouter wraps an upstream 429 as HTTP 200 with error.code 429 sometimes, and as a
        # real 429 other times; both land here or below. Back off and retry up to 4 times.
        if e.code in (429, 500, 502, 503) and _attempt < 4:
            time.sleep(5 * (2 ** _attempt))
            return call(body, timeout, stream, _attempt + 1)
        return {"status": e.code, "headers": {k.lower(): v for k, v in e.headers.items()},
                "json": data, "elapsed": round(time.time() - t0, 3)}
    except Exception as e:  # noqa: BLE001
        return {"status": "ERR", "error": str(e)[:300], "elapsed": round(time.time() - t0, 3)}


def prompt_tokens(model, text):
    r = call({"model": model, "max_tokens": 16, "temperature": 0,
              "messages": [{"role": "user", "content": text}]})
    j = r.get("json") or {}
    # a 200 carrying an error object (OpenRouter's upstream-error shape) is a retry case too
    if isinstance(j.get("error"), dict) and j["error"].get("code") in (429, 500, 502, 503):
        for attempt in range(4):
            time.sleep(5 * (2 ** attempt))
            r = call({"model": model, "max_tokens": 16, "temperature": 0,
                      "messages": [{"role": "user", "content": text}]})
            j = r.get("json") or {}
            if not (isinstance(j.get("error"), dict) and j["error"].get("code") in (429, 500, 502, 503)):
                break
    u = j.get("usage") or {}
    return u.get("prompt_tokens"), r


def model_card(model):
    try:
        with urllib.request.urlopen(urllib.request.Request(
                f"{API}/models/{model}/endpoints", headers={"Authorization": f"Bearer {KEY}"}),
                timeout=60) as resp:
            d = json.load(resp)["data"]
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)[:200]}
    ep = (d.get("endpoints") or [{}])[0]
    return {"tokenizer": (d.get("architecture") or {}).get("tokenizer"),
            "modality": (d.get("architecture") or {}).get("modality"),
            "context_length": ep.get("context_length"),
            "max_completion_tokens": ep.get("max_completion_tokens"),
            "provider_name": ep.get("provider_name"), "quantization": ep.get("quantization"),
            "supported_parameters": sorted(ep.get("supported_parameters") or []),
            "pricing": ep.get("pricing"), "implicit_caching": ep.get("supports_implicit_caching"),
            "latency_p50_ms": (ep.get("latency_last_30m") or {}).get("p50"),
            "throughput_p50": (ep.get("throughput_last_30m") or {}).get("p50"),
            "created": d.get("created"), "description": (d.get("description") or "")[:400]}


def style_stats(text):
    return {"chars": len(text), "em_dashes": text.count("—"), "en_dashes": text.count("–"),
            "headers": len(re.findall(r"^#+ ", text, re.M)),
            "bullets": len(re.findall(r"^\s*[-*•] ", text, re.M)),
            "bold": text.count("**") // 2, "sentences": len(re.findall(r"[.!?](\s|$)", text)),
            "first_person": len(re.findall(r"\bI\b", text))}


def fingerprint(model, out_dir, args):
    d = out_dir / model.replace("/", "__")
    d.mkdir(parents=True, exist_ok=True)
    fp = {"model": model, "card": model_card(model)}

    def save(name, obj):
        (d / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")

    # P1 metadata (reasoning models think even on "OK": give them room and ask for low effort)
    r = call({"model": model, "max_tokens": 1200, "temperature": 0, "reasoning": {"effort": "low"},
              "messages": [{"role": "user", "content": "Reply with exactly: OK"}]})
    save("p1_metadata", r)
    j = r.get("json") or {}
    ch = (j.get("choices") or [{}])[0]
    fp["meta"] = {
        "status": r["status"], "provider": j.get("provider"), "model_echo": j.get("model"),
        "id": j.get("id"), "object": j.get("object"), "system_fingerprint": j.get("system_fingerprint"),
        "finish_reason": ch.get("finish_reason"), "native_finish_reason": ch.get("native_finish_reason"),
        "usage_keys": sorted((j.get("usage") or {}).keys()),
        "usage_detail_keys": sorted({f"{k}.{kk}" for k, v in (j.get("usage") or {}).items()
                                     if isinstance(v, dict) for kk in v}),
        "extra_top_keys": sorted(set(j.keys()) - {"id", "object", "created", "model", "choices", "usage",
                                                  "provider", "system_fingerprint"}),
        "message_keys": sorted((ch.get("message") or {}).keys()),
        "content": ((ch.get("message") or {}).get("content") or "")[:80],
        "headers_of_interest": {k: v for k, v in (r.get("headers") or {}).items()
                                if k.startswith("x-") or k in ("server", "via", "cf-ray")},
        "elapsed": r.get("elapsed"),
    }

    # P2 tokenizer
    base, rb = prompt_tokens(model, "x")
    passage, rp = prompt_tokens(model, "x" + PASSAGE)
    tok = {"baseline_x": base, "passage_delta": (passage - base) if (base is not None and passage is not None) else None,
           "specials": {}}
    for s in SPECIAL:
        n, rs = prompt_tokens(model, "x " + s)
        err = None
        if n is None:
            err = str((rs.get("json") or {}).get("error") or rs.get("error") or rs.get("status"))[:120]
        tok["specials"][s] = {"delta": (n - base) if (n is not None and base is not None) else None, "error": err}
    fp["tokenizer"] = tok
    save("p2_tokenizer", {"baseline": rb, "passage": rp, "tok": tok})

    # P3 reasoning shape
    r = call({"model": model, "max_tokens": 6000, "temperature": 0,
              "reasoning": {"effort": args.reasoning_effort}, "include_reasoning": True,
              "messages": [{"role": "user", "content": REASONING_PROMPT}]})
    save("p3_reasoning", r)
    j = r.get("json") or {}
    msg = ((j.get("choices") or [{}])[0].get("message") or {})
    details = msg.get("reasoning_details") or []
    fp["reasoning"] = {
        "status": r["status"], "answer": (msg.get("content") or "")[:60].replace("\n", " "),
        "reasoning_len": len(msg.get("reasoning") or ""),
        "reasoning_tokens": ((j.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "details_types": sorted({x.get("type") for x in details if isinstance(x, dict)}),
        "details_formats": sorted({str(x.get("format")) for x in details if isinstance(x, dict)}),
        "details_n": len(details),
        "details_id_sample": next((x.get("id") for x in details if isinstance(x, dict) and x.get("id")), None),
        "has_signature": any(isinstance(x, dict) and x.get("signature") for x in details),
        "reasoning_head": (msg.get("reasoning") or "")[:160].replace("\n", " "),
        "error": str((j.get("error") or ""))[:160] if j.get("error") else None,
        "elapsed": r.get("elapsed"),
    }

    # P4 tool call
    r = call({"model": model, "max_tokens": 400, "temperature": 0, "tools": [TOOL],
              "tool_choice": "auto",
              "messages": [{"role": "user", "content": "What's the weather in Warsaw in celsius? Use the tool."}]})
    save("p4_tool", r)
    j = r.get("json") or {}
    msg = ((j.get("choices") or [{}])[0].get("message") or {})
    tcs = msg.get("tool_calls") or []
    tc = tcs[0] if tcs else {}
    fp["tool"] = {
        "status": r["status"], "n_calls": len(tcs), "id": tc.get("id"),
        "id_shape": re.sub(r"[A-Za-z0-9]", lambda m: "9" if m.group().isdigit() else ("a" if m.group().islower() else "A"), tc.get("id") or ""),
        "arguments": ((tc.get("function") or {}).get("arguments") or "")[:120],
        "extra_keys": sorted(set(tc.keys()) - {"id", "type", "function", "index"}),
        "finish_reason": ((j.get("choices") or [{}])[0]).get("finish_reason"),
        "native_finish_reason": ((j.get("choices") or [{}])[0]).get("native_finish_reason"),
        "content_alongside": bool(msg.get("content")),
        "error": str((j.get("error") or ""))[:160] if j.get("error") else None,
    }

    # P5 timing (streamed)
    if not args.skip_timing:
        runs = []
        for _ in range(args.timing_runs):
            # low effort + room: reasoning models spent all 600 tokens thinking and never
            # streamed content (Kimi/Qwen 2026-08-24), which left ttf_content None
            r = call({"model": model, "max_tokens": 1500, "temperature": 0, "stream": True,
                      "usage": {"include": True}, "reasoning": {"effort": "low"},
                      "messages": [{"role": "user", "content": STREAM_PROMPT}]}, stream=True)
            u = r.get("usage") or {}
            ct = u.get("completion_tokens")
            gen = (r.get("elapsed") or 0) - (r.get("ttf_content") or r.get("ttfb") or 0)
            runs.append({"ttfb": r.get("ttfb"), "ttf_reasoning": r.get("ttf_reasoning"),
                         "ttf_content": r.get("ttf_content"), "total": r.get("elapsed"),
                         "completion_tokens": ct,
                         "tok_per_s": round(ct / gen, 1) if (ct and gen and gen > 0) else None,
                         "status": r.get("status")})
        save("p5_timing", runs)
        ttfs = sorted(x["ttf_content"] for x in runs if x.get("ttf_content") is not None)
        tps = sorted(x["tok_per_s"] for x in runs if x.get("tok_per_s"))
        fp["timing"] = {"runs": runs,
                        "ttf_content_median": ttfs[len(ttfs) // 2] if ttfs else None,
                        "tok_per_s_median": tps[len(tps) // 2] if tps else None}

    # P6 behaviour
    r = call({"model": model, "max_tokens": 1500, "temperature": 0, "reasoning": {"effort": "low"},
              "messages": [{"role": "user", "content": IDENTITY_PROMPT}]})
    save("p6_identity", r)
    ident = (((r.get("json") or {}).get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    r2 = call({"model": model, "max_tokens": 2000, "temperature": 0, "reasoning": {"effort": "low"},
               "messages": [{"role": "user", "content": STYLE_PROMPT}]})
    save("p6_style", r2)
    style_text = (((r2.get("json") or {}).get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    r3 = call({"model": model, "max_tokens": 16, "temperature": 0, "logprobs": True, "top_logprobs": 2,
               "messages": [{"role": "user", "content": "Say hi"}]})
    save("p6_logprobs", r3)
    j3 = r3.get("json") or {}
    fp["behaviour"] = {
        "identity": ident.strip().replace("\n", " ")[:220],
        "style": style_stats(style_text), "style_head": style_text[:140].replace("\n", " "),
        "logprobs": ("returned" if (((j3.get("choices") or [{}])[0]).get("logprobs")) else
                     ("error:" + str(j3.get("error") or "")[:80] if j3.get("error") else "ignored")),
    }
    (d / "fingerprint.json").write_text(json.dumps(fp, indent=1, ensure_ascii=False), encoding="utf-8")
    return fp


def main():
    global KEY
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS))
    ap.add_argument("--out", default="Temp/data/model-fingerprint")
    ap.add_argument("--reasoning-effort", default="medium")
    ap.add_argument("--skip-timing", action="store_true")
    ap.add_argument("--timing-runs", type=int, default=2)
    ap.add_argument("--pace", type=float, default=1.0, help="seconds to sleep after every call")
    args = ap.parse_args()
    KEY = read_key()
    global PACE_S
    PACE_S = args.pace
    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for model in [m.strip() for m in args.models.split(",") if m.strip()]:
        t0 = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] {model} ...", flush=True)
        try:
            fp = fingerprint(model, out_dir, args)
        except Exception as e:  # noqa: BLE001
            fp = {"model": model, "error": str(e)[:300]}
        results.append(fp)
        print(f"   done in {time.time() - t0:.0f}s", flush=True)
    (out_dir / "fingerprint.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")

    # summary table
    rows = []
    for fp in results:
        if "error" in fp and "meta" not in fp:
            rows.append(f"| {fp['model']} | ERROR {fp['error'][:60]} |")
            continue
        c, m, t, rz, tl, b = fp["card"], fp["meta"], fp["tokenizer"], fp["reasoning"], fp["tool"], fp["behaviour"]
        sp = {k: v["delta"] if v["delta"] is not None else ("ERR" if v["error"] else "?") for k, v in t["specials"].items()}
        tm = fp.get("timing") or {}
        rows.append("| " + " | ".join(str(x) for x in [
            fp["model"], c.get("tokenizer"), c.get("modality"), c.get("context_length"), c.get("max_completion_tokens"),
            m.get("provider"), m.get("system_fingerprint"), m.get("native_finish_reason"),
            t.get("passage_delta"), sp.get("<|endoftext|>"), sp.get("<|im_start|>"), sp.get("<|begin_of_text|>"),
            sp.get("<｜begin▁of▁sentence｜>"), sp.get("<start_of_turn>"), sp.get("<think>"),
            rz.get("details_types"), rz.get("details_formats"), rz.get("has_signature"), rz.get("reasoning_tokens"),
            tl.get("id_shape"), tl.get("arguments"),
            tm.get("ttf_content_median"), tm.get("tok_per_s_median"),
            b.get("logprobs"), b["style"].get("em_dashes"), b["style"].get("headers"), b["style"].get("bullets"),
            b.get("identity")[:120],
        ]) + " |")
    header = ("| model | OR tokenizer | modality | ctx | max_out | provider | system_fingerprint | native_finish | "
              "passage Δtok | <\\|endoftext\\|> | <\\|im_start\\|> | <\\|begin_of_text\\|> | DeepSeek BOS | "
              "<start_of_turn> | <think> | reasoning types | formats | signed | reasoning_tok | tool id shape | "
              "tool args | TTF content s | tok/s | logprobs | em— | # | bullets | identity |")
    sep = "|" + "---|" * (header.count("|") - 1)
    table = "\n".join([header, sep, *rows])
    (out_dir / "README.md").write_text(
        f"# model_fingerprint — {time.strftime('%Y-%m-%d %H:%M')}\n\nPassage: {len(PASSAGE)} chars. "
        f"Specials Δ = prompt_tokens('x '+token) - prompt_tokens('x'). Reasoning effort: {args.reasoning_effort}.\n\n"
        + table + "\n", encoding="utf-8")
    print("\n" + table)
    print(f"\nraw + summary: {out_dir}")


if __name__ == "__main__":
    main()
