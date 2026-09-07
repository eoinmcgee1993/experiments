"""Raw API transports. One call = one essay or one verdict. No system prompt is ever sent.

Every function returns (text, raw_response_json, request_body). The request body is the model's ENTIRE
context, so it is filed as the receipt. Keys come from environment variables only and are never written
anywhere. HTTP 4xx is never retried (a rejection is a finding); transport failures and 429/5xx are retried.
"""
import json, os, time, urllib.request, urllib.error

RETRIES = 3


def _key(var):
    v = os.environ.get(var, "").strip()
    if not v:
        raise SystemExit(f"{var} is not set in the environment")
    return v


def _post(url, body, headers, timeout):
    data = json.dumps(body).encode()
    last = None
    for attempt in range(RETRIES):
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"Content-Type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:400]
            if e.code in (429, 500, 502, 503, 504) and attempt < RETRIES - 1:
                time.sleep(8 * (attempt + 1)); last = f"HTTP {e.code} {msg}"; continue
            raise RuntimeError(f"HTTP {e.code} {msg}")
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            last = repr(e)
            if attempt < RETRIES - 1:
                time.sleep(8 * (attempt + 1)); continue
            raise RuntimeError(f"transport: {last}")
    raise RuntimeError(f"transport: {last}")


def openai_responses(model, prompt, max_tokens=8000, timeout=600, effort=None, **_):
    body = {"model": model, "input": prompt, "max_output_tokens": max_tokens, "store": False}
    if effort:
        body["reasoning"] = {"effort": effort}
    d = _post("https://api.openai.com/v1/responses", body,
              {"Authorization": "Bearer " + _key("OPENAI_API_KEY")}, timeout)
    text = "".join(c.get("text", "") for it in d.get("output", []) if it.get("type") == "message"
                   for c in it.get("content", []) if c.get("type") == "output_text")
    return text, d, body


def openrouter(model, prompt, max_tokens=8000, timeout=600, **_):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens,
            "provider": {"allow_fallbacks": False}, "usage": {"include": True}}
    d = _post("https://openrouter.ai/api/v1/chat/completions", body,
              {"Authorization": "Bearer " + _key("OPENROUTER_API_KEY")}, timeout)
    text = d["choices"][0]["message"].get("content") or ""
    return text, d, body


def xai_chat(model, prompt, max_tokens=8000, timeout=300, **_):
    """Streams (SSE). Measured 2026-09-07: 2 of 6 concurrent judge-sized non-streaming grok-4.6 calls never
    returned and sat on the 600 s read timeout, which starved the judge (3 verdicts/min at 50 workers). With a
    stream the connection carries bytes while the model works and a true stall fails fast and is retried.
    `timeout` is the idle gap between chunks. The raw receipt is rebuilt in chat-completion shape from the
    chunks (content, finish_reason, usage from the final chunk) and flagged "streamed": true."""
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens,
            "stream": True, "stream_options": {"include_usage": True}}
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + _key("XAI_API_KEY")}
    last = None
    for attempt in range(RETRIES):
        req = urllib.request.Request("https://api.x.ai/v1/chat/completions", data=json.dumps(body).encode(),
                                     method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                parts, usage, meta, finish = [], None, {}, None
                for raw_line in r:
                    line = raw_line.decode("utf-8", "replace").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    ch = json.loads(data)
                    meta = {k: ch.get(k) for k in ("id", "model", "created", "system_fingerprint") if k in ch}
                    for c in ch.get("choices") or []:
                        delta = (c.get("delta") or {}).get("content")
                        if delta:
                            parts.append(delta)
                        finish = c.get("finish_reason") or finish
                    if ch.get("usage"):
                        usage = ch["usage"]
            text = "".join(parts)
            d = {**meta, "object": "chat.completion", "streamed": True, "usage": usage,
                 "choices": [{"index": 0, "finish_reason": finish,
                              "message": {"role": "assistant", "content": text}}]}
            return text, d, body
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:400]
            if e.code in (429, 500, 502, 503, 504) and attempt < RETRIES - 1:
                time.sleep(8 * (attempt + 1)); last = f"HTTP {e.code} {msg}"; continue
            raise RuntimeError(f"HTTP {e.code} {msg}")
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, ValueError) as e:
            last = repr(e)
            if attempt < RETRIES - 1:
                time.sleep(8 * (attempt + 1)); continue
            raise RuntimeError(f"transport: {last}")
    raise RuntimeError(f"transport: {last}")


def google(model, prompt, max_tokens=8000, timeout=600, json_mode=False, thinking="high", **_):
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens}}
    if thinking:
        body["generationConfig"]["thinkingConfig"] = {"thinkingLevel": thinking}
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key="
           + _key("GEMINI_API_KEY"))
    d = _post(url, body, {}, timeout)
    parts = d["candidates"][0]["content"].get("parts", [])
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    return text, d, body


TRANSPORTS = {"openai_responses": openai_responses, "openrouter": openrouter, "xai_chat": xai_chat,
              "google": google}


def usage_summary(transport, d):
    """Normalise token usage so receipts are comparable across vendors."""
    u = d.get("usage") or d.get("usageMetadata") or {}
    if transport == "openai_responses":
        return {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
                "reasoning_tokens": (u.get("output_tokens_details") or {}).get("reasoning_tokens"),
                "effort_echoed": (d.get("reasoning") or {}).get("effort"), "served_model": d.get("model")}
    if transport in ("openrouter", "xai_chat"):
        return {"input_tokens": u.get("prompt_tokens"), "output_tokens": u.get("completion_tokens"),
                "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                "cost_usd": u.get("cost"), "served_model": d.get("model"), "provider": d.get("provider")}
    if transport == "google":
        return {"input_tokens": u.get("promptTokenCount"), "output_tokens": u.get("candidatesTokenCount"),
                "reasoning_tokens": u.get("thoughtsTokenCount"), "served_model": d.get("modelVersion")}
    return u
