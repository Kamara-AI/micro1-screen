"""SCREEN Pydantic schemas — the contracts for all pipeline data."""

from screen.schemas.analysis import CareerShape, FitAnalysis, LearningVelocityEvidence
from screen.schemas.candidate import CandidateProfile, EducationEntry, EmploymentGap, RoleEntry
from screen.schemas.cohort import CandidateRank, CohortAnalysis
from screen.schemas.decision import CandidateFeedback, Decision, HumanBrief, Verdict
from screen.schemas.evidence import (
    Claim,
    Contradiction,
    EvidenceBundle,
    SIGNAL_WEIGHTS,
    SignalTier,
    SilenceFlag,
)
from screen.schemas.input import ScreeningInput
from screen.schemas.state import ScreeningState, initial_state
from screen.schemas.trajectory import HumanOverride, TrajectoryEntry

__all__ = [
    # Input
    "ScreeningInput",
    # Candidate
    "CandidateProfile",
    "RoleEntry",
    "EducationEntry",
    "EmploymentGap",
    # Evidence
    "EvidenceBundle",
    "Claim",
    "Contradiction",
    "SilenceFlag",
    "SignalTier",
    "SIGNAL_WEIGHTS",
    # Analysis
    "FitAnalysis",
    "CareerShape",
    "LearningVelocityEvidence",
    # Decision
    "Decision",
    "Verdict",
    "HumanBrief",
    "CandidateFeedback",
    # Cohort
    "CohortAnalysis",
    "CandidateRank",
    # Trajectory
    "TrajectoryEntry",
    "HumanOverride",
    # State
    "ScreeningState",
    "initial_state",
]
