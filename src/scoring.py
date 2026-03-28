"""
Answer scoring for SCF benchmark evaluations.
Handles numeric, string, boolean, and date comparisons with appropriate tolerances.
"""

import re
from typing import Any


def normalize_number(s: str) -> float | None:
    """Try to parse a string as a number."""
    s = s.strip().replace(",", "").replace("$", "").replace("%", "").replace(" ", "")
    # Handle scientific notation
    s = s.replace("×10^", "e").replace("x10^", "e")
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def normalize_string(s: str) -> str:
    """Normalize a string for comparison."""
    s = s.strip().lower()
    # Remove common prefixes/suffixes
    s = re.sub(r"^(approximately|about|roughly|around|~)\s*", "", s)
    s = re.sub(r"\s*(approximately|approx\.?)$", "", s)
    return s


def score_answer(predicted: str, ground_truth: str, tolerance: float = 0.05) -> dict:
    """Score a predicted answer against ground truth.

    Returns dict with:
        - correct: bool (is the answer correct)
        - score: float (0.0 to 1.0)
        - method: str (how it was scored)
        - details: str (explanation)
    """
    pred = predicted.strip()
    gt = ground_truth.strip()

    # Normalize unicode dashes (en-dash, em-dash, minus sign) to ASCII hyphen
    for ch in ('\u2013', '\u2014', '\u2212'):  # –, —, −
        pred = pred.replace(ch, '-')
        gt = gt.replace(ch, '-')

    if not pred:
        return {"correct": False, "score": 0.0, "method": "empty", "details": "Empty prediction"}

    # Try numeric comparison first
    pred_num = normalize_number(pred)
    gt_num = normalize_number(gt)

    if gt_num is not None and pred_num is not None:
        if gt_num == 0:
            # For zero ground truth, check if prediction is also zero or very close
            if abs(pred_num) < 0.01:
                return {"correct": True, "score": 1.0, "method": "numeric_exact_zero",
                        "details": f"Both near zero: pred={pred_num}, gt={gt_num}"}
            return {"correct": False, "score": 0.0, "method": "numeric_zero_mismatch",
                    "details": f"GT is 0, pred={pred_num}"}

        rel_error = abs(pred_num - gt_num) / abs(gt_num)

        if rel_error < 0.001:  # Within 0.1%
            return {"correct": True, "score": 1.0, "method": "numeric_exact",
                    "details": f"Exact match: rel_error={rel_error:.6f}"}
        elif rel_error < tolerance:
            return {"correct": True, "score": 0.8, "method": "numeric_close",
                    "details": f"Close match: rel_error={rel_error:.4f} < {tolerance}"}
        else:
            # Check if they got the right order of magnitude
            if pred_num > 0 and gt_num > 0:
                import math
                mag_diff = abs(math.log10(pred_num) - math.log10(gt_num))
                if mag_diff < 0.1:
                    return {"correct": False, "score": 0.3, "method": "numeric_magnitude",
                            "details": f"Right magnitude but off: rel_error={rel_error:.4f}"}
            return {"correct": False, "score": 0.0, "method": "numeric_wrong",
                    "details": f"Wrong: pred={pred_num}, gt={gt_num}, rel_error={rel_error:.4f}"}

    # String comparison
    pred_norm = normalize_string(pred)
    gt_norm = normalize_string(gt)

    if pred_norm == gt_norm:
        return {"correct": True, "score": 1.0, "method": "string_exact",
                "details": "Exact string match"}

    # Check containment
    if gt_norm in pred_norm or pred_norm in gt_norm:
        return {"correct": True, "score": 0.8, "method": "string_contains",
                "details": f"Containment match"}

    # For Yes/No questions
    yes_words = {"yes", "true", "correct", "affirmative"}
    no_words = {"no", "false", "incorrect", "negative"}
    if gt_norm in yes_words and pred_norm in yes_words:
        return {"correct": True, "score": 1.0, "method": "boolean_match", "details": "Both yes"}
    if gt_norm in no_words and pred_norm in no_words:
        return {"correct": True, "score": 1.0, "method": "boolean_match", "details": "Both no"}

    return {"correct": False, "score": 0.0, "method": "no_match",
            "details": f"No match: pred='{pred[:50]}', gt='{gt[:50]}'"}


def extract_answer_from_response(response: str) -> str:
    """Extract the concise answer from an LLM response.

    Looks for patterns like "Answer: X" or "The answer is X" or just the last number/value.
    """
    response = response.strip()

    # Look for explicit answer markers
    patterns = [
        r"(?:^|\n)\s*(?:Answer|ANSWER|A):\s*(.+?)(?:\n|$)",
        r"(?:the answer is|the result is|the value is|the total is)\s+(.+?)(?:\.|$)",
        r"(?:^|\n)\s*\*\*(.+?)\*\*\s*(?:\n|$)",
    ]
    for pat in patterns:
        m = re.search(pat, response, re.IGNORECASE)
        if m:
            answer = m.group(1).strip()
            # Clean up markdown/formatting
            answer = answer.strip("*`'\"")
            return answer

    # If response is short (one line), use it directly
    lines = [l.strip() for l in response.split("\n") if l.strip()]
    if len(lines) == 1:
        return lines[0].strip("*`'\"")

    # Look for the last line that contains a number or short answer
    for line in reversed(lines):
        line = line.strip("*`'\"- ")
        if line and len(line) < 100:
            # Check if it looks like a final answer
            num = normalize_number(line)
            if num is not None:
                return line
            if len(line) < 50 and not line.endswith(":"):
                return line

    # Fall back to first line
    return lines[0] if lines else response
