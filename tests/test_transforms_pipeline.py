from __future__ import annotations

import pytest

from ctf_payload_studio.errors import TransformError, ValidationError
from ctf_payload_studio.models import TransformName
from ctf_payload_studio.pipeline import run_pipeline
from ctf_payload_studio.transforms import apply_transform, auto_decode


@pytest.mark.parametrize(
    ("encode", "decode"),
    [
        (TransformName.URL_ENCODE, TransformName.URL_DECODE),
        (TransformName.BASE64_ENCODE, TransformName.BASE64_DECODE),
        (TransformName.HEX_ENCODE, TransformName.HEX_DECODE),
        (TransformName.HTML_ENCODE, TransformName.HTML_DECODE),
        (TransformName.UNICODE_ESCAPE, TransformName.UNICODE_UNESCAPE),
    ],
)
def test_reversible_transform_pairs(encode: TransformName, decode: TransformName) -> None:
    source = "Merhaba <Dünya>"
    assert apply_transform(apply_transform(source, encode), decode) == source


def test_pipeline_records_hashes_sizes_and_round_trip() -> None:
    result = run_pipeline("Merhaba", [TransformName.URL_ENCODE, TransformName.BASE64_ENCODE])
    assert len(result.steps) == 2
    assert all(step.round_trip_ok for step in result.steps)
    assert all(len(step.input_sha256) == 64 for step in result.steps)
    assert "flowchart LR" in result.graph
    assert "Merhaba" not in result.graph


def test_pipeline_requires_bounded_steps() -> None:
    with pytest.raises(ValidationError):
        run_pipeline("x", [])
    with pytest.raises(ValidationError):
        run_pipeline("x", [TransformName.NORMALIZE] * 13)


@pytest.mark.parametrize(
    ("value", "name"),
    [
        ("%Q1", TransformName.URL_DECODE),
        ("not base64!", TransformName.BASE64_DECODE),
        ("ZE==", TransformName.BASE64_DECODE),
        ("123", TransformName.HEX_DECODE),
        (r"\q", TransformName.UNICODE_UNESCAPE),
        (r"\ud800", TransformName.UNICODE_UNESCAPE),
    ],
)
def test_malformed_encodings_are_rejected(value: str, name: TransformName) -> None:
    with pytest.raises(TransformError):
        apply_transform(value, name)


def test_auto_decode_is_bounded_and_detects_layers() -> None:
    layered = apply_transform(
        apply_transform("Merhaba Dünya", TransformName.URL_ENCODE), TransformName.BASE64_ENCODE
    )
    result = auto_decode(layered, max_depth=4)
    assert result.output == "Merhaba Dünya"
    assert result.detected_steps == (TransformName.BASE64_DECODE, TransformName.URL_DECODE)
    with pytest.raises(ValidationError):
        auto_decode(layered, max_depth=9)


def test_auto_decode_hex() -> None:
    result = auto_decode("6869")
    assert result.output == "hi"
    assert result.detected_steps == (TransformName.HEX_DECODE,)


def test_normalization_is_explicitly_not_reversible() -> None:
    result = run_pipeline("\uff21", [TransformName.NORMALIZE])
    assert result.output == "A"
    assert result.steps[0].round_trip_ok is None
