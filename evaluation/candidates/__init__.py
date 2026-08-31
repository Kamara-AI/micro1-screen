"""
WHY: Centralises all 10 test candidates in one importable list so the runner
can iterate over them without knowing their individual module names. Adding a
new candidate means adding one import and one list entry — nothing else changes.

HOW: Each candidate module exports CANDIDATE_INPUT (ScreeningInput),
GROUND_TRUTH_VERDICT (str), GROUND_TRUTH_RATIONALE (str), CV_TEXT (str),
and JOB_DESCRIPTION (str). We re-export all of them here as structured dicts
so the runner has everything it needs in one place.
"""

from evaluation.candidates import (
    c01_strong_yes,
    c02_strong_no,
    c03_date_contradiction,
    c04_skill_conflict,
    c05_non_linear_path,
    c06_builder_signal,
    c07_weak_looks_strong,
    c08_strong_looks_weak,
    c09_incomplete_cv,
    c10_employment_gap,
)

# WHY: Structured list rather than a flat list of inputs — the runner needs
# ground truth alongside each input to compute accuracy metrics. Keeping them
# together prevents the index-alignment bugs that plague parallel lists.
ALL_CANDIDATES: list[dict] = [
    {
        "module": c01_strong_yes,
        "candidate_input": c01_strong_yes.CANDIDATE_INPUT,
        "ground_truth_verdict": c01_strong_yes.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": c01_strong_yes.GROUND_TRUTH_RATIONALE,
        "cv_text": c01_strong_yes.CV_TEXT,
        "job_description": c01_strong_yes.JOB_DESCRIPTION,
    },
    {
        "module": c02_strong_no,
        "candidate_input": c02_strong_no.CANDIDATE_INPUT,
        "ground_truth_verdict": c02_strong_no.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": c02_strong_no.GROUND_TRUTH_RATIONALE,
        "cv_text": c02_strong_no.CV_TEXT,
        "job_description": c02_strong_no.JOB_DESCRIPTION,
    },
    {
        "module": c03_date_contradiction,
        "candidate_input": c03_date_contradiction.CANDIDATE_INPUT,
        "ground_truth_verdict": c03_date_contradiction.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": c03_date_contradiction.GROUND_TRUTH_RATIONALE,
        "cv_text": c03_date_contradiction.CV_TEXT,
        "job_description": c03_date_contradiction.JOB_DESCRIPTION,
    },
    {
        "module": c04_skill_conflict,
        "candidate_input": c04_skill_conflict.CANDIDATE_INPUT,
        "ground_truth_verdict": c04_skill_conflict.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": c04_skill_conflict.GROUND_TRUTH_RATIONALE,
        "cv_text": c04_skill_conflict.CV_TEXT,
        "job_description": c04_skill_conflict.JOB_DESCRIPTION,
    },
    {
        "module": c05_non_linear_path,
        "candidate_input": c05_non_linear_path.CANDIDATE_INPUT,
        "ground_truth_verdict": c05_non_linear_path.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": c05_non_linear_path.GROUND_TRUTH_RATIONALE,
        "cv_text": c05_non_linear_path.CV_TEXT,
        "job_description": c05_non_linear_path.JOB_DESCRIPTION,
    },
    {
        "module": c06_builder_signal,
        "candidate_input": c06_builder_signal.CANDIDATE_INPUT,
        "ground_truth_verdict": c06_builder_signal.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": c06_builder_signal.GROUND_TRUTH_RATIONALE,
        "cv_text": c06_builder_signal.CV_TEXT,
        "job_description": c06_builder_signal.JOB_DESCRIPTION,
    },
    {
        "module": c07_weak_looks_strong,
        "candidate_input": c07_weak_looks_strong.CANDIDATE_INPUT,
        "ground_truth_verdict": c07_weak_looks_strong.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": c07_weak_looks_strong.GROUND_TRUTH_RATIONALE,
        "cv_text": c07_weak_looks_strong.CV_TEXT,
        "job_description": c07_weak_looks_strong.JOB_DESCRIPTION,
    },
    {
        "module": c08_strong_looks_weak,
        "candidate_input": c08_strong_looks_weak.CANDIDATE_INPUT,
        "ground_truth_verdict": c08_strong_looks_weak.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": c08_strong_looks_weak.GROUND_TRUTH_RATIONALE,
        "cv_text": c08_strong_looks_weak.CV_TEXT,
        "job_description": c08_strong_looks_weak.JOB_DESCRIPTION,
    },
    {
        "module": c09_incomplete_cv,
        "candidate_input": c09_incomplete_cv.CANDIDATE_INPUT,
        "ground_truth_verdict": c09_incomplete_cv.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": c09_incomplete_cv.GROUND_TRUTH_RATIONALE,
        "cv_text": c09_incomplete_cv.CV_TEXT,
        "job_description": c09_incomplete_cv.JOB_DESCRIPTION,
    },
    {
        "module": c10_employment_gap,
        "candidate_input": c10_employment_gap.CANDIDATE_INPUT,
        "ground_truth_verdict": c10_employment_gap.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": c10_employment_gap.GROUND_TRUTH_RATIONALE,
        "cv_text": c10_employment_gap.CV_TEXT,
        "job_description": c10_employment_gap.JOB_DESCRIPTION,
    },
]

__all__ = ["ALL_CANDIDATES"]
