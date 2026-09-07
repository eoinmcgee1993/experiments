"""The human calibration design, shared by judge.py, panel.py, report.py and calibration_by_arm.py.

Every model arm gets TESTS_PER_ARM tests against the human control posts, the same count as a model-vs-model
pair (3 tasks x 3 samples = 9). Arm k, test t pairs human post (TESTS_PER_ARM * k + t) % len(human) with the
arm's LinkedIn sample t % samples + 1, so each arm sees 9 distinct human posts, each of its 3 LinkedIn samples
is used 3 times, and every human post is used 7 or 8 times across the 12 arms. Receipt keys are
calib-[<variant>-]<human stem>-vs-<arm>-<n>-{HM,MH}, unchanged from the first design (one post per arm), so
receipts that match are reused.
"""
TESTS_PER_ARM = 9


def pairings(arms, human, samples, tests_per_arm=TESTS_PER_ARM):
    """List of (human stem, arm, sample index) in run order."""
    out = []
    for k, arm in enumerate(arms):
        for t in range(tests_per_arm):
            out.append((human[(tests_per_arm * k + t) % len(human)], arm, t % samples + 1))
    return out
