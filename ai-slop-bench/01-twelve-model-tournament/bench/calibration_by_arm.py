"""Human calibration split by the model arm each human post was paired with. Writes results/calibration_by_arm.json.

Pairings come from calib.pairings (9 tests per arm, same as judge.py). Each judge
that is not the arm's vendor scores the pairing in both orders (-HM, -MH); a verdict counts when both orders agree.
Usage: python bench/calibration_by_arm.py
"""
import json
from calib import pairings
from panel import ARMS, CFG, HUMAN, JUDGES, N, ROOT, load, verdict


def main():
    V = {j: load(j) for j in JUDGES}
    out = {a: {"human": 0, "model": 0, "flip": 0, "judges": {}, "pairings": 0} for a in ARMS}
    for h, arm, n in pairings(ARMS, HUMAN, N):
        out[arm]["pairings"] += 1
        for j in JUDGES:
            if CFG["judges"][j]["vendor"] == CFG["arms"][arm]["vendor"]:
                continue
            r = verdict(V[j], f"calib-{h}-vs-{arm}-{n}", "human", "model", "-HM", "-MH")
            if r is None:
                continue
            out[arm][r] += 1
            if r != "flip":
                out[arm]["judges"][j] = out[arm]["judges"].get(j, 0) + 1
    (ROOT / "results/calibration_by_arm.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    tot = {k: sum(v[k] for v in out.values()) for k in ("human", "model", "flip")}
    print(json.dumps(out, indent=1))
    print("total:", tot)


if __name__ == "__main__":
    main()
