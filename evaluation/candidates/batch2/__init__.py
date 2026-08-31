"""
WHY: Batch 2 — Senior Data Scientist at PesaWise (Kenyan fintech, credit risk ML).
A second independent evaluation set to measure SCREEN's generalisation beyond the
original engineering JD and to gather consistency data across 5 runs.

HOW: Same structure as the root candidates/__init__.py — exports ALL_CANDIDATES_B2
as a structured list of dicts.
"""

from evaluation.candidates.batch2 import (
    d01_strong_yes,
    d02_strong_no,
    d03_date_contradiction,
    d04_skill_conflict,
    d05_yes,
    d06_no,
    d07_ambiguous,
    d08_non_traditional_yes,
)

ALL_CANDIDATES_B2: list[dict] = [
    {
        "module": d01_strong_yes,
        "candidate_input": d01_strong_yes.CANDIDATE_INPUT,
        "ground_truth_verdict": d01_strong_yes.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": d01_strong_yes.GROUND_TRUTH_RATIONALE,
        "cv_text": d01_strong_yes.CV_TEXT,
        "job_description": d01_strong_yes.JOB_DESCRIPTION,
    },
    {
        "module": d02_strong_no,
        "candidate_input": d02_strong_no.CANDIDATE_INPUT,
        "ground_truth_verdict": d02_strong_no.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": d02_strong_no.GROUND_TRUTH_RATIONALE,
        "cv_text": d02_strong_no.CV_TEXT,
        "job_description": d02_strong_no.JOB_DESCRIPTION,
    },
    {
        "module": d03_date_contradiction,
        "candidate_input": d03_date_contradiction.CANDIDATE_INPUT,
        "ground_truth_verdict": d03_date_contradiction.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": d03_date_contradiction.GROUND_TRUTH_RATIONALE,
        "cv_text": d03_date_contradiction.CV_TEXT,
        "job_description": d03_date_contradiction.JOB_DESCRIPTION,
    },
    {
        "module": d04_skill_conflict,
        "candidate_input": d04_skill_conflict.CANDIDATE_INPUT,
        "ground_truth_verdict": d04_skill_conflict.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": d04_skill_conflict.GROUND_TRUTH_RATIONALE,
        "cv_text": d04_skill_conflict.CV_TEXT,
        "job_description": d04_skill_conflict.JOB_DESCRIPTION,
    },
    {
        "module": d05_yes,
        "candidate_input": d05_yes.CANDIDATE_INPUT,
        "ground_truth_verdict": d05_yes.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": d05_yes.GROUND_TRUTH_RATIONALE,
        "cv_text": d05_yes.CV_TEXT,
        "job_description": d05_yes.JOB_DESCRIPTION,
    },
    {
        "module": d06_no,
        "candidate_input": d06_no.CANDIDATE_INPUT,
        "ground_truth_verdict": d06_no.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": d06_no.GROUND_TRUTH_RATIONALE,
        "cv_text": d06_no.CV_TEXT,
        "job_description": d06_no.JOB_DESCRIPTION,
    },
    {
        "module": d07_ambiguous,
        "candidate_input": d07_ambiguous.CANDIDATE_INPUT,
        "ground_truth_verdict": d07_ambiguous.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": d07_ambiguous.GROUND_TRUTH_RATIONALE,
        "cv_text": d07_ambiguous.CV_TEXT,
        "job_description": d07_ambiguous.JOB_DESCRIPTION,
    },
    {
        "module": d08_non_traditional_yes,
        "candidate_input": d08_non_traditional_yes.CANDIDATE_INPUT,
        "ground_truth_verdict": d08_non_traditional_yes.GROUND_TRUTH_VERDICT,
        "ground_truth_rationale": d08_non_traditional_yes.GROUND_TRUTH_RATIONALE,
        "cv_text": d08_non_traditional_yes.CV_TEXT,
        "job_description": d08_non_traditional_yes.JOB_DESCRIPTION,
    },
]

__all__ = ["ALL_CANDIDATES_B2"]
