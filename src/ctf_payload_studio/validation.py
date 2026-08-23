"""Kaynak tüketimini sınırlayan ortak doğrulamalar."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from ctf_payload_studio.errors import ValidationError

MAX_INPUT_BYTES = 65_536
MAX_PIPELINE_STEPS = 12
MAX_DIFF_SEGMENTS = 128


def validate_text(value: str, *, label: str = "metin") -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{label} bir metin olmalıdır")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise ValidationError(f"{label} geçerli Unicode skaler değerleri içermelidir") from exc
    if size > MAX_INPUT_BYTES:
        raise ValidationError(f"{label} en fazla {MAX_INPUT_BYTES} UTF-8 baytı olabilir")
    return value


def read_text_file(path: Path) -> str:
    """Symlink/FIFO izlemeden, sınırlı boyutta tek bir UTF-8 dosyası okur."""
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_NONBLOCK"):
        raise ValidationError("bu platform güvenli dosya girdisi bayraklarını desteklemiyor")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValidationError(f"girdi dosyası güvenle açılamadı: {path}") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValidationError("girdi yalnızca normal bir dosya olabilir")
        if info.st_size > MAX_INPUT_BYTES:
            raise ValidationError(f"girdi dosyası en fazla {MAX_INPUT_BYTES} bayt olabilir")
        payload = bytearray()
        while len(payload) <= MAX_INPUT_BYTES:
            chunk = os.read(descriptor, min(8192, MAX_INPUT_BYTES + 1 - len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
        if len(payload) > MAX_INPUT_BYTES:
            raise ValidationError(f"girdi dosyası en fazla {MAX_INPUT_BYTES} bayt olabilir")
        try:
            return bytes(payload).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("girdi dosyası geçerli UTF-8 olmalıdır") from exc
    finally:
        os.close(descriptor)
