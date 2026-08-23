from __future__ import annotations

import pytest

from ctf_payload_studio.compare import compare_texts
from ctf_payload_studio.errors import ValidationError
from ctf_payload_studio.fingerprint import fingerprint_text
from ctf_payload_studio.models import Context
from ctf_payload_studio.validation import MAX_INPUT_BYTES


def test_fingerprint_is_deterministic() -> None:
    first = fingerprint_text("örnek")
    second = fingerprint_text("örnek")
    assert first == second
    assert len(first.sha256) == 64
    assert first.bytes > first.characters
    assert 0 <= first.entropy <= 8


def test_empty_fingerprint_has_defined_statistics() -> None:
    result = fingerprint_text("")
    assert result.entropy == 0
    assert result.printable_ratio == 1


def test_unicode_equivalent_texts_compare_equal_after_normalization() -> None:
    report = compare_texts("café", "cafe\u0301")
    assert not report.identical
    assert report.normalized_identical
    assert report.similarity == 1


def test_comparison_explains_risk_delta() -> None:
    report = compare_texts("değer", "{{ değer }}", Context.TEMPLATE)
    assert report.risk_delta > 0
    assert report.right.risk_score > report.left.risk_score
    assert report.differences


def test_diff_segments_are_bounded() -> None:
    left = "".join("a" if index % 2 else "b" for index in range(600))
    right = "".join("x" if index % 2 else "y" for index in range(600))
    report = compare_texts(left, right)
    assert len(report.differences) <= 128


def test_repetitive_max_size_comparison_is_bounded() -> None:
    left = "ab" * (MAX_INPUT_BYTES // 2)
    right = "ba" * (MAX_INPUT_BYTES // 2)
    report = compare_texts(left, right)
    assert not report.identical
    assert len(report.differences) <= 128


def test_normalized_comparison_output_must_remain_bounded() -> None:
    source = "\ufdfa" * (MAX_INPUT_BYTES // len("\ufdfa".encode("utf-8")))
    with pytest.raises(ValidationError, match="normalize edilmiş metin"):
        compare_texts(source, source)
