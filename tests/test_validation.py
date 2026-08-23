from __future__ import annotations

import os
from pathlib import Path

import pytest

from ctf_payload_studio.errors import ValidationError
from ctf_payload_studio.validation import MAX_INPUT_BYTES, read_text_file, validate_text


def test_text_size_limit_uses_utf8_bytes() -> None:
    assert validate_text("a" * MAX_INPUT_BYTES)
    with pytest.raises(ValidationError):
        validate_text("ş" * (MAX_INPUT_BYTES // 2 + 1))


def test_lone_surrogate_is_rejected_as_invalid_unicode() -> None:
    with pytest.raises(ValidationError, match="Unicode"):
        validate_text("\ud800")


def test_regular_utf8_file_is_read(tmp_path: Path) -> None:
    path = tmp_path / "input.txt"
    path.write_text("Merhaba", encoding="utf-8")
    assert read_text_file(path) == "Merhaba"


def test_symlink_and_fifo_are_rejected_without_blocking(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("x", encoding="utf-8")
    symlink = tmp_path / "link.txt"
    symlink.symlink_to(target)
    with pytest.raises(ValidationError):
        read_text_file(symlink)
    if hasattr(os, "mkfifo"):
        fifo = tmp_path / "pipe"
        os.mkfifo(fifo)
        with pytest.raises(ValidationError):
            read_text_file(fifo)


def test_binary_and_oversized_files_are_rejected(tmp_path: Path) -> None:
    binary = tmp_path / "binary"
    binary.write_bytes(b"\xff")
    with pytest.raises(ValidationError):
        read_text_file(binary)
    oversized = tmp_path / "large"
    oversized.write_bytes(b"x" * (MAX_INPUT_BYTES + 1))
    with pytest.raises(ValidationError):
        read_text_file(oversized)
