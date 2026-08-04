# Accredia Bug Hunt Bench — blind-judge verdicts

Diff = ground truth; reports are intent evidence only. Judges received anonymized
candidate packets. `fixed_equivalent = fixed_match + 0.5 × fixed_partial`; extras do not increase the planted score.

| Arm | Judge | Status | Match | Partial | Claimed only | Missed | Fixed eq. | Fixed % | Genuine extras |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.8-Max | codex | scored | 14 | 0 | 1 | 45 | 14.0 | 23.33% | 3 |

## Qwen3.8-Max (R1, judged by codex)

- `fixed_match`: P006, P020, P033, P041, P063, P096, P097, P099, P022, P035, P046, P005, P030, P034
- `fixed_partial`: none
- `claimed_only`: P079
- `missed`: P001, P010, P023, P027, P044, P056, P066, P086, P095, P002, P003, P009, P013, P014, P016, P057, P061, P064, P082, P083, P104, P004, P012, P036, P050, P073, P102, P007, P028, P031, P037, P038, P074, P080, P103, P008, P025, P072, P091, P094, P032, P039, P109, P114, P116

Extras:
- `EXTRA_GENUINE` — [description withheld — real (non-planted) defect in Accredia's code; we publish counts and verdicts, never the app's code or bugs]
- `EXTRA_GENUINE` — [description withheld — real (non-planted) defect in Accredia's code; we publish counts and verdicts, never the app's code or bugs]
- `EXTRA_GENUINE` — [description withheld — real (non-planted) defect in Accredia's code; we publish counts and verdicts, never the app's code or bugs]
