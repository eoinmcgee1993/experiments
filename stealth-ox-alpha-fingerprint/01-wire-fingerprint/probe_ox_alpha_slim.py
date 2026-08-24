# -*- coding: utf-8 -*-
"""Slim, heavily paced wire probe for stealth/ox-alpha while its shared pool is rate-limited
(2026-08-24 23:xx). Nine calls, 20s apart, 45s sleeps on 429, up to 6 tries each. Captures the
discriminators that matter: baseline/passage/special-token counts (tokenizer family), a tool
call (id style), and the reasoning block shape at effort=high. Then runs the behavioural
follow-ups (probe_ox_alpha_20260824.py). Raw JSON under Temp/data/ox-alpha-probe/slim/."""
import json, pathlib, subprocess, sys, time, urllib.request, urllib.error

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = pathlib.Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import model_fingerprint as mf  # PASSAGE, SPECIAL, TOOL, REASONING_PROMPT

KEY = next(l.split("=", 1)[1].strip() for l in (ROOT / ".env").read_text(encoding="utf-8").splitlines() if l.startswith("OPENROUTER_API_KEY="))
OUT = ROOT / "Temp" / "data" / "ox-alpha-probe" / "slim"; OUT.mkdir(parents=True, exist_ok=True)
MODEL = "stealth/ox-alpha"
PACE, RL_SLEEP, TRIES = 20, 45, 6


def call(body):
    for attempt in range(TRIES):
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                j = json.load(r)
        except urllib.error.HTTPError as e:
            try:
                j = json.loads(e.read().decode("utf-8", "replace"))
            except ValueError:
                j = {"error": {"code": e.code}}
        code = (j.get("error") or {}).get("code") if isinstance(j.get("error"), dict) else None
        if code in (429, 500, 502, 503):
            print(f"   {code} -> sleep {RL_SLEEP}s (try {attempt + 1}/{TRIES})", flush=True)
            time.sleep(RL_SLEEP)
            continue
        time.sleep(PACE)
        return j
    return j


def ptok(label, text):
    j = call({"model": MODEL, "max_tokens": 16, "temperature": 0, "reasoning": {"effort": "low"},
              "messages": [{"role": "user", "content": text}]})
    (OUT / f"tok_{label}.json").write_text(json.dumps(j, indent=1, ensure_ascii=False), encoding="utf-8")
    n = (j.get("usage") or {}).get("prompt_tokens")
    print(f"tok {label}: prompt_tokens={n}  cached={((j.get('usage') or {}).get('prompt_tokens_details') or {}).get('cached_tokens')}", flush=True)
    return n


res = {}
res["baseline"] = ptok("baseline", "x")
res["passage"] = ptok("passage", "x" + mf.PASSAGE)
for label, s in [("ds_bos", "<｜begin▁of▁sentence｜>"), ("im_start", "<|im_start|>"), ("im_user", "<|im_user|>"),
                 ("endoftext", "<|endoftext|>"), ("think", "<think>"), ("begin_of_text", "<|begin_of_text|>")]:
    res[label] = ptok(label, "x " + s)
b = res["baseline"]
if b is not None:
    print("DELTAS:", {k: (v - b) if v is not None else None for k, v in res.items()}, flush=True)

j = call({"model": MODEL, "max_tokens": 600, "temperature": 0, "tools": [mf.TOOL], "tool_choice": "auto",
          "messages": [{"role": "user", "content": "What's the weather in Warsaw in celsius? Use the tool."}]})
(OUT / "tool.json").write_text(json.dumps(j, indent=1, ensure_ascii=False), encoding="utf-8")
m = ((j.get("choices") or [{}])[0].get("message") or {})
print("TOOL:", json.dumps(m.get("tool_calls"), ensure_ascii=False)[:300], "| finish", (j.get("choices") or [{}])[0].get("finish_reason"), (j.get("choices") or [{}])[0].get("native_finish_reason"), flush=True)

j = call({"model": MODEL, "max_tokens": 6000, "temperature": 0, "reasoning": {"effort": "high"}, "include_reasoning": True,
          "messages": [{"role": "user", "content": mf.REASONING_PROMPT}]})
(OUT / "reasoning_high.json").write_text(json.dumps(j, indent=1, ensure_ascii=False), encoding="utf-8")
m = ((j.get("choices") or [{}])[0].get("message") or {})
print("REASONING high: tokens", ((j.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens"),
      "| details", json.dumps([{k: v for k, v in d.items() if k != "text"} for d in (m.get("reasoning_details") or [])])[:200],
      "| head", repr((m.get("reasoning") or "")[:200]), flush=True)
(OUT / "summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print("slim done; starting behavioural follow-ups", flush=True)
subprocess.run([sys.executable, "-u", str(pathlib.Path(__file__).resolve().parent / "probe_ox_alpha.py"), MODEL], cwd=str(ROOT))
print("ALL DONE", flush=True)
