#!/usr/bin/env python3
"""
WHY: After a genuine calibration round (where accuracy improvements are intentional,
not regressions being hidden), this script promotes the latest eval_summary_*.json
into the BASELINE_ACCURACY dict in run_evals.py. This keeps the baseline current
without requiring manual edits to the source file.

HOW: Reads the latest eval_summary_*.json from evaluation/results/, checks that
overall_status == "pass" (no regressions), then rewrites the BASELINE_ACCURACY
dict literal in run_evals.py using a regex replacement.

Safety: Will not update the baseline if the latest summary shows a regression.
This prevents accidentally baking a bad run into the baseline.

Usage:
    python scripts/update_baseline.py
    python scripts/update_baseline.py --results-dir /custom/path
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────

SCRIPTS_DIR = Path(__file__).parent
REPO_ROOT = SCRIPTS_DIR.parent
RESULTS_DIR = REPO_ROOT / "evaluation" / "results"
RUN_EVALS_PATH = SCRIPTS_DIR / "run_evals.py"


# ── Helpers ────────────────────────────────────────────────────────────────────

def find_latest_summary(results_dir: Path) -> Path:
    """
    WHY: The latest eval_summary_*.json reflects the most recent calibration run.
    We sort by mtime (not filename) to be robust to clock skew or manual file copies.

    Args:
        results_dir: Directory containing eval_summary_*.json files.

    Returns:
        Path to the latest summary JSON file.

    Raises:
        FileNotFoundError: If no summary files exist in the directory.
    """
    summaries = sorted(
        results_dir.glob("eval_summary_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not summaries:
        raise FileNotFoundError(
            f"No eval_summary_*.json files found in {results_dir}. "
            "Run `python scripts/run_evals.py` first."
        )
    return summaries[0]


def load_summary(path: Path) -> dict:
    """
    WHY: Deserialise the eval summary JSON. Validation is minimal — we trust the
    output of run_evals.py, which controls the schema.

    Args:
        path: Path to the eval_summary_*.json file.

    Returns:
        Parsed summary dict.

    Raises:
        ValueError: If the JSON is missing required keys.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    required = {"overall_status", "batches"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Summary JSON is missing required keys: {missing}")

    return data


def build_baseline_dict_literal(batches: dict) -> str:
    """
    WHY: We write the new baseline as a Python dict literal that replaces the
    existing BASELINE_ACCURACY dict in run_evals.py. Preserving the inline comments
    (batch domain annotations) makes the code self-documenting for future readers.

    HOW: The domain comments come from BATCH_DOMAINS in run_evals.py. We hardcode
    them here since they don't change between runs — they describe the batch, not
    the results.

    Args:
        batches: Dict from the eval summary, keyed by batch key (e.g. "batch1"),
            each with an "accuracy" field (float or None).

    Returns:
        A Python source string for the BASELINE_ACCURACY dict body (without the
        variable name or surrounding braces — those are handled by the regex).
    """
    domain_comments = {
        "batch1": "Senior SWE — 10 candidates",
        "batch2": "Senior Data Scientist — 8 candidates",
        "batch3": "FMCG Ops Manager — 20 candidates",
        "batch4": "Digital Marketing — 33 candidates (first uncalibrated run)",
    }

    lines = []
    for key in ["batch1", "batch2", "batch3", "batch4"]:
        if key not in batches:
            continue
        accuracy = batches[key].get("accuracy")
        if accuracy is None:
            # Skip batches that errored — preserve existing baseline value
            continue
        comment = domain_comments.get(key, "")
        lines.append(f'    "{key}": {accuracy:.1f},   # {comment}')

    return "\n".join(lines)


def update_baseline_in_source(new_baseline_lines: str) -> None:
    """
    WHY: Directly editing the Python source file ensures the baseline is always
    co-located with the regression logic — no external config file that can get
    out of sync. The regex targets the BASELINE_ACCURACY dict literal precisely.

    HOW: Uses a regex that matches the entire dict body between the outer braces.
    This is safe because the dict has a predictable structure (four string keys,
    float values, inline comments — all on separate lines).

    Args:
        new_baseline_lines: The new dict body as a Python source string, with
            leading spaces and trailing comma on each entry.

    Raises:
        ValueError: If the BASELINE_ACCURACY dict is not found in the source.
        RuntimeError: If the replacement produces no change (likely a regex issue).
    """
    source = RUN_EVALS_PATH.read_text(encoding="utf-8")

    # WHY: Match the dict body between BASELINE_ACCURACY = { ... }.
    # [^}]* stops at the first closing brace, which is what we want since
    # BASELINE_ACCURACY contains only scalar values (no nested dicts).
    # re.DOTALL is required because dict entries span multiple lines.
    pattern = re.compile(
        r"(BASELINE_ACCURACY:\s*dict\[str,\s*float\]\s*=\s*\{)[^}]*(})",
        re.DOTALL,
    )

    match = pattern.search(source)
    if not match:
        raise ValueError(
            "Could not find BASELINE_ACCURACY dict in run_evals.py. "
            "Has the variable name or type annotation changed?"
        )

    new_source = pattern.sub(
        rf"\1\n{new_baseline_lines}\n\2",
        source,
    )

    if new_source == source:
        raise RuntimeError(
            "Replacement produced no change. The new baseline values may be "
            "identical to the existing ones, or the regex did not match correctly."
        )

    RUN_EVALS_PATH.write_text(new_source, encoding="utf-8")


# ── Argument parsing ───────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """
    WHY: Allow the results directory to be overridden so this script can be used
    in non-standard repo layouts or CI artefact directories.

    Returns:
        Parsed argparse.Namespace.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Promote the latest eval summary to BASELINE_ACCURACY in run_evals.py. "
            "Only runs if overall_status == 'pass' (no regressions)."
        )
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=RESULTS_DIR,
        metavar="PATH",
        help=f"Directory containing eval_summary_*.json files (default: {RESULTS_DIR})",
    )
    return parser.parse_args()


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    """
    WHY: Gated behind overall_status == "pass" to prevent accidentally anchoring
    the baseline to a bad run. If regressions exist, the engineer must fix them
    before the baseline can be promoted.

    Returns:
        Exit code: 0 on success or clean skip, 1 on error.
    """
    args = parse_args()

    try:
        summary_path = find_latest_summary(args.results_dir)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Reading latest summary: {summary_path}")

    try:
        summary = load_summary(summary_path)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: Could not load summary — {exc}", file=sys.stderr)
        return 1

    overall_status = summary["overall_status"]
    if overall_status != "pass":
        regressions = summary.get("regressions", [])
        print(
            f"BLOCKED: overall_status is '{overall_status}' "
            f"(regressions: {regressions}). "
            "Fix regressions before updating the baseline."
        )
        return 1

    batches = summary["batches"]

    # Print what will be updated
    print("\nBaseline updates to apply:")
    for batch_key in ["batch1", "batch2", "batch3", "batch4"]:
        if batch_key not in batches:
            continue
        accuracy = batches[batch_key].get("accuracy")
        old_baseline = batches[batch_key].get("baseline", "unknown")
        if accuracy is None:
            print(f"  {batch_key}: SKIPPED (runner error — keeping existing baseline)")
        else:
            print(f"  {batch_key}: {old_baseline:.1f}% → {accuracy:.1f}%")

    new_lines = build_baseline_dict_literal(batches)

    try:
        update_baseline_in_source(new_lines)
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"\nBaseline updated in: {RUN_EVALS_PATH}")
    print("Run `python scripts/run_evals.py` to confirm the new baseline is clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
