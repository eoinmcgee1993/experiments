# 02 — Five attempts to run: what day-one access actually cost

## Question

The model was announced hours before anyone in the West could meter it. Separately from *how good is it*: what did it take to get one clean benchmark run on launch day?

## Method

Three access paths were tried, all through the same Anthropic-API proxy shim ([harness/kimi_proxy2.py](harness/kimi_proxy2.py)) on port 8792:

1. **OpenRouter** — a poller ([harness/poll_qwen38_20260803.py](harness/poll_qwen38_20260803.py)) checked the public models list every 15 min, ready to fire the chain ([harness/run_qwen38max_20260803.py](harness/run_qwen38max_20260803.py)) the moment a slug appeared.
2. **Alibaba "token-plan" subscription endpoint** — a Claude-Code-style coding plan with a 5-hour rolling quota.
3. **Alibaba pay-as-you-go international endpoint** — the chain's `--fallback-api-root` escape hatch.

Raw receipts: [run-gbvb.log](run-gbvb.log), [run-abhb.log](run-abhb.log) (per-leg prepare/start/DONE), [proxy-8792.log](proxy-8792.log) (the throttle and failover tracebacks), [poll.log](poll.log), and the VOID rows in [../01-two-repo-bug-hunt/metrics_qwen.csv](../01-two-repo-bug-hunt/metrics_qwen.csv). Timestamps in the logs are local CEST (UTC+2).

## Results

| Local time (CEST) | Event | Outcome |
|---|---|---|
| 07:59 | Poller starts watching OpenRouter | Never fires — the model was still unlisted when the bench finished 11h later (and, per the source post, ~20h after the announcement) |
| 09:02 | **Attempt 1** — first chain launch | Aborted before any tokens: the proxy liveness probe round-tripped the upstream, the maas host answered slower than the timeout, and the retry double-bound the port. Probe rewritten to a local socket connect ([harness/run_qwen38max_20260803.py](harness/run_qwen38max_20260803.py), `proxy_alive`) |
| 09:10–09:14 | **Attempt 2** — both repo legs concurrent on the token-plan endpoint | Two concurrent agents exhausted the **5-hour quota in ~60 min**; legs died in 429 loops, killed before the runner wrote rows. Throttle message: "resets at 08-03 11:58:00 UTC" |
| 14:00 | **Attempt 3** — relauncher ([harness/relaunch_qwen38max_at_reset.py](harness/relaunch_qwen38max_at_reset.py)) fires after the advertised reset, sequential this time | gbvb leg dies again at 14:47 after 36.6 min back in the 429 loop — ~$4.22 of quota-equivalent tokens burned. VOID row 1 |
| 14:46–14:56 | **Attempt 4** — chain killed, proxy hot-swapped to the pay-as-you-go endpoint, same session resumed | Dead in 182.7s: the resumed Claude-harness session replays signed thinking blocks, and the second gateway **404s the replayed signatures**. VOID row 2, $0.00 |
| 15:12 | **Attempt 5** — fresh session on pay-as-you-go | Dead in 354.8s: the key's **free tier ran dry mid-run and the account refused paid billing (403)** until billing was activated in a separate console. VOID row 3, $0.67 |
| 17:36–17:40 | Billing live — both legs relaunched fresh, concurrent | **Both clean**: gbvb 66.5 min (18:43), abhb 81.7 min (19:01). Judged same evening ([harness/finish_qwen38max_20260803.py](harness/finish_qwen38max_20260803.py)) |

Total: ~$31.10 in pay-as-you-go token-estimate for the clean legs, plus one burned 5-hour subscription window and the void legs, across ~10 hours of clock for ~148 model-minutes.

## Findings

1. **A day-one benchmark measures the serving stack as much as the model.** Same lesson as Kimi K3's launch ([kimi-k3-day-one/02](../../kimi-k3-day-one/02-day-one-capacity/)), different failure surface: K3's was queue depth; Qwen's was quota design, gateway compatibility, and billing state.
2. **Subscription coding-plan quotas are sized for one interactive human, not agents.** Two concurrent agentic legs ate the 5-hour window in about an hour — and after the advertised reset, even a single sequential leg died back in the 429 loop 36 minutes in.
3. **"Anthropic-compatible" endpoints are not interchangeable mid-session.** A resumed Claude-harness session replays signed thinking blocks; the second host rejects the foreign signatures with 404s. Failover between gateways means a fresh session, always — pick your endpoint before the run.
4. **There is a shadow wall between free tier and paid.** The pay-as-you-go key didn't degrade gracefully when its free allocation ran out mid-run; it hard-403'd until billing was switched on in a different console. Model capability was never the blocker — account state was.
5. **The meter you can't cross-check is a caveat, not a number.** With no OpenRouter listing there was no credits-delta to verify the token-estimate against; every dollar figure in this set carries that asterisk.

## Caveats

- Timestamps are local CEST (UTC+2); the quota reset "11:58 UTC" is 13:58 local, and the relauncher fired at 14:00 local by design.
- One CSV note mislabels VOID row 1 as "09:xx" — per the run log, that leg ran 14:11–14:47. Where the CSV note and the log disagree, the log wins.
- The 09:10 concurrent legs were killed before the runner wrote CSV rows; their quota burn is visible only in the throttle behavior, not as a dollar figure.
- Single account, single region, single day. **This experiment expires** — it describes Alibaba's serving on Aug 3, 2026, and that is the finding, not a flaw.
