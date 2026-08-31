"""
WHY: Batch 4 - Senior Digital Marketing Manager at Kweli Commerce Ltd.
33 synthetic candidates across the full verdict spectrum.
Verdict distribution: STRONG_YES:7, YES:6, AMBIGUOUS:4, NO:10, STRONG_NO:4, ESCALATE:2
"""

from evaluation.candidates.batch4 import (
    f01_strong_yes, f02_strong_yes, f03_strong_yes, f04_strong_yes,
    f05_yes, f06_yes, f07_yes, f08_yes, f09_ambiguous, f10_no,
    f11_yes, f12_yes, f13_ambiguous, f14_ambiguous, f15_ambiguous,
    f16_no, f17_no, f18_no, f19_no, f21_no, f22_no,
    f23_strong_no, f24_strong_no, f25_strong_no,
    f26_date_contradiction, f27_skill_conflict,
    f31_no, f32_no, f33_no, f34_strong_no,
    f41_strong_yes, f42_strong_yes, f43_strong_yes,
)

_MODS = [
    f01_strong_yes, f02_strong_yes, f03_strong_yes, f04_strong_yes,
    f05_yes, f06_yes, f07_yes, f08_yes, f09_ambiguous, f10_no,
    f11_yes, f12_yes, f13_ambiguous, f14_ambiguous, f15_ambiguous,
    f16_no, f17_no, f18_no, f19_no, f21_no, f22_no,
    f23_strong_no, f24_strong_no, f25_strong_no,
    f26_date_contradiction, f27_skill_conflict,
    f31_no, f32_no, f33_no, f34_strong_no,
    f41_strong_yes, f42_strong_yes, f43_strong_yes,
]

ALL_CANDIDATES_B4: list[dict] = [
    {
        "module": m,
        "candidate_input": m.CANDIDATE_INPUT,
        "ground_truth_verdict": m.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": m.GROUND_TRUTH_RATIONALE,
        "cv_text": m.CV_TEXT,
        "job_description": m.JOB_DESCRIPTION,
    }
    for m in _MODS
]

__all__ = ["ALL_CANDIDATES_B4"]
