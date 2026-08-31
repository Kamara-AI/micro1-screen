"""
WHY: A typed exception hierarchy makes error handling explicit and testable.
Every failure mode in SCREEN has a specific exception type so callers can
respond differently to LLM timeouts vs. schema validation failures vs.
hard requirement rejections.

This mirrors byYou's AppException hierarchy — each exception carries enough
context to log meaningfully without exposing candidate data.

HOW: All exceptions inherit from ScreenException. Callers catch the specific
type they want to handle; everything else bubbles up to the global handler.
"""


class ScreenException(Exception):
    """
    WHY: Base class for all SCREEN exceptions. Carries a message and an optional
    error_code so structured logs can filter by type without string matching.
    """

    def __init__(self, message: str, error_code: str = "SCREEN_ERROR") -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.error_code}, message={self.message!r})"


class LLMCallError(ScreenException):
    """
    WHY: Raised when an LLM API call fails after all retries are exhausted.
    Separates transient network errors from logic errors.

    Carries the node name so trajectory logging knows which step failed.
    """

    def __init__(self, node: str, cause: str) -> None:
        self.node = node
        super().__init__(
            message=f"LLM call failed in node '{node}' after max retries: {cause}",
            error_code="LLM_CALL_FAILED",
        )


class SchemaValidationError(ScreenException):
    """
    WHY: Raised when LLM output cannot be parsed into the expected Pydantic schema.
    Indicates the model returned malformed JSON or an unexpected structure.
    The raw_output field is included for debugging (never logged to external systems).
    """

    def __init__(self, schema_name: str, raw_output: str) -> None:
        self.schema_name = schema_name
        self.raw_output = raw_output  # Kept in memory only — never logged externally
        super().__init__(
            message=f"LLM output failed validation for schema '{schema_name}'",
            error_code="SCHEMA_VALIDATION_FAILED",
        )


class HardRejectError(ScreenException):
    """
    WHY: Raised (and caught) during Tier 1 pre-filter when a candidate fails
    a hard requirement. This is not a bug — it's an expected control flow
    signal that routes the graph to END with a STRONG_NO verdict.

    Using an exception rather than a flag keeps the node return type clean.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            message=f"Hard requirement not met: {reason}",
            error_code="HARD_REJECT",
        )


class StateTransitionError(ScreenException):
    """
    WHY: Raised when the LangGraph state contains an unexpected combination —
    e.g., a node is asked to run before its prerequisite node has written output.
    Surfaces structural bugs in graph wiring rather than hiding them.
    """

    def __init__(self, node: str, missing_field: str) -> None:
        super().__init__(
            message=f"Node '{node}' requires '{missing_field}' in state, but it is None",
            error_code="STATE_TRANSITION_ERROR",
        )


class EvaluationError(ScreenException):
    """
    WHY: Raised by the evaluation runner when a test case produces an unexpected
    error (distinct from a wrong verdict, which is a metric, not an exception).
    """

    def __init__(self, candidate_id: str, cause: str) -> None:
        super().__init__(
            message=f"Evaluation failed for candidate '{candidate_id}': {cause}",
            error_code="EVALUATION_ERROR",
        )
