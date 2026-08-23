"""İki metni normalize edilmiş görünüm ve risk sinyalleriyle karşılaştırır."""

from __future__ import annotations

import difflib
import unicodedata

from ctf_payload_studio.analyzer import analyze_text
from ctf_payload_studio.models import ComparisonReport, Context, Difference
from ctf_payload_studio.validation import MAX_DIFF_SEGMENTS, validate_text


def normalize_for_compare(text: str) -> str:
    text = validate_text(text)
    normalized = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    return validate_text(normalized, label="normalize edilmiş metin")


def compare_texts(left: str, right: str, context: Context = Context.GENERIC) -> ComparisonReport:
    left = validate_text(left, label="sol metin")
    right = validate_text(right, label="sağ metin")
    normalized_left = normalize_for_compare(left)
    normalized_right = normalize_for_compare(right)
    if normalized_left == normalized_right:
        opcodes: tuple[tuple[str, int, int, int, int], ...] = ()
        similarity = 1.0
    else:
        matcher = difflib.SequenceMatcher(None, normalized_left, normalized_right, autojunk=True)
        opcodes = tuple(matcher.get_opcodes())
        similarity = round(matcher.ratio(), 4)
    differences: list[Difference] = []
    for operation, left_start, left_end, right_start, right_end in opcodes:
        if operation == "equal":
            continue
        differences.append(
            Difference(
                operation=operation,
                left=normalized_left[left_start:left_end][:256],
                right=normalized_right[right_start:right_end][:256],
            )
        )
        if len(differences) >= MAX_DIFF_SEGMENTS:
            break
    left_report = analyze_text(left, context)
    right_report = analyze_text(right, context)
    return ComparisonReport(
        identical=left == right,
        normalized_identical=normalized_left == normalized_right,
        similarity=similarity,
        left=left_report,
        right=right_report,
        risk_delta=right_report.risk_score - left_report.risk_score,
        differences=tuple(differences),
    )
