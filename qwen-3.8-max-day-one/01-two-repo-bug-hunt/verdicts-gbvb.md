# Accredia Bug Hunt Bench — blind-judge verdicts

Diff = ground truth; reports are intent evidence only. Judges received anonymized
candidate packets. `fixed_equivalent = fixed_match + 0.5 × fixed_partial`; extras do not increase the planted score.

| Arm | Judge | Status | Match | Partial | Claimed only | Missed | Fixed eq. | Fixed % | Genuine extras |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.8-Max | codex | scored | 5 | 0 | 0 | 40 | 5.0 | 11.11% | 3 |

## Qwen3.8-Max (R1, judged by codex)

- `fixed_match`: E3, G1, G3, H1, J9
- `fixed_partial`: none
- `claimed_only`: none
- `missed`: A1, A2, A3, A4, A5, A6, B1, B2, B3, B4, B5, C1, C2, C3, D1, D2, D3, E1, E2, F1, F2, F3, F4, G2, G4, G5, H2, H3, I1, I2, J1, J2, J3, J4, J5, J6, J7, J8, J10, J11

Extras:
- `EXTRA_GENUINE` — Host-side promptComplete metadata now strips totalTokens: 0 so /compact or /session-info zero reports do not reset the context donut.
- `EXTRA_GENUINE` — Permission-card diff subtitles now count an empty old or new text region as zero lines, fixing new-file create subtitles like 0 -> N.
- `EXTRA_GENUINE` — Inline file-reference detection now preserves Windows drive colons and C#/F# path components by stripping only trailing line anchors.
