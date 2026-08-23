from __future__ import annotations

import json
from pathlib import Path

import pytest

from ctf_payload_studio.cli import main


def test_analyze_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["analyze", "{{ value }}", "--context", "template", "--format", "json"]) == 0
    output = capsys.readouterr().out
    assert json.loads(output)["risk_score"] > 0


def test_transform_and_compare(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["transform", "abc", "--step", "hex-encode", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["output"] == "616263"
    assert main(["compare", "a", "b", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["identical"] is False


def test_file_input_and_conflict(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "input.txt"
    path.write_text("yerel", encoding="utf-8")
    assert main(["fingerprint", "--input-file", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["characters"] == 5
    assert main(["analyze", "x", "--input-file", str(path)]) == 2
    assert "birlikte kullanılamaz" in capsys.readouterr().err


def test_catalog_self_test_and_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["catalog"]) == 0
    assert "auto-decode" in capsys.readouterr().out
    assert main(["self-test"]) == 0
    assert "başarılı" in capsys.readouterr().out


def test_error_control_characters_are_escaped(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["transform", r"\q\x1b", "--step", "unicode-unescape"]) == 2
    error = capsys.readouterr().err
    assert "\x1b" not in error
