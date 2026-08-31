"""
WHY: Top-level evaluation package. Provides a single import surface for the
runner and any external test harness. Keeps the runner clean — it imports
from evaluation, not from evaluation.candidates.c01_strong_yes etc.

HOW: Re-exports ALL_CANDIDATES from the candidates subpackage. Any new
subpackage (e.g. evaluation.results, evaluation.fixtures) should be added here.
"""

from evaluation.candidates import ALL_CANDIDATES

__all__ = ["ALL_CANDIDATES"]
